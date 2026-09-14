"""Cursor-based search across content packs, the local dictionary and personal entries.

The previous route took the first 100 index rows, mixed in up to 100 dictionary rows and
then sliced by cursor, so `total` described the truncated candidate set rather than the
match set, page two of a 242-match query was empty, and the favourites filter could only
see the rows that survived truncation (LEX-08, §9.1).

Each source here is ordered by the same key — `(match rank, not common, sourceRef)` — and
carries its own offset inside one opaque cursor. Merging the next `limit + 1` of every
source is enough to emit the next `limit` in global order: anything further down a source
is by construction greater than everything already in hand, so pages never overlap and
never skip.
"""
from __future__ import annotations

import base64
import json

SCOPES = ('all', 'packs', 'dictionary', 'personal')
FIELDS = ('head', 'reading', 'roman', 'gloss', 'examples', 'connection')
LEVELS = ('N1', 'N2', 'N3', 'N4', 'N5', 'ungraded')


class CursorError(ValueError):
    """The cursor cannot be honoured, so the caller must restart from the first page."""


def encode_cursor(state: dict) -> str:
    raw = json.dumps(state, separators=(',', ':'), sort_keys=True).encode('utf-8')
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def decode_cursor(value: str) -> dict:
    if not value:
        return {}
    # A bare integer is the pre-cursor offset format; treat it as "start over".
    if value.isdigit():
        raise CursorError('搜索游标格式已更新，请从第一页重新查询。')
    try:
        padded = value + '=' * (-len(value) % 4)
        state = json.loads(base64.urlsafe_b64decode(padded.encode('ascii')).decode('utf-8'))
    except (ValueError, UnicodeDecodeError) as exc:
        raise CursorError('搜索游标无效，请从第一页重新查询。') from exc
    if not isinstance(state, dict):
        raise CursorError('搜索游标无效，请从第一页重新查询。')
    return state


def sort_key(item: dict) -> tuple:
    """One frozen order for every source, so a merged page is stable across requests."""
    return (int(item.get('score', 50)), 0 if item.get('common') else 1, str(item.get('sourceRef', '')))


def _integer(value, default, minimum, maximum):
    try:
        result = int(value if value is not None else default)
    except (ValueError, TypeError):
        raise ValueError('分页或题量参数无效。')
    if not minimum <= result <= maximum:
        raise ValueError('分页或题量参数超出范围。')
    return result


def _validate(params: dict) -> dict:
    kind = params.get('kind', '')
    level = params.get('level', '')
    scope = params.get('scope') or 'all'
    field = params.get('field', '')
    pack = params.get('pack', '')
    unit = params.get('unit', '')
    if kind not in {'', 'word', 'grammar'}:
        raise ValueError('未知内容类型。')
    if level not in ('',) + LEVELS:
        raise ValueError('未知等级。')
    if scope not in SCOPES:
        raise ValueError('未知查询来源。')
    if field and field not in FIELDS:
        raise ValueError('查询字段无效。')
    if unit and not pack:
        # `u1` exists in more than one pack, so an unqualified unit would match across them.
        raise ValueError('按单元筛选时必须同时指定内容包。')
    if unit and scope == 'dictionary':
        raise ValueError('词典查询不接受教材单元。')
    if pack and scope == 'dictionary':
        raise ValueError('词典查询不接受内容包筛选。')
    return {'kind': kind, 'level': level, 'scope': scope, 'field': field, 'pack': pack, 'unit': unit,
            'limit': _integer(params.get('limit'), 20, 1, 100),
            'starred': params.get('starred') == '1'}


def _personal_rows(services, options, refs):
    """Personal entries that are not already represented by another source.

    A favourited pack entry is the same entity as its pack row, and the pack row carries
    the richer snapshot, so it is not emitted twice.
    """
    from jp_inflection import normalize
    needle = normalize(options['query'], reading=True)
    rows = []
    if not needle:
        return rows
    dictionary_covered = options['dictionary_available'] and options['scope'] in {'all', 'dictionary'}
    for entry in services.practice.user_entries():
        ref = entry['sourceRef']
        if ref.startswith('lex:'):
            continue
        if ref.startswith('dict:') and dictionary_covered:
            continue
        if refs is not None and ref not in refs:
            continue
        if options['kind'] and entry.get('kind', 'word') != options['kind']:
            continue
        if options['level'] and entry.get('level', '') != options['level']:
            continue
        haystack = normalize(' '.join([
            str(entry.get('headword', '')), str(entry.get('reading', '')), str(entry.get('note', '')),
            json.dumps(entry.get('gloss', {}), ensure_ascii=False),
        ]), reading=True)
        if needle not in haystack:
            continue
        rows.append({**entry, 'id': ref, 'sourceRef': ref, 'score': 40, 'matchField': '个人条目/笔记'})
    rows.sort(key=sort_key)
    return rows


