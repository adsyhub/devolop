"""Bounded Japanese lookup normalization and deinflection candidates.

Candidates are suggestions only: DictionaryStore must validate the base and POS.
"""
from __future__ import annotations
import re
import unicodedata


def normalize(text: str, *, reading: bool = False) -> str:
    value = unicodedata.normalize("NFKC", str(text)).strip().lower()
    value = re.sub(r"[〜～~]", "", value)
    if reading:
        value = ''.join(chr(ord(c)-0x60) if 'ァ' <= c <= 'ヶ' else c for c in value)
    return ' '.join(value.split())


_ROWS = [('あいうえお','a i u e o'),('かきくけこ','ka ki ku ke ko'),('さしすせそ','sa shi su se so'),
         ('たちつてと','ta chi tsu te to'),('なにぬねの','na ni nu ne no'),('はひふへほ','ha hi fu he ho'),
         ('まみむめも','ma mi mu me mo'),('やゆよ','ya yu yo'),('らりるれろ','ra ri ru re ro'),
         ('わをん','wa wo n'),('がぎぐげご','ga gi gu ge go'),('ざじずぜぞ','za ji zu ze zo'),
         ('だぢづでど','da ji zu de do'),('ばびぶべぼ','ba bi bu be bo'),('ぱぴぷぺぽ','pa pi pu pe po')]
_ROMAJI = {kana: roman for kana_row, roman_row in _ROWS for kana, roman in zip(kana_row, roman_row.split())}
for base, prefix in [('き','ky'),('ぎ','gy'),('し','sh'),('じ','j'),('ち','ch'),('に','ny'),('ひ','hy'),('び','by'),('ぴ','py'),('み','my'),('り','ry')]:
    for small, vowel in [('ゃ','a'),('ゅ','u'),('ょ','o')]: _ROMAJI[base+small] = prefix+vowel
# Loanword digraphs. Katakana is folded to hiragana before this table is consulted, so
# ファ arrives as ふぁ; without an entry it would romanize as "fua" rather than "fa".
for base, prefix in [('ふ','f'),('う','w'),('く','kw'),('ぐ','gw'),('つ','ts'),('で','d'),('て','t'),('ゔ','v')]:
    for small, vowel in [('ぁ','a'),('ぃ','i'),('ぅ','u'),('ぇ','e'),('ぉ','o')]:
        _ROMAJI.setdefault(base+small, prefix+vowel)
_ROMAJI.update({'ゐ':'i','ゑ':'e','ぁ':'a','ぃ':'i','ぅ':'u','ぇ':'e','ぉ':'o','ゎ':'wa'})


def romanize(text: str) -> str:
    s = normalize(text, reading=True); result = ''; i = 0
    while i < len(s):
        pair = s[i:i+2]
        if s[i] == 'っ' and i+1 < len(s):
            # Geminate: repeat the first consonant of the syllable that follows. Before
            # the ch- row Hepburn writes t, so っち is "tchi" (matcha), not "cchi".
            following = _ROMAJI.get(s[i+1:i+3], _ROMAJI.get(s[i+1], s[i+1]))
            if following.startswith('ch'): result += 't'
            elif following[:1] in ('', 'a', 'i', 'u', 'e', 'o'): result += 't'
            else: result += following[0]
            i += 1; continue
        if s[i] == 'ー':
            result += result[-1:] if result[-1:] in 'aeiou' else ''; i += 1; continue
        if s[i] == 'ん':
            # Moraic n. Before a vowel it needs the apostrophe, or しんあい and しない
            # would both come out "sinai"; before b/m/p it is conventionally written m.
            nxt = _ROMAJI.get(s[i+1:i+3], _ROMAJI.get(s[i+1:i+2], ''))
            result += 'm' if nxt[:1] in ('b', 'm', 'p') else ("n'" if nxt[:1] in ('a','i','u','e','o','y') else 'n')
            i += 1; continue
        if pair in _ROMAJI:
            result += _ROMAJI[pair]; i += 2
        else:
            result += _ROMAJI.get(s[i], s[i]); i += 1
    return result


# Keyboard spellings people actually type, mapped onto what `romanize` produces. These
# are input aliases only: an unsupported spelling returns no result rather than being
# "corrected" into a different word (§9.3).
_ALIASES = (('si','shi'),('ti','chi'),('tu','tsu'),('hu','fu'),('zi','ji'),('di','ji'),('du','zu'),
            ('sya','sha'),('syu','shu'),('syo','sho'),('tya','cha'),('tyu','chu'),('tyo','cho'),
            ('jya','ja'),('jyu','ju'),('jyo','jo'),('cya','cha'),('nn',"n"),('wo','o'))


def roman_candidates(text: str) -> list[str]:
    """Common keyboard spelling aliases; never changes the stored reading."""
    s = normalize(text)
    if len(s) > 64: raise ValueError('罗马字查询最多 64 字符。')
    values = {s}
    aliased = s
    for typed, canonical in _ALIASES: aliased = aliased.replace(typed, canonical)
    values.add(aliased)
    # Long vowels are typed both ways: "tōkyō" as toukyou or tookyoo.
    for value in list(values):
        values.add(value.replace('ou','oo'))
        values.add(value.replace('oo','ou'))
        values.add(value.replace('uu','u'))
    # Moraic n is written three ways, and an index built by an older version of
    # `romanize` stored the plain form. Offering every spelling keeps an already
    # installed dictionary searchable without rebuilding it.
    for value in list(values):
        plain = value.replace("n'", 'n')
        values.add(plain)
        values.add(re.sub(r'n(?=[bmp])', 'm', plain))
        values.add(re.sub(r'm(?=[bmp])', 'n', plain))
    return sorted(v for v in values if v)


