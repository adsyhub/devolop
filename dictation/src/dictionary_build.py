"""Build/update JMdict without touching personal learning data.

python src/dictionary_build.py --download
python src/dictionary_build.py --input JMdict_e.gz --out assets/dictionary/jmdict.sqlite3
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
import urllib.request
import xml.etree.ElementTree as ET
from jp_inflection import normalize, romanize

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT/'assets/dictionary/jmdict.sqlite3'
SOURCE_URL = 'https://www.edrdg.org/pub/Nihongo/JMdict_e.gz'
LICENSE_URL = 'https://www.edrdg.org/edrdg/licence.html'
MAX_DOWNLOAD = 100*1024*1024


class Cancelled(Exception):
    """The learner asked for the install to stop; the current version is untouched."""


def report(message: str, **detail) -> None:
    """Default progress sink. Accepts the structured detail a job recorder wants."""
    print(message if not detail else f"{message}  [{', '.join(f'{k}={v}' for k, v in detail.items())}]")


def build(source: Path, output: Path, progress=report, cancelled=None) -> dict:
    """Build a dictionary and publish it as one unit.

    `cancelled` is an optional callable polled between batches. Publishing writes the
    database and its SOURCES sidecar into `versions/<revision>/` and then moves a single
    pointer, so the two can never disagree and a failed run leaves the previous version
    exactly as it was (§9.4).
    """
    should_stop = cancelled if callable(cancelled) else (lambda: False)
    output.parent.mkdir(parents=True,exist_ok=True)
    # Build and validate next to the target, then atomically replace it.
    with tempfile.TemporaryDirectory(prefix='.jmdict-',dir=output.parent) as td:
        clean=Path(td)/'source.xml'; db=Path(td)/'dictionary.sqlite3'
        digest=hashlib.sha256(); total=0
        with source.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''): digest.update(chunk)
        opener=gzip.open if source.read_bytes()[:2]==b'\x1f\x8b' else open
        with opener(source,'rb') as src, clean.open('wb') as dst:
            for line in src:
                total+=len(line)
                if total>512*1024*1024: raise ValueError('词典解压后超过大小限制。')
                # Keep POS entity names (v5k etc.) rather than expanded English labels.
                line=re.sub(rb'&([A-Za-z0-9_-]+);',lambda m:m[0] if m[1] in {b'amp',b'lt',b'gt',b'quot',b'apos'} else m[1],line)
                dst.write(line)
        conn=sqlite3.connect(db)
        try:
            conn.executescript('''
              CREATE TABLE entries(id TEXT PRIMARY KEY,data TEXT NOT NULL);
              CREATE TABLE forms(entry_id TEXT NOT NULL,text TEXT NOT NULL,normalized TEXT NOT NULL,roman TEXT NOT NULL);
              CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
              CREATE TABLE sense_keys(entry_id TEXT,sense_key TEXT,data TEXT,PRIMARY KEY(entry_id,sense_key));
            ''')
            try:
                conn.execute("CREATE VIRTUAL TABLE entry_fts USING fts5(entry_id UNINDEXED, gloss, tokenize='trigram')")
                fts='trigram'
            except sqlite3.OperationalError:
                try:
                    conn.execute('CREATE VIRTUAL TABLE entry_fts USING fts5(entry_id UNINDEXED,gloss)'); fts='unicode61'
                except sqlite3.OperationalError: fts='none'
            count=0
            context=ET.iterparse(clean,events=('start','end')); _,root=next(context)
            for event,entry in context:
                if event!='end' or entry.tag!='entry': continue
                key=entry.findtext('ent_seq','')
                if not key.isdigit(): raise ValueError('JMdict 词目 ID 无效。')
                written=[e.text for e in entry.findall('k_ele/keb') if e.text]
                readings=[{'text':r.findtext('reb',''),'restrictions':[e.text for e in r.findall('re_restr')],'noKanji':r.find('re_nokanji') is not None} for r in entry.findall('r_ele')]
                senses=[]; all_pos=set(); inherited=[]
                for sense in entry.findall('sense'):
                    pos=[e.text for e in sense.findall('pos')]; inherited=pos or inherited
                    gloss=[g.text for g in sense.findall('gloss') if g.get('{http://www.w3.org/XML/1998/namespace}lang','eng')=='eng' and g.text]
                    if not gloss: continue
                    record={'gloss':gloss,'pos':inherited,'writtenRestrictions':[e.text for e in sense.findall('stagk')],'readingRestrictions':[e.text for e in sense.findall('stagr')],'notes':[e.text for e in sense.findall('s_inf')]}
                    sense_key=hashlib.sha256(json.dumps(record,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:20]
                    record['key']=sense_key; senses.append(record); all_pos.update(inherited)
                    conn.execute('INSERT OR IGNORE INTO sense_keys VALUES (?,?,?)',(key,sense_key,json.dumps(record,ensure_ascii=False)))
                if not readings: continue
                headword=written[0] if written else readings[0]['text']
                glosses=[g for s in senses for g in s['gloss']]
                item={'id':key,'sourceRef':'dict:jmdict#'+key,'kind':'word','headword':headword,'reading':readings[0]['text'],'readings':readings,'writtenForms':written,'senses':senses,'pos':sorted(all_pos),'common':bool(entry.findall('.//ke_pri') or entry.findall('.//re_pri')),'gloss':{'en':'; '.join(glosses)},'source':'JMdict','license':'CC BY-SA 4.0','licenseUrl':LICENSE_URL}
                conn.execute('INSERT INTO entries VALUES (?,?)',(key,json.dumps(item,ensure_ascii=False)))
                for text in dict.fromkeys(written+[r['text'] for r in readings]):
                    conn.execute('INSERT INTO forms VALUES (?,?,?,?)',(key,text,normalize(text,reading=True),romanize(text)))
                if fts!='none': conn.execute('INSERT INTO entry_fts(entry_id,gloss) VALUES (?,?)',(key,' '.join(glosses)))
                count+=1; root.clear()
                if count%2000==0 and should_stop(): raise Cancelled('已按请求取消安装。')
                if count%20000==0: progress(f'已导入 {count} 个词目',entries=count)
            if not count: raise ValueError('没有读取到 JMdict 词目。')
            conn.executescript('CREATE INDEX forms_normalized ON forms(normalized); CREATE INDEX forms_roman ON forms(roman);')
            metadata={'source':'JMdict','sourceUrl':SOURCE_URL,'license':'CC BY-SA 4.0','licenseUrl':LICENSE_URL,'attribution':'JMdict © James William Breen and EDRDG','builtAt':datetime.now(timezone.utc).isoformat(),'sourceSha256':digest.hexdigest(),'entries':str(count),'fts':fts,'languages':'Japanese, English','schemaVersion':'1'}
            if fts=='none': progress('本次构建没有 FTS5：释义全文检索不可用，表记与读音查询正常。')
            conn.executemany('INSERT INTO metadata VALUES (?,?)',metadata.items()); conn.commit()
            if conn.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValueError('词典数据库完整性检查失败。')
        finally: conn.close()
        if should_stop(): raise Cancelled('已按请求取消安装。')
        publish(db, output, metadata)
        progress(f'词典安装完成：{count} 个词目',entries=count)
        return metadata


def publish(built: Path, output: Path, metadata: dict) -> Path:
    """Move a verified build into its own version directory and repoint `current.json`.

    Everything the version needs is complete inside the directory before the pointer
    moves, so a crash between the two leaves the previous version serving. The previous
    version directory is kept; older ones are pruned.
    """
    revision = str(metadata['sourceSha256'])[:32]
    root = output.parent
    versions = root/'versions'
    versions.mkdir(parents=True,exist_ok=True)
    target = versions/revision
    staging = versions/('.staging-'+revision)
    if staging.exists(): shutil.rmtree(staging)
    staging.mkdir()
    os.replace(built, staging/'dictionary.sqlite3')
    (staging/'SOURCES.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (staging/'SOURCES.md').write_text('# JMdict\n\n'+metadata['attribution']+'\n\n日语和英语数据。\n\n来源：'+SOURCE_URL+'\n\n许可与署名要求：'+LICENSE_URL+'\n\n使用 python src/dictionary_build.py --download 更新；每个版本保存在 versions/<revision>/ 下。\n',encoding='utf-8')
    if not (staging/'dictionary.sqlite3').is_file(): raise ValueError('词典文件未写入暂存目录。')
    if target.exists(): shutil.rmtree(target)
    os.replace(staging, target)

    previous = None
    pointer = root/'current.json'
    if pointer.is_file():
        try: previous = json.loads(pointer.read_text(encoding='utf-8')).get('revision')
        except ValueError: previous = None
    payload = {'revision':revision,'path':f'versions/{revision}/dictionary.sqlite3',
               'sources':f'versions/{revision}/SOURCES.json','previousRevision':previous,
               'publishedAt':datetime.now(timezone.utc).isoformat()}
    temporary = root/'.current.json.tmp'
    temporary.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(temporary, pointer)

    # Top-level copies stay readable for anything that still points at the fixed path.
    (root/'SOURCES.json').write_text((target/'SOURCES.json').read_text(encoding='utf-8'),encoding='utf-8')
    (root/'SOURCES.md').write_text((target/'SOURCES.md').read_text(encoding='utf-8'),encoding='utf-8')
    keep = {revision, previous}
    for directory in versions.iterdir():
        if directory.is_dir() and directory.name not in keep:
            shutil.rmtree(directory, ignore_errors=True)
    return target/'dictionary.sqlite3'


def download(output: Path=DEFAULT_PATH, progress=report, cancelled=None) -> dict:
    should_stop = cancelled if callable(cancelled) else (lambda: False)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.download-',dir=output.parent) as td:
        source=Path(td)/'JMdict_e.gz'; total=0
        request=urllib.request.Request(SOURCE_URL,headers={'User-Agent':'Dictation local dictionary installer'})
        progress('正在下载 JMdict…',stage='download')
        with urllib.request.urlopen(request,timeout=60) as response, source.open('wb') as f:
            for chunk in iter(lambda:response.read(256*1024),b''):
                if should_stop(): raise Cancelled('已按请求取消下载。')
                total+=len(chunk)
                if total>MAX_DOWNLOAD: raise ValueError('下载文件超过大小限制。')
                f.write(chunk)
                if total % (8*1024*1024) < 256*1024: progress(f'已下载 {total//(1024*1024)} MB',stage='download',bytes=total)
        progress('正在建立索引…',stage='build',bytes=total)
        return build(source,output,progress,cancelled)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path); parser.add_argument('--out',type=Path,default=DEFAULT_PATH)
    parser.add_argument('--download',action='store_true')
    args=parser.parse_args()
    if args.download: download(args.out)
    elif args.input: build(args.input,args.out)
    else: parser.error('需要 --input 或 --download')

if __name__=='__main__': main()
