"""Revision-aware local content index. Rebuilt indexes contain no user state."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import threading
from jp_inflection import normalize, romanize
from lexicon_exercise import plain, reading_of, source_ref


class LexiconIndex:
    def __init__(self,store):
        self.store=store; self.lock=threading.RLock(); self.signature=None; self.revision=''
        self.db=sqlite3.connect(':memory:',check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        self.db.execute('CREATE TABLE entries(ref TEXT PRIMARY KEY,head TEXT,reading TEXT,roman TEXT,gloss TEXT,examples TEXT,connection TEXT,kind TEXT,level TEXT,pack TEXT,unit TEXT,data TEXT)')
        self.db.execute('CREATE INDEX heads ON entries(head)')
        self.db.execute('CREATE INDEX readings ON entries(reading)')

    def refresh(self):
        paths=sorted(self.store.root.glob('*/pack.json'))
        signature=tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in paths)
        if signature==self.signature:return
        rows=[]
        for path in paths:
            try: pack=self.store.get_pack(path.parent.name)
            except (ValueError,OSError): continue
            if not pack or pack['quality']['blocked']: continue
            for entry in pack.get('entries',[]):
                reading=reading_of(entry); ref=source_ref(pack,entry)
                result={'id':entry['id'],'sourceRef':ref,'packSlug':path.parent.name,'packTitle':pack['title'],'kind':entry['kind'],'level':entry.get('level',''),'headword':entry['headword'],'reading':reading,'gloss':entry.get('gloss',{}),'unitId':entry.get('unitId','')}
                fields=[plain(entry['headword']),reading,romanize(reading),' '.join(entry.get('gloss',{}).values()),' '.join(' '.join(str(v) for k,v in e.items() if k in {'ja','zh','en'}) for e in entry.get('examples',[])),json.dumps(entry.get('grammar',{}),ensure_ascii=False)]
                rows.append((ref,*[normalize(f,reading=True) for f in fields],entry['kind'],entry.get('level',''),path.parent.name,entry.get('unitId',''),json.dumps(result,ensure_ascii=False)))
        with self.db:
            self.db.execute('DELETE FROM entries'); self.db.executemany('INSERT INTO entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',rows)
        self.signature=signature
        # A generation stamp a cursor can be checked against. mtime/size alone decide when
        # to rebuild; the revision covers what was actually indexed (§9.1).
        self.revision=hashlib.sha256(
            json.dumps([signature,len(rows)],ensure_ascii=False,default=str).encode()).hexdigest()[:16]

    def search(self,query,*,kind='',level='',pack='',unit='',field='',limit=100,offset=0,refs=None):
        needle=normalize(query,reading=True)
        if not needle:return {'results':[],'total':0}
        if len(needle)>200: raise ValueError('查询内容最多 200 字。')
        fields=['head','reading','roman','gloss','examples','connection']
        if field and field not in fields: raise ValueError('查询字段无效。')
        selected=[field] if field else fields
        escaped=needle.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        clauses=['('+' OR '.join(f"{f} LIKE ? ESCAPE '\\'" for f in selected)+')']; params=['%'+escaped+'%']*len(selected)
        for name,value in [('kind',kind),('level',level),('pack',pack),('unit',unit)]:
            if value: clauses.append(f'{name}=?'); params.append(value)
        if refs is not None:
            # Restricting before the count keeps `total` and the pages describing the
            # same set; filtering afterwards could only ever see one page (§9.1).
            if not refs: clauses.append('0')
            else: clauses.append('ref IN ('+','.join('?' for _ in refs)+')'); params.extend(sorted(refs))
        where=' AND '.join(clauses)
        with self.lock:
            self.refresh()
            total=self.db.execute('SELECT COUNT(*) FROM entries WHERE '+where,params).fetchone()[0]
            rows=self.db.execute('SELECT *,CASE WHEN head=? THEN 0 WHEN reading=? THEN 5 WHEN head LIKE ? ESCAPE \'\\\' THEN 20 ELSE 45 END rank FROM entries WHERE '+where+' ORDER BY rank,ref LIMIT ? OFFSET ?',[needle,needle,escaped+'%',*params,limit,offset]).fetchall()
        labels={'head':'表记/文型','reading':'读音','roman':'罗马字','gloss':'释义','examples':'例句','connection':'接续/说明'}
        # `(rank, ref)` must be exactly the merge key the pager sorts every source by;
        # adding `pack` between them would make the sources disagree (§9.1).
        results=[]
        for row in rows:
            item=json.loads(row['data']); item['score']=row['rank']; item['matchField']=', '.join(labels[f] for f in selected if needle in row[f]); results.append(item)
        return {'results':results,'total':total}