# Each rule records what it consumes and what it produces, so a chain can be checked
# instead of only its last step's part of speech being kept. `derived` marks a rule whose
# output is itself an inflectable verb form (a potential/passive/causative stem, or a
# て-form taking an auxiliary); anything else produces a dictionary form, and applying a
# further rule to one of those is what used to invent candidates like 食べる → 食ぶ (§9.3).
RULES: list[dict] = []


def _rule(ending: str, base: str, pos: str, label: str, *, derived: bool = False) -> None:
    RULES.append({'ending': ending, 'base': base, 'pos': pos, 'label': label,
                  'derived': derived, 'cost': len(ending)})

for end, label in [('ました','过去礼貌形'),('ませんでした','过去否定礼貌形'),('ません','否定礼貌形'),('ます','礼貌形'),('ない','否定形'),('なかった','过去否定形'),('て','て形'),('た','过去形'),('れば','条件形'),('よう','意向形')]:
    _rule(end,'る','v1',label)
for end, label in [('られる','可能/被动形'),('させる','使役形')]:
    _rule(end,'る','v1',label,derived=True)
for base, a, i, e, o in [('う','わ','い','え','お'),('く','か','き','け','こ'),('ぐ','が','ぎ','げ','ご'),('す','さ','し','せ','そ'),('つ','た','ち','て','と'),('ぬ','な','に','ね','の'),('ぶ','ば','び','べ','ぼ'),('む','ま','み','め','も'),('る','ら','り','れ','ろ')]:
    pos = {'う':'v5u','く':'v5k','ぐ':'v5g','す':'v5s','つ':'v5t','ぬ':'v5n','ぶ':'v5b','む':'v5m','る':'v5r'}[base]
    for end,label in [(i+'ます','礼貌形'),(i+'ました','过去礼貌形'),(i+'ません','否定礼貌形'),(i+'ませんでした','过去否定礼貌形'),(a+'ない','否定形'),(a+'なかった','过去否定形'),(e+'ば','条件形'),(o+'う','意向形')]: _rule(end,base,pos,label)
    for end,label in [(e+'る','可能形'),(a+'れる','被动形'),(a+'せる','使役形')]: _rule(end,base,pos,label,derived=True)
for endings,bases in [(('って','った'),['う','つ','る']),(('いて','いた'),['く']),(('いで','いだ'),['ぐ']),(('んで','んだ'),['ぬ','ぶ','む']),(('して','した'),['す'])]:
    for end in endings:
        for base in bases: _rule(end,base,{'う':'v5u','つ':'v5t','る':'v5r','く':'v5k','ぐ':'v5g','ぬ':'v5n','ぶ':'v5b','む':'v5m','す':'v5s'}[base],'て/た形')
for end in ['くない','くなかった','かった','くて','ければ']: _rule(end,'い','adj-i','形容词变化')
for end in ['します','しました','しません','しませんでした','して','した','しない','しなかった','すれば','しよう','される','させる']: _rule(end,'する','vs','する变化')
for end in ['来ます','来ました','来ない','来なかった','来て','来た','来れば','来よう','来られる','来させる']: _rule(end,'来る','vk','来る变化')
for end in ['きます','きました','こない','こなかった','きて','きた','くれば','こよう','こられる']: _rule(end,'くる','vk','くる变化')
for end in ['行って','行った']: _rule(end,'行く','v5k','行く特殊变化')
for end in ['よくない','よかった','よくて','よければ']: _rule(end,'いい','adj-i','いい特殊变化')
for end in ['ている','ていた','ていない']: _rule(end,'て','v','持续形',derived=True)
for end in ['でいる','でいた','でいない']: _rule(end,'で','v','持续形',derived=True)


MAX_QUERY = 64


def deinflect(text: str, max_depth: int = 3, limit: int = 96) -> list[dict]:
    """Base-form candidates for one surface form, breadth first.

    Breadth first means the first time a form is reached is by its shortest chain, so the
    cheapest derivation wins and longer ones for the same (form, part of speech) are
    dropped. Every candidate carries `steps` with each rule's input and output class,
    depth and cost; `pos` stays the class the dictionary must confirm.
    """
    query = normalize(text, reading=True)
    if len(query) > MAX_QUERY: raise ValueError(f'查询内容最多 {MAX_QUERY} 字。')
    root = {'text': query, 'pos': '', 'chain': [], 'steps': [], 'cost': 0, 'inflectable': True}
    queue = [root]; seen = {(query, '')}; out = []
    for candidate in queue:
        out.append(candidate)
        if len(candidate['chain']) >= max_depth: continue
        # Only a surface form or a derived stem can carry another ending. A completed
        # dictionary form cannot, and treating it as one invents words.
        if not candidate['inflectable']: continue
        for rule in RULES:
            if not candidate['text'].endswith(rule['ending']): continue
            changed = candidate['text'][:-len(rule['ending'])] + rule['base']
            if len(changed) < 2 or (changed, rule['pos']) in seen: continue
            seen.add((changed, rule['pos']))
            queue.append({
                'text': changed, 'pos': rule['pos'],
                'chain': candidate['chain'] + [rule['label']],
                'steps': candidate['steps'] + [{
                    'label': rule['label'], 'from': candidate['pos'] or 'surface', 'to': rule['pos'],
                    'ending': rule['ending'], 'depth': len(candidate['chain']) + 1, 'cost': rule['cost'],
                }],
                'cost': candidate['cost'] + rule['cost'],
                'inflectable': rule['derived'],
            })
            if len(queue) >= limit: return queue
    return out