def search(services, params: dict) -> dict:
    options = _validate(params)
    query = str(params.get('q', '')).strip()
    options['query'] = query
    cursor = decode_cursor(str(params.get('cursor', '')))
    limit = options['limit']

    dictionary_status = services.dictionary.status()
    options['dictionary_available'] = bool(dictionary_status.get('available'))

    with services.index.lock:
        services.index.refresh()
        index_revision = services.index.revision
    if cursor and cursor.get('rev') and cursor['rev'] != index_revision:
        raise CursorError('内容索引已更新，请从第一页重新查询当前条件。')

    personal = services.practice.user_entries()
    saved = {entry['sourceRef']: entry for entry in personal}
    refs = None
    if options['starred']:
        # Reverse-looked-up from the complete favourites set, never filtered after paging.
        refs = {ref for ref, entry in saved.items() if entry.get('starred')}
        if not refs:
            refs = set()

    available = ['packs', 'personal'] + (['dictionary'] if options['dictionary_available'] else [])
    wanted = available if options['scope'] == 'all' else [options['scope']]
    active = [name for name in wanted if name in available or name == 'personal']

    notes = []
    if options['scope'] == 'dictionary' and options['kind'] == 'grammar':
        # The dictionary holds no grammar patterns; saying so beats returning word rows.
        return {'query': query, 'results': [], 'total': 0, 'totalRelation': 'eq', 'hasMore': False,
                'nextCursor': None, 'scope': 'dictionary', 'availableSources': available,
                'indexRevision': index_revision, 'dictionaryAvailable': options['dictionary_available'],
                'notes': ['词典只收录词条，没有语法文型。']}

    offsets = cursor.get('offsets') if isinstance(cursor.get('offsets'), dict) else {}
    windows: dict[str, list] = {}
    totals: dict[str, int] = {}
    capped = False

    if 'packs' in active and query:
        start = int(offsets.get('packs') or 0)
        page = services.index.search(
            query, kind=options['kind'], level=options['level'], pack=options['pack'],
            unit=options['unit'], field=options['field'], limit=limit + 1, offset=start, refs=refs,
        )
        windows['packs'] = page['results']
        totals['packs'] = page['total']

    if 'dictionary' in active and query and options['kind'] != 'grammar' and not options['pack']:
        start = int(offsets.get('dictionary') or 0)
        try:
            rows = services.dictionary.search(query, start + limit + 1)
        except ValueError as exc:
            # The dictionary's own limits are tighter than the index's. Say the source was
            # skipped rather than failing a query the packs could still answer.
            rows = []
            notes.append(f'词典未参与本次查询：{exc}')
        if refs is not None:
            rows = [row for row in rows if row.get('sourceRef') in refs]
        if options['level']:
            rows = []  # JMdict carries no JLPT level; claiming a match would be inventing one.
        rows.sort(key=sort_key)
        capped = len(rows) >= services.dictionary.candidate_cap
        windows['dictionary'] = rows[start:start + limit + 1]
        totals['dictionary'] = len(rows)

    if 'personal' in active and query:
        start = int(offsets.get('personal') or 0)
        rows = _personal_rows(services, options, refs)
        windows['personal'] = rows[start:start + limit + 1]
        totals['personal'] = len(rows)

    # Merge the heads of every window until the page is full.
    heads = {name: 0 for name in windows}
    merged = []
    while len(merged) < limit:
        best = None
        for name, rows in windows.items():
            index = heads[name]
            if index >= len(rows):
                continue
            key = sort_key(rows[index])
            if best is None or key < best[0]:
                best = (key, name)
        if best is None:
            break
        name = best[1]
        merged.append(windows[name][heads[name]])
        heads[name] += 1

    consumed = {name: int(offsets.get(name) or 0) + heads[name] for name in windows}
    remaining = sum(max(0, totals.get(name, 0) - consumed[name]) for name in windows)
    has_more = remaining > 0

    for item in merged:
        item['starred'] = bool(saved.get(item.get('sourceRef'), {}).get('starred'))

    total = sum(totals.values())
    relation = 'gte' if capped else 'eq'
    if capped:
        notes.append('词典候选达到本次查询上限，总数为下限值。')

    return {
        'query': query,
        'results': merged,
        'total': total,
        'totalRelation': relation,
        'hasMore': has_more,
        'nextCursor': encode_cursor({'rev': index_revision, 'offsets': consumed}) if has_more else None,
        'scope': options['scope'],
        'availableSources': available,
        'sourceTotals': totals,
        'indexRevision': index_revision,
        'dictionaryAvailable': options['dictionary_available'],
        'notes': notes,
    }
