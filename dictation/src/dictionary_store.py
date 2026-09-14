"""Read-only SQLite dictionary. No network access during lookup."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from jp_inflection import normalize, roman_candidates, deinflect


POINTER_NAME = 'current.json'


class DictionaryStore:
    # How many candidates one lookup will assemble. A query that reaches it reports its
    # total as a lower bound rather than pretending the number is exact (§9.1).
    candidate_cap = 200

    def __init__(self, path: Path):
        self.nominal_path = Path(path)

    @property
    def path(self) -> Path:
        """Where the installed dictionary actually is.

        A build publishes into `versions/<revision>/` and then moves one pointer file, so
        the database and its SOURCES sidecar become current together. Resolving through
        the pointer on every access means an install that lands mid-session is picked up,
        and a half-written version directory is never served (§9.4).
        """
        pointer = self.nominal_path.parent / POINTER_NAME
        try:
            if pointer.is_file():
                target = self.nominal_path.parent / json.loads(pointer.read_text(encoding='utf-8'))['path']
                if target.is_file(): return target
        except (OSError, ValueError, KeyError):
            pass
        return self.nominal_path

    def connect(self):
        conn = sqlite3.connect(self.path.resolve().as_uri()+'?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def status(self) -> dict:
        path = self.path
        if not path.is_file(): return {'available':False, 'message':'尚未安装本地词典，可继续查询内容包。'}
        try:
            with self.connect() as c:
                metadata = dict(c.execute('SELECT key,value FROM metadata').fetchall())
            # Say which search capability this build actually has, so a degraded install
            # is visible rather than silently returning fewer results (§9.3).
            index = str(metadata.get('fts') or 'none')
            return {'available':True, **metadata, 'path':str(path),
                    'indexCapability':index,
                    'glossSearch':index != 'none',
                    'degraded':index == 'none',
                    'degradedReason':'' if index != 'none' else '本次构建没有 FTS5，释义全文检索不可用；表记、读音与前缀查询正常。'}
        except sqlite3.Error:
            return {'available':False,'message':'词典索引不可读，请重新导入。'}

    def get(self, key: str) -> dict | None:
        if not self.path.exists(): return None
        with self.connect() as c:
            row = c.execute('SELECT data FROM entries WHERE id=?',(key,)).fetchone()
        return json.loads(row[0]) if row else None

    # ---- written form / reading / sense compatibility (LEX-09, §9.2) --------

    @staticmethod
    def readings_for(entry: dict, written: str = '') -> list[dict]:
        """Readings that may be used with *written*.

        `re_restr` says a reading only applies to some spellings and `re_nokanji` says it
        is not a reading of the kanji at all. Consumers that take `readings[0]` publish a
        pairing the dictionary explicitly rules out.
        """
        allowed = []
        for reading in entry.get('readings') or []:
            restrictions = reading.get('restrictions') or []
            if written and restrictions and written not in restrictions: continue
            if written and reading.get('noKanji') and written != reading.get('text'): continue
            allowed.append(reading)
        return allowed or list(entry.get('readings') or [])

    @staticmethod
    def senses_for(entry: dict, written: str = '', reading: str = '') -> list[dict]:
        """Senses compatible with a chosen spelling and reading."""
        allowed = []
        for sense in entry.get('senses') or []:
            written_only = sense.get('writtenRestrictions') or []
            reading_only = sense.get('readingRestrictions') or []
            if written and written_only and written not in written_only: continue
            if reading and reading_only and reading not in reading_only: continue
            allowed.append(sense)
        return allowed

    def selection_options(self, entry: dict) -> dict:
        """The choices a learner actually has, as a compatible tree."""
        forms = list(entry.get('writtenForms') or []) or [
            reading.get('text', '') for reading in entry.get('readings') or []
        ]
        tree = []
        for written in forms:
            readings = self.readings_for(entry, written)
            tree.append({
                'writtenForm': written,
                'readings': [{
                    'reading': reading.get('text', ''),
                    'senses': [{'key': sense.get('key', ''), 'gloss': sense.get('gloss', []),
                                'notes': sense.get('notes', []), 'pos': sense.get('pos', [])}
                               for sense in self.senses_for(entry, written, reading.get('text', ''))],
                } for reading in readings],
            })
        return {'writtenForms': tree, 'dictionaryVersion': str(self.status().get('sourceSha256') or '')}

    def resolve_selection(self, entry: dict, selection: dict) -> dict:
        """Check a stored selection against the installed dictionary.

        A rebuilt dictionary can change a sense key, because the key is a hash of the
        sense's own content. That must not silently swap the learner's meaning for a
        different one, so an unresolved selection reports candidates instead (§9.2.6).
        """
        written = str(selection.get('writtenForm') or '')
        reading = str(selection.get('reading') or '')
        wanted = [str(key) for key in selection.get('senseKeys') or []]
        by_key = {str(sense.get('key')): sense for sense in entry.get('senses') or []}
        matched = [by_key[key] for key in wanted if key in by_key]
        missing = [key for key in wanted if key not in by_key]
        version = str(self.status().get('sourceSha256') or '')
        stale = bool(selection.get('dictionaryVersion')) and selection['dictionaryVersion'] != version
        return {
            'writtenForm': written, 'reading': reading,
            'senses': matched, 'missingSenseKeys': missing,
            'resolved': bool(wanted) and not missing,
            'chosen': bool(wanted),
            'dictionaryChanged': stale,
            # Candidates to re-confirm against, never an automatic substitution.
            'candidates': [] if not missing else [
                {'key': sense.get('key', ''), 'gloss': sense.get('gloss', []), 'notes': sense.get('notes', [])}
                for sense in self.senses_for(entry, written, reading)
            ],
        }

    def _annotate_match(self, item: dict, matched_text: str) -> dict:
        """Record which spelling and readings this hit actually was.

        Returning the record's first reading regardless of what matched attributes a
        reading to a spelling the entry may not allow (§9.2.1).
        """
        written = list(item.get('writtenForms') or [])
        if matched_text and matched_text in written:
            item['matchedForm'] = matched_text
            item['readingCandidates'] = [r.get('text','') for r in self.readings_for(item, matched_text)]
        elif matched_text and any(matched_text == r.get('text') for r in item.get('readings') or []):
            item['matchedForm'] = ''
            item['readingCandidates'] = [matched_text]
        else:
            item['matchedForm'] = written[0] if written else ''
            item['readingCandidates'] = [r.get('text','') for r in self.readings_for(item, item.get('matchedForm',''))]
        item['reading'] = item['readingCandidates'][0] if item['readingCandidates'] else item.get('reading','')
        item['senseCount'] = len(item.get('senses') or [])
        return item

    def search(self, query: str, limit: int = 30) -> list[dict]:
        if not self.path.is_file() or not query.strip(): return []
        needle = normalize(query,reading=True)
        found: dict[str, dict] = {}
        with self.connect() as c:
            for candidate in deinflect(needle):
                for row in c.execute('SELECT DISTINCT e.id,e.data,f.text FROM forms f JOIN entries e ON e.id=f.entry_id WHERE f.normalized=? LIMIT 60',(candidate['text'],)):
                    item = json.loads(row['data']); pos = ' '.join(item.get('pos',[]))
                    if candidate['pos'] and candidate['pos'] not in pos: continue
                    score = 0 if not candidate['chain'] else 30+len(candidate['chain'])
                    if row['id'] not in found or found[row['id']]['score']>score:
                        found[row['id']] = self._annotate_match(
                            {**item,'score':score,'matchField':'原形' if candidate['chain'] else '表记/读音','chain':candidate['chain']},
                            row['text'])
            for roman in roman_candidates(query):
                for row in c.execute('SELECT DISTINCT e.id,e.data FROM forms f JOIN entries e ON e.id=f.entry_id WHERE f.roman=? LIMIT 40',(roman,)):
                    found.setdefault(row['id'], {**json.loads(row['data']),'score':10,'matchField':'罗马字','chain':[]})
            upper = needle + '\U0010ffff'
            for row in c.execute('SELECT DISTINCT e.id,e.data FROM forms f JOIN entries e ON e.id=f.entry_id WHERE f.normalized>=? AND f.normalized<? LIMIT 80',(needle,upper)):
                found.setdefault(row['id'],{**json.loads(row['data']),'score':20,'matchField':'前缀','chain':[]})
            if len(found)<limit and len(needle)>=3:
                try:
                    rows=c.execute('SELECT e.id,e.data FROM entry_fts f JOIN entries e ON e.id=f.entry_id WHERE entry_fts MATCH ? LIMIT 60',('"'+needle.replace('"','""')+'"',))
                    for row in rows: found.setdefault(row['id'],{**json.loads(row['data']),'score':50,'matchField':'词典释义','chain':[]})
                except sqlite3.OperationalError: pass
        return sorted(found.values(),key=lambda x:(x['score'],not x.get('common'),x['id']))[:max(limit,1)]
