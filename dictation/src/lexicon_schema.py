"""Vocabulary and grammar packs: schema, stable identity, connection grammar, audit.

A *pack* is one book turned into learnable entries — 「新日语能力考试考前对策 N2 文法」,
say — stored as a single ``pack.json`` the way an exam is one ``exam.json`` and a course
is one ``manifest.json``. ``prepare_pack`` assigns deterministic ids and derived counts,
``audit_pack`` returns a report in exactly the shape ``audit_exam`` and ``audit_manifest``
return, so the fail-closed loading rule in ``serve_course`` applies to packs without
inventing a third vocabulary for "this content is broken".

One schema for words and grammar
--------------------------------
An entry is ``kind: "word" | "grammar"`` with the kind-specific fields hanging off a
``word`` / ``grammar`` sub-object. They share everything that costs real work — stable
ids, level grouping, multilingual glosses, examples, source tracing, card templates,
audit rules — and differ in two fields. Splitting them into two modules would not have
saved code, it would have bought two import pipelines, two offline strategies and two
answers to "how much do I owe today", and the learner needs one number, not "40 words
and 12 grammar points".

Identity is not the text
------------------------
OCR mis-reads characters, textbook entries span page breaks, and units get reordered
when a gap is filled. So the headword, the ``unitId`` and the printed ``order`` are all
excluded from the id::

    entryId = kind[0] + "_" + sha256(packId + US + entryKey)[:24]

``entryKey`` is frozen once, in ``entry-keys.json``, and never recomputed from the text.
Fixing a typo therefore keeps every SRS card attached to the entry it belongs to. 24 hex
characters is 96 bits, matching the question bank; the 24 bits of a 6-character id would
collide at least once in a 2,000-word pack with probability ≈11%.

Text markup
-----------
Entry text is plain UTF-8 with four printable conventions, three shared with the
question bank so the two renderers agree:

===================  ==================================================
``｜漢字《かんじ》``    furigana printed above the base text (full-width ｜)
``<u>…</u>``          an underlined span
``【…】``              a connection placeholder — ``【V辞書形】＋うちに``
``⟦…⟧``               the span a cloze card blanks out
===================  ==================================================

Connection notation
-------------------
The book prints connections as a closed abbreviation vocabulary (see its 接続の表示方法
legend): a base marker ``V`` / ``A`` / ``na`` / ``N`` / ``普`` followed by an inflection
marker from that base's table. It is *not* Japanese text: the OCR of this very book read
``naで`` as ``なで``. So connections are stored structured, an unknown abbreviation is an
error rather than a guess, and ``なで`` fails loudly with the confusion named.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

SCHEMA_VERSION = 1

PACK_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
ENTRY_KEY_PATTERN = re.compile(r"^e[0-9]{4,}$")
ENTRY_ID_PATTERN = re.compile(r"^[wg]_[0-9a-f]{24}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

#: ``lex:<packId>#<entryId>`` — how a card, a confusable or an alias names an entry.
SOURCE_REF_PATTERN = re.compile(r"^lex:([A-Za-z0-9][A-Za-z0-9._-]{0,63})#([wg]_[0-9a-f]{24})$")

LEVELS = ("N1", "N2", "N3", "N4", "N5", "ungraded")
ENTRY_KINDS = ("word", "grammar")
PROMPT_TYPES = ("recall", "production", "cloze", "usage")
GLOSS_LANGUAGES = ("zh", "en", "ko")
READING_SOURCES = ("dictionary", "manual")
SOURCE_TYPES = ("textbook-ocr", "open-dictionary", "original")

#: The unit separator that joins the two halves of an id's namespace. A literal
#: character no identifier may contain, so ``pack``+``e0012`` cannot collide with
#: ``pac``+``ke0012``.
US = "\x1f"

_RUBY_OPEN, _RUBY_CLOSE = "《", "》"
_SLOT_OPEN, _SLOT_CLOSE = "【", "】"
_CLOZE_OPEN, _CLOZE_CLOSE = "⟦", "⟧"
_UNDERLINE_OPEN, _UNDERLINE_CLOSE = "<u>", "</u>"

# Entry text is OCR output. "The model emitted a stray tag" is a real failure mode
# here, not a hypothetical one, and it must not reach the renderer.
_STRAY_TAG = re.compile(r"</?(?!u>)[A-Za-z][^>]*>")

# The wave-dash family. 〜 (U+301C), ～ (U+FF5E) and ~ (U+007E) are printed
# interchangeably and OCR picks whichever it feels like; they are normalised away for
# search and duplicate detection but never for identity.
_WAVE_DASH = re.compile(r"[〜～~]")
_ASCII_LETTER = re.compile(r"[A-Za-z]")


# ---------------------------------------------------------------------------
# Connection notation
# ---------------------------------------------------------------------------

#: Base markers exactly as the book prints them, with the display form the UI shows.
#: ``A`` and ``na`` become イA / ナA on screen because "A" alone does not tell a learner
#: which adjective class is meant, and the two take different connections.
CONNECTION_BASES: dict[str, dict[str, str]] = {
    "V": {"slot": "verb", "display": "V", "label": "動詞"},
    "A": {"slot": "i-adjective", "display": "イA", "label": "い形容詞"},
    "na": {"slot": "na-adjective", "display": "ナA", "label": "な形容詞"},
    "N": {"slot": "noun", "display": "N", "label": "名詞"},
    "普": {"slot": "plain-form", "display": "普通形", "label": "普通形"},
    # Week 8 teaches discourse connectors whose left-hand operand is a complete
    # clause, not an inflecting word.  Modelling that as 普通形 produces the wrong
    # learning prompt, so it has its own connection slot.
    "文": {"slot": "clause", "display": "文", "label": "文・句"},
}

#: Inflection markers per base, transcribed from the book's own 接続の表示方法 tables.
#: A marker that is not here is an error, not something to pattern-match around: the
#: whole point of storing connections structured is that ``なで`` cannot pass as ``naで``.
#: ``""`` is the dictionary / stem form the tables list first.
CONNECTION_FORMS: dict[str, dict[str, str]] = {
    "V": {
        "": "verb",
        "る": "verb",
        "辞書形": "verb",
        "基本形": "verb",
        "ない": "verb",
        "なかった": "verb",
        "ます": "verb",
        "て": "verb",
        "で": "verb",
        "た": "verb",
        "だ": "verb",
        "ている": "verb",
        "ば": "verb",
        "よう": "verb",
        "れる": "verb",
        "られる": "verb",
        "させる": "verb",
        "命令形": "verb",
        # Vたい is an い-adjective grown out of a verb, and the book connects through it
        # (Vたくてたまらない). Its own slot, because a card that teaches "attach to the
        # て-form of a verb" would be teaching the wrong thing.
        "たい": "verb-desiderative",
        "たく": "verb-desiderative",
        "たくて": "verb-desiderative",
    },
    "A": {
        "": "i-adjective",
        "い": "i-adjective",
        "く": "i-adjective",
        "くて": "i-adjective",
        "くない": "i-adjective",
        "かった": "i-adjective",
        "ければ": "i-adjective",
    },
    "na": {
        "": "na-adjective",
        "だ": "na-adjective",
        "な": "na-adjective",
        "で": "na-adjective",
        "でない": "na-adjective",
        "だった": "na-adjective",
        "なら": "na-adjective",
        "である": "na-adjective",
    },
    "N": {
        "": "noun",
        "だ": "noun",
        "の": "noun",
        "で": "noun",
        "でない": "noun",
        "だった": "noun",
        "なら": "noun",
        # The book uses both な (before explanatory nominalisers such as もの) and
        # the formal である form in its connection frames.
        "な": "noun",
        "である": "noun",
        "する": "noun",
    },
    "普": {"": "plain-form"},
    "文": {"": "clause"},
}

#: Abbreviations this book's OCR is known to mangle, mapped to what was printed. Used
#: only to make the error message say what happened; nothing is silently rewritten.
CONNECTION_CONFUSIONS: dict[str, str] = {
    "な": "na",
    "ナ": "na",
    "n": "N",
    "ｎ": "N",
    "Ｎ": "N",
    "ｖ": "V",
    "Ｖ": "V",
    "Ａ": "A",
    "ａ": "A",
}


class ConnectionError_(ValueError):
    """An abbreviation the book's legend does not define."""


def parse_connection(raw: str) -> dict[str, str]:
    """Turn one printed connection token into ``{slot, form, display, tail}``.

    ``"Aくて"`` → i-adjective / ``くて``; ``"Nがち"`` → noun / ``""`` with ``がち`` as the
    pattern's own tail; ``"なで"`` raises, naming ``naで`` as the probable original.
    """
    token = str(raw or "").strip()
    token = token.replace("／", "/").strip()
    if not token:
        raise ConnectionError_("Empty connection token.")

    base = next((marker for marker in ("na", "普", "文", "V", "A", "N") if token.startswith(marker)), None)
    if base is None:
        confused = CONNECTION_CONFUSIONS.get(token[0])
        hint = f" Did the scan read {confused + token[1:]!r} as {token!r}?" if confused else ""
        raise ConnectionError_(f"Unknown connection base in {token!r}.{hint}")

    rest = token[len(base) :]
    if base == "普" and rest not in {"", "形", "通形"}:
        # 普 is the one base marker that is also an ordinary kanji. Without this, 普段
        # and 普通 would parse as connections and a headword line could be swallowed.
        raise ConnectionError_(f"{token!r} starts with 普 but is not the 普通形 marker.")
    if base == "文" and rest and not rest.startswith("。"):
        # 文 is also an ordinary kanji.  The book's discourse notation is either the
        # bare slot or ``文。接続詞``; words such as 文章 must remain ordinary text.
        raise ConnectionError_(f"{token!r} starts with 文 but is not a clause connection marker.")
    forms = CONNECTION_FORMS[base]
    # Longest match first: "Vたくて" is the desiderative, not "Vた" plus a stray "くて".
    form = max((marker for marker in forms if rest.startswith(marker)), key=len, default=None)
    if form is None:
        raise ConnectionError_(f"Unknown inflection marker in {token!r} for base {base!r}.")

    tail = rest[len(form) :]
    if tail and _looks_like_abbreviation(tail):
        raise ConnectionError_(
            f"{token!r} looks like two connections run together; split them into separate lines."
        )
    if tail and (_ASCII_LETTER.search(tail) or " " in tail or "　" in tail):
        # The tail is the pattern's own Japanese text. Without this, an English line that
        # happens to open with a capital — "As you get older, you become more forgetful."
        # — parses as base A plus a very long tail, and lands in a connection table.
        raise ConnectionError_(f"{token!r} is not a connection: its tail is not Japanese.")
    return {
        "slot": forms[form],
        "form": form,
        "display": CONNECTION_BASES[base]["display"] + form + tail,
        "tail": tail,
    }


def parse_connection_line(raw: str) -> list[dict[str, str]]:
    """Parse one printed line, which may show alternatives: ``"Vまっぽい／Aっぽい"``.

    The book separates alternatives with a full-width slash on one line, so a line is a
    connection line only when *every* alternative on it parses. One half parsing is the
    signature of an ordinary sentence that happens to start with a letter.
    """
    parts = [part.strip() for part in re.split(r"[／/]", str(raw or "")) if part.strip()]
    if not parts:
        raise ConnectionError_("Empty connection line.")
    return [parse_connection(part) for part in parts]


def _looks_like_abbreviation(text: str) -> bool:
    """True when a tail starts with another base marker — two tokens joined by OCR."""
    return any(text.startswith(marker) for marker in ("na", "V", "A", "N", "普", "文"))


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


def entry_id(pack_id: str, entry_key: str, kind: str) -> str:
    """The 96-bit id an entry keeps for its whole life.

    Derived only from things that must never change: the pack's immutable namespace
    and the key frozen in ``entry-keys.json``. Not the headword, not the unit, not the
    printed order — correcting any of those must leave the learner's cards attached.
    """
    if not PACK_ID_PATTERN.fullmatch(pack_id or ""):
        raise ValueError(f"Invalid packId: {pack_id!r}")
    if not ENTRY_KEY_PATTERN.fullmatch(entry_key or ""):
        raise ValueError(f"Invalid entryKey: {entry_key!r}")
    if kind not in ENTRY_KINDS:
        raise ValueError(f"Invalid entry kind: {kind!r}")
    digest = hashlib.sha256(f"{pack_id}{US}{entry_key}".encode("utf-8")).hexdigest()[:24]
    return f"{kind[0]}_{digest}"


def source_ref(pack_id: str, entry_id_value: str) -> str:
    return f"lex:{pack_id}#{entry_id_value}"


def parse_source_ref(ref: str) -> tuple[str, str] | None:
    """``lex:<packId>#<entryId>`` → ``(packId, entryId)``, or ``None`` if malformed."""
    match = SOURCE_REF_PATTERN.fullmatch(str(ref or ""))
    return (match.group(1), match.group(2)) if match else None


def normalized_headword(text: str) -> str:
    """A search / duplicate-detection key. Deliberately *not* part of any identity.

    NFKC, wave-dash variants folded together, whitespace collapsed. Two entries that
    normalise the same are worth a human look; they are never merged automatically,
    because a hash that happens to change is not a migration.
    """
    folded = unicodedata.normalize("NFKC", str(text or ""))
    folded = _WAVE_DASH.sub("", folded)
    return " ".join(folded.split())


# ---------------------------------------------------------------------------
# Preparation
# ---------------------------------------------------------------------------


def publish_pack(directory: Path, files: dict[str, Any], *, revision: str) -> dict[str, Any]:
    """Write a pack and everything that describes it as one publish unit.

    Per-file ``os.replace`` only makes each file individually atomic, so an interrupted
    build could leave ``match-report.json`` describing one revision and ``pack.json``
    another — which is how the shipped grammar pack came to carry a report for a revision
    it no longer is. Everything is staged and verified first; the manifest is moved last,
    so a half-published directory is detectable rather than silently believed (§6.5).
    """
    import os
    import shutil
    import tempfile

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".publish-", dir=directory))
    try:
        digests = {}
        for name, payload in files.items():
            text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
            encoded = text.encode("utf-8")
            (staging / name).write_bytes(encoded)
            digests[name] = hashlib.sha256(encoded).hexdigest()
        manifest = {"contentRevision": revision, "files": digests,
                    "publishedAt": datetime.now(timezone.utc).isoformat()}
        # Build time lives here, never in the content hash: two runs over the same inputs
        # must produce the same revision (§6.5).
        (staging / "publish.json").write_bytes(
            (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

        for name in files:
            os.replace(staging / name, directory / name)
        os.replace(staging / "publish.json", directory / "publish.json")
        return manifest
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def prepare_pack(pack: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with ids, printed order, derived counts and ``contentRevision``.

    Existing valid ids are preserved. New ones come from ``entryKey``, so two machines
    assembling the same pack from the same registry agree without talking to each other.
    """
    if not isinstance(pack, dict):
        raise ValueError("Pack must be an object.")

    prepared = copy.deepcopy(pack)
    prepared["schemaVersion"] = SCHEMA_VERSION

    pack_id = str(prepared.get("packId") or "")
    if not PACK_ID_PATTERN.fullmatch(pack_id):
        raise ValueError(f"Invalid packId: {pack_id!r}")

    kind = str(prepared.get("kind") or "")
    if kind not in ENTRY_KINDS:
        raise ValueError(f"Pack kind must be one of {', '.join(ENTRY_KINDS)}, got {kind!r}.")

    _prepare_attribution(prepared)

    entries = prepared.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Pack must contain an entries array.")

    units = prepared.get("units")
    if not isinstance(units, list):
        raise ValueError("Pack must contain a units array.")

    # Printed order comes from the unit lists, which is where a human edits it. Deriving
    # it here rather than trusting a hand-written number keeps the two from disagreeing.
    order_of: dict[str, int] = {}
    position = 0
    for unit in units:
        if not isinstance(unit, dict):
            raise ValueError("Every unit must be an object.")
        unit.setdefault("title", "")
        for key in unit.get("entryIds") or []:
            position += 1
            order_of[str(key)] = position

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry {index} must be an object.")
        entry.setdefault("kind", kind)
        entry.setdefault("level", prepared.get("level"))

        entry_key = str(entry.get("entryKey") or "")
        if not ENTRY_KEY_PATTERN.fullmatch(entry_key):
            raise ValueError(f"Entry {index} has an invalid entryKey: {entry_key!r}")

        existing = entry.get("id")
        expected = entry_id(pack_id, entry_key, str(entry.get("kind")))
        if existing and not ENTRY_ID_PATTERN.fullmatch(str(existing)):
            raise ValueError(f"Invalid entry id: {existing!r}")
        if existing and str(existing) != expected:
            # An id that does not follow from its key means the key was reassigned or
            # the id was hand-edited. Either way the learner's cards now point somewhere
            # unrelated, and quietly rewriting it is how that becomes invisible.
            raise ValueError(
                f"Entry {entry_key} carries id {existing!r} but its key derives {expected!r}. "
                "Migrate it through idAliases rather than editing the id."
            )
        entry["id"] = expected

        entry.setdefault("headword", "")
        entry.setdefault("gloss", {})
        entry.setdefault("examples", [])
        entry.setdefault("cardTemplates", [])
        entry.setdefault("source", {})
        entry.setdefault("flags", [])
        entry.setdefault("idAliases", [])
        entry["order"] = order_of.get(entry["id"], order_of.get(entry_key, 0))

        if entry.get("kind") == "grammar":
            grammar = entry.setdefault("grammar", {})
            if isinstance(grammar, dict):
                grammar.setdefault("connection", [])
                grammar.setdefault("notes", "")
                grammar.setdefault("confusables", [])

        for example_index, example in enumerate(entry.get("examples") or []):
            if isinstance(example, dict):
                example.setdefault("exampleId", f"ex{example_index + 1}")
                # A reading with no accountable source is a reading the OCR invented, and
                # docs/PDF_OCR.md measured why: at this book's furigana size the model
                # does not read them, it makes them up. No reading is the better record.
                if str(example.get("readingSource") or "") not in READING_SOURCES or not example.get("reading"):
                    example.pop("reading", None)
                    example.pop("readingSource", None)

    # Entry ids referenced by a unit are written as entryKeys by the importer; resolve
    # them once here so everything downstream sees ids only.
    key_to_id = {str(entry.get("entryKey")): str(entry.get("id")) for entry in entries}
    for unit in units:
        unit["entryIds"] = [key_to_id.get(str(ref), str(ref)) for ref in unit.get("entryIds") or []]
        unit["entryCount"] = len(unit["entryIds"])

    entries.sort(key=lambda item: (int(item.get("order") or 0) or 10**9, str(item.get("entryKey"))))
    prepared["entryCount"] = len(entries)
    prepared["unitCount"] = len(units)
    prepared["cardCount"] = sum(len(entry.get("cardTemplates") or []) for entry in entries)
    prepared["contentRevision"] = ""
    prepared["contentRevision"] = content_revision(prepared)
    return prepared


def _prepare_attribution(pack: dict[str, Any]) -> None:
    """Fail on a rights claim the pack is not entitled to make.

    ADR-LEX-002 / LEXICON.md §8: a textbook pack is not redistributable, full stop.
    A missing or wrong flag is refused rather than corrected, because silently writing
    ``false`` over someone's ``true`` hides the fact that a pack was built believing the
    opposite — and the next person reads the corrected file, not the mistake.
    """
    attribution = pack.get("attribution")
    if not isinstance(attribution, dict):
        raise ValueError("Pack must carry an attribution object.")
    source_type = str(attribution.get("sourceType") or "")
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"attribution.sourceType must be one of {', '.join(SOURCE_TYPES)}.")
    if source_type == "textbook-ocr" and attribution.get("redistributable") is not False:
        raise ValueError(
            "A textbook-ocr pack must declare attribution.redistributable = false. "
            "Scanning a book does not change who owns it."
        )
    attribution.setdefault("redistributable", False)


def content_revision(pack: dict[str, Any]) -> str:
    """SHA-256 over the whole pack with ``contentRevision`` blanked.

    Everything a learner or an auditor sees participates: attribution, flags, card
    templates and order included. Nothing machine-local does, because nothing
    machine-local is in the file — which is what makes two machines agree.
    """
    payload = copy.deepcopy(pack)
    payload["contentRevision"] = ""
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def iter_entries(pack: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for entry in pack.get("entries") or []:
        if isinstance(entry, dict):
            yield entry


def entry_index(pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(entry.get("id")): entry for entry in iter_entries(pack)}


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def audit_pack(pack: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-serialisable quality report without mutating *pack*.

    Same shape as ``audit_exam`` and ``audit_manifest``: ``status`` / ``summary`` /
    ``issues``, so the loader refuses a broken pack through the code path it already has.
    """
    issues: list[dict[str, Any]] = []

    if pack.get("schemaVersion") not in {1, 2}:
        _issue(issues, "error", "schema.unsupported", "Supported schemaVersion values are 1 and 2.")
    pack_id = str(pack.get("packId") or "")
    if not PACK_ID_PATTERN.fullmatch(pack_id):
        _issue(issues, "error", "pack.id_invalid", "packId must match [A-Za-z0-9][A-Za-z0-9._-]{0,63}.")
    if not str(pack.get("title") or "").strip():
        _issue(issues, "error", "pack.title_missing", "A non-empty title is required.")
    if str(pack.get("level") or "") not in LEVELS:
        _issue(issues, "error", "pack.level_invalid", f"level must be one of {', '.join(LEVELS)}.")
    pack_kind = str(pack.get("kind") or "")
    if pack_kind not in ENTRY_KINDS:
        _issue(issues, "error", "pack.kind_invalid", f"kind must be one of {', '.join(ENTRY_KINDS)}.")

    _audit_attribution(pack, issues)
    _audit_dictionary_link(pack, issues)

    entries = pack.get("entries")
    if not isinstance(entries, list) or not entries:
        _issue(issues, "error", "pack.entries_missing", "A non-empty entries array is required.")
        entries = []

    known_ids: set[str] = set()
    seen_keys: set[str] = set()
    normalised: dict[str, list[str]] = {}

    for entry in entries:
        if not isinstance(entry, dict):
            _issue(issues, "error", "entry.not_object", "Entry must be an object.")
            continue
        ref = str(entry.get("id") or entry.get("entryKey") or "?")

        entry_key = str(entry.get("entryKey") or "")
        if not ENTRY_KEY_PATTERN.fullmatch(entry_key):
            _issue(issues, "error", "entry.key_invalid", "entryKey must look like e0001.", ref)
        elif entry_key in seen_keys:
            _issue(issues, "error", "entry.key_duplicate", f"entryKey {entry_key} appears twice.", ref)
        seen_keys.add(entry_key)

        entry_id_value = str(entry.get("id") or "")
        if not ENTRY_ID_PATTERN.fullmatch(entry_id_value):
            _issue(issues, "error", "entry.id_invalid", "id must look like g_<24 hex chars>.", ref)
        elif entry_id_value in known_ids:
            _issue(issues, "error", "entry.id_duplicate", "Duplicate entry id.", ref)
        elif pack_id and ENTRY_KEY_PATTERN.fullmatch(entry_key):
            expected = entry_id(pack_id, entry_key, str(entry.get("kind") or pack_kind or "grammar"))
            if entry_id_value != expected:
                _issue(
                    issues,
                    "error",
                    "entry.id_not_derived",
                    "id does not derive from packId + entryKey; it was hand-edited or the key moved.",
                    ref,
                )
        known_ids.add(entry_id_value)

        if str(entry.get("kind") or "") != pack_kind:
            _issue(issues, "error", "entry.kind_mismatch", f"Entry kind must equal the pack kind {pack_kind!r}.", ref)
        if str(entry.get("level") or "") not in LEVELS:
            _issue(issues, "error", "entry.level_invalid", "Entry level must be a JLPT level.", ref)

        headword = str(entry.get("headword") or "")
        if not headword.strip():
            _issue(issues, "error", "entry.headword_missing", "Entry headword is empty.", ref)
        _audit_markup(headword, issues, "entry", ref)
        normalised.setdefault(normalized_headword(headword), []).append(ref)

        _audit_gloss(entry, issues, ref)
        _audit_examples(entry, issues, ref)
        _audit_flags(entry, issues, ref)
        if str(entry.get("kind") or "") == "grammar":
            _audit_grammar(entry, issues, ref)
        else:
            _audit_word(entry, issues, ref)

    for key, refs in sorted(normalised.items()):
        if key and len(refs) > 1:
            _issue(
                issues,
                "warning",
                "entry.headword_duplicate",
                f"{len(refs)} entries normalise to {key!r}; confirm they are genuinely different items.",
                refs[0],
            )

    _audit_units(pack, entries, known_ids, issues)
    # Card templates reference other entries, so they are checked once every id is known.
    for entry in entries:
        if isinstance(entry, dict):
            _audit_cards(entry, pack_id, known_ids, issues)
            from lexicon_exercise import validate_spec
            seen_variants = set()
            for spec in entry.get("exerciseTemplates", []):
                try:
                    validate_spec(spec)
                    variant = spec.get("variantKey")
                    if not isinstance(variant, str) or not SLUG_PATTERN.fullmatch(variant) or variant in seen_variants:
                        raise ValueError("Exercise variants must have unique stable keys.")
                    seen_variants.add(variant)
                    from lexicon_exercise import review_state, review_content_hash
                    state = review_state(spec)
                    if state != "draft" and not spec.get("evidence") and not spec.get("review"):
                        raise ValueError("Checked or reviewed exercises require evidence.")
                    if state == "reviewed":
                        # A review that does not name its reviewer and the exact content it
                        # covers cannot be audited later, so it is not a review (LEX-04).
                        review = spec.get("review") if isinstance(spec.get("review"), dict) else {}
                        if not str(review.get("reviewer") or "").strip():
                            raise ValueError("Reviewed exercises must name their reviewer.")
                        if review.get("contentHash") != review_content_hash(spec):
                            raise ValueError("Review record does not cover the current content.")
                except (ValueError, KeyError, TypeError) as exc:
                    _issue(issues, "error", "exercise.invalid", str(exc), entry.get("id"))

    declared = pack.get("entryCount")
    if isinstance(declared, int) and not isinstance(declared, bool) and declared != len(entries):
        _issue(
            issues,
            "error",
            "pack.entry_count_mismatch",
            f"entryCount says {declared} but {len(entries)} entries are present.",
        )
    revision = str(pack.get("contentRevision") or "")
    if not SHA256_PATTERN.fullmatch(revision):
        _issue(issues, "error", "pack.revision_invalid", "contentRevision must be a lowercase SHA-256 digest.")
    elif revision != content_revision(pack):
        _issue(
            issues,
            "error",
            "pack.revision_stale",
            "contentRevision does not match the pack's content; re-run assemble instead of editing pack.json.",
        )

    severity_counts = Counter(issue["severity"] for issue in issues)
    code_counts = Counter(issue["code"] for issue in issues)
    status = "failed" if severity_counts["error"] else "needs_review" if severity_counts["warning"] else "passed"
    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": status,
        "summary": {
            "entries": len(entries),
            "units": len(pack.get("units") or []),
            "errors": severity_counts["error"],
            "warnings": severity_counts["warning"],
            "issueCounts": dict(sorted(code_counts.items())),
        },
        "issues": issues,
    }


def _audit_attribution(pack: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    attribution = pack.get("attribution")
    if not isinstance(attribution, dict):
        _issue(issues, "error", "pack.attribution_missing", "attribution is required.")
        return
    source_type = str(attribution.get("sourceType") or "")
    if source_type not in SOURCE_TYPES:
        _issue(issues, "error", "pack.source_type_invalid", f"Unknown sourceType {source_type!r}.")
    if source_type == "textbook-ocr":
        if attribution.get("redistributable") is not False:
            # LEXICON.md §8.2. The claim itself is the defect: a pack that says it may
            # be shared will eventually be shared.
            _issue(
                issues,
                "error",
                "pack.redistributable_claim",
                "A textbook-derived pack claims to be redistributable. It is not.",
            )
        if not str(attribution.get("sourceSha256") or "").strip():
            _issue(
                issues,
                "warning",
                "pack.source_hash_missing",
                "No sourceSha256: the pack cannot be tied back to the book it came from.",
            )
    if not str(attribution.get("publisher") or attribution.get("originalPublisher") or "").strip():
        _issue(issues, "warning", "pack.publisher_missing", "No publisher recorded for this source.")


def _audit_dictionary_link(pack: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    dictionary = pack.get("dictionary")
    if dictionary is None:
        return
    if not isinstance(dictionary, dict):
        _issue(issues, "error", "pack.dictionary_invalid", "dictionary must be an object when present.")
        return
    if dictionary.get("required") and not str(dictionary.get("name") or "").strip():
        _issue(issues, "error", "pack.dictionary_unnamed", "dictionary.required is set but no dictionary is named.")
    digest = str(dictionary.get("fileSha256") or "")
    if digest and not SHA256_PATTERN.fullmatch(digest):
        _issue(issues, "error", "pack.dictionary_hash_invalid", "dictionary.fileSha256 must be a SHA-256 digest.")


def _audit_units(
    pack: dict[str, Any],
    entries: list[Any],
    known_ids: set[str],
    issues: list[dict[str, Any]],
) -> None:
    units = pack.get("units")
    if not isinstance(units, list) or not units:
        _issue(issues, "error", "pack.units_missing", "A non-empty units array is required.")
        return

    seen_unit_ids: set[str] = set()
    membership: dict[str, int] = {}
    for unit in units:
        if not isinstance(unit, dict):
            _issue(issues, "error", "unit.not_object", "Unit must be an object.")
            continue
        unit_id = str(unit.get("unitId") or "")
        if not SLUG_PATTERN.fullmatch(unit_id):
            _issue(issues, "error", "unit.id_invalid", "unitId must match [a-z][a-z0-9-]{0,63}.", unit_id or "?")
        if unit_id in seen_unit_ids:
            _issue(issues, "error", "unit.id_duplicate", "Duplicate unitId.", unit_id)
        seen_unit_ids.add(unit_id)
        if not str(unit.get("label") or "").strip():
            _issue(issues, "warning", "unit.label_missing", "Unit has no printed label.", unit_id)

        entry_ids = unit.get("entryIds")
        if not isinstance(entry_ids, list) or not entry_ids:
            _issue(issues, "error", "unit.entries_missing", "A unit must list at least one entry.", unit_id)
            continue
        for reference in entry_ids:
            key = str(reference)
            if key not in known_ids:
                _issue(issues, "error", "unit.entry_unknown", f"entryIds names {key!r}, which is not in this pack.", unit_id)
            membership[key] = membership.get(key, 0) + 1

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_id_value = str(entry.get("id") or "")
        count = membership.get(entry_id_value, 0)
        if count == 0:
            # An entry in no unit is unreachable: the browse view walks units, so it
            # would be in the pack, counted, and invisible.
            _issue(issues, "error", "entry.unit_missing", "Entry belongs to no unit.", entry_id_value)
        elif count > 1:
            _issue(issues, "error", "entry.unit_duplicate", f"Entry appears in {count} units.", entry_id_value)


def _audit_gloss(entry: dict[str, Any], issues: list[dict[str, Any]], ref: str) -> None:
    gloss = entry.get("gloss")
    if not isinstance(gloss, dict):
        _issue(issues, "error", "entry.gloss_invalid", "gloss must be an object keyed by language.", ref)
        return
    unknown = sorted(set(gloss) - set(GLOSS_LANGUAGES))
    if unknown:
        _issue(issues, "error", "entry.gloss_language_unknown", f"Unknown gloss languages: {unknown}.", ref)
    for language, text in gloss.items():
        if not isinstance(text, str):
            _issue(issues, "error", "entry.gloss_not_text", f"gloss.{language} must be a string.", ref)
            continue
        _audit_markup(text, issues, "entry", ref)
    if str(gloss.get("zh") or "").strip():
        return
    # The interface is Simplified Chinese, so an entry a learner cannot read anything
    # about in Chinese is not a learnable card — that is the error. A missing gloss on an
    # entry whose examples *are* translated is a different, smaller problem: this book
    # prints a per-item gloss only in the side box, and only for some items, so demanding
    # one for all of them would block most of a correctly-read pack.
    if any(
        str(example.get("zh") or "").strip()
        for example in entry.get("examples") or []
        if isinstance(example, dict)
    ):
        _issue(issues, "warning", "entry.gloss_zh_missing", "No Chinese gloss for the entry itself.", ref)
    else:
        _issue(
            issues,
            "error",
            "entry.chinese_missing",
            "Neither the entry nor any of its examples carries Chinese; nothing here is readable.",
            ref,
        )


def _audit_examples(entry: dict[str, Any], issues: list[dict[str, Any]], ref: str) -> None:
    examples = entry.get("examples")
    if not isinstance(examples, list):
        _issue(issues, "error", "entry.examples_invalid", "examples must be an array.", ref)
        return
    if not examples:
        _issue(issues, "warning", "entry.examples_missing", "No example sentence.", ref)
    seen: set[str] = set()
    for example in examples:
        if not isinstance(example, dict):
            _issue(issues, "error", "example.not_object", "Example must be an object.", ref)
            continue
        example_id = str(example.get("exampleId") or "")
        if not SLUG_PATTERN.fullmatch(example_id):
            _issue(issues, "error", "example.id_invalid", "exampleId must match [a-z][a-z0-9-]{0,63}.", ref)
        if example_id in seen:
            _issue(issues, "error", "example.id_duplicate", f"Duplicate exampleId {example_id!r}.", ref)
        seen.add(example_id)

        japanese = str(example.get("ja") or "")
        if not japanese.strip():
            _issue(issues, "error", "example.ja_missing", f"Example {example_id} has no Japanese text.", ref)
        for field in ("ja", "zh", "en", "ko", "paraphrase"):
            _audit_markup(str(example.get(field) or ""), issues, "example", ref)

        reading = str(example.get("reading") or "")
        if reading:
            source = str(example.get("readingSource") or "")
            if source not in READING_SOURCES:
                # LEXICON.md 判断二: a reading with no accountable origin is a reading the
                # OCR invented, and an invented reading is worse than none at all.
                _issue(
                    issues,
                    "error",
                    "example.reading_unsourced",
                    f"Example {example_id} has a reading but readingSource is {source!r}; "
                    "it must be 'dictionary' or 'manual'.",
                    ref,
                )


def _audit_flags(entry: dict[str, Any], issues: list[dict[str, Any]], ref: str) -> None:
    flags = entry.get("flags")
    if not isinstance(flags, list):
        _issue(issues, "error", "entry.flags_invalid", "flags must be an array.", ref)
        return
    for flag in flags:
        severity = str(flag.get("severity") or "") if isinstance(flag, dict) else ""
        if severity not in {"warning", "info"}:
            # An entry that knows it is broken must not ship inside a pack that says it
            # passed. Errors are resolved in pages/, not carried along as a label.
            _issue(
                issues,
                "error",
                "entry.flag_severity_invalid",
                "Entry flags may only be 'warning' or 'info'; an error-level entry must not ship.",
                ref,
            )


def _audit_grammar(entry: dict[str, Any], issues: list[dict[str, Any]], ref: str) -> None:
    grammar = entry.get("grammar")
    if not isinstance(grammar, dict):
        _issue(issues, "error", "entry.grammar_missing", "A grammar entry needs a grammar object.", ref)
        return
    connection = grammar.get("connection")
    if not isinstance(connection, list) or not connection:
        _issue(issues, "error", "grammar.connection_missing", "No connection recorded for this pattern.", ref)
        connection = []
    for item in connection:
        if not isinstance(item, dict):
            _issue(issues, "error", "grammar.connection_not_object", "A connection must be an object.", ref)
            continue
        slot = str(item.get("slot") or "")
        known_slots = {base["slot"] for base in CONNECTION_BASES.values()} | {
            slot_name for forms in CONNECTION_FORMS.values() for slot_name in forms.values()
        }
        if slot not in known_slots:
            _issue(issues, "error", "grammar.connection_slot_unknown", f"Unknown connection slot {slot!r}.", ref)
        if not str(item.get("display") or "").strip():
            _issue(issues, "error", "grammar.connection_display_missing", "A connection needs a display form.", ref)
    _audit_markup(str(grammar.get("notes") or ""), issues, "grammar", ref)


def _audit_word(entry: dict[str, Any], issues: list[dict[str, Any]], ref: str) -> None:
    snapshot = entry.get("snapshot")
    if snapshot is not None and not isinstance(snapshot, dict):
        _issue(issues, "error", "word.snapshot_invalid", "snapshot must be an object when present.", ref)
    dict_ref = entry.get("dictRef")
    if dict_ref is None:
        _issue(
            issues,
            "warning",
            "word.dict_ref_missing",
            "No dictionary reference: readings and senses cannot be verified.",
            ref,
        )
        return
    if not isinstance(dict_ref, dict):
        _issue(issues, "error", "word.dict_ref_invalid", "dictRef must be an object.", ref)
        return
    ent_seq = dict_ref.get("entSeq")
    if isinstance(ent_seq, bool) or not isinstance(ent_seq, int):
        _issue(issues, "error", "word.ent_seq_invalid", "dictRef.entSeq must be an integer.", ref)


def _audit_cards(
    entry: dict[str, Any],
    pack_id: str,
    known_ids: set[str],
    issues: list[dict[str, Any]],
) -> None:
    ref = str(entry.get("id") or entry.get("entryKey") or "?")
    templates = entry.get("cardTemplates")
    if not isinstance(templates, list):
        _issue(issues, "error", "entry.cards_invalid", "cardTemplates must be an array.", ref)
        return
    if not templates:
        _issue(issues, "warning", "entry.cards_missing", "No card template: this entry cannot be studied.", ref)

    example_ids = {
        str(example.get("exampleId"))
        for example in entry.get("examples") or []
        if isinstance(example, dict)
    }
    seen: set[tuple[str, str]] = set()

    for template in templates:
        if not isinstance(template, dict):
            _issue(issues, "error", "card.not_object", "A card template must be an object.", ref)
            continue
        prompt_type = str(template.get("promptType") or "")
        variant_key = str(template.get("variantKey") or "")
        if prompt_type not in PROMPT_TYPES:
            _issue(issues, "error", "card.prompt_type_invalid", f"Unknown promptType {prompt_type!r}.", ref)
        if not SLUG_PATTERN.fullmatch(variant_key):
            _issue(issues, "error", "card.variant_key_invalid", "variantKey must match [a-z][a-z0-9-]{0,63}.", ref)
        identity = (prompt_type, variant_key)
        if identity in seen:
            # (sourceRef, promptType, variantKey) is the card's identity in the learner's
            # database. Two templates sharing it would be one card with two faces.
            _issue(
                issues,
                "error",
                "card.identity_duplicate",
                f"Two templates share promptType {prompt_type!r} and variantKey {variant_key!r}.",
                ref,
            )
        seen.add(identity)

        example_id = template.get("exampleId")
        if example_id is not None and str(example_id) not in example_ids:
            _issue(issues, "error", "card.example_unknown", f"exampleId {example_id!r} is not on this entry.", ref)

        if prompt_type == "cloze":
            marked = str(template.get("markedJa") or "")
            if not marked.strip():
                _issue(issues, "error", "card.cloze_text_missing", "A cloze card needs markedJa.", ref)
            elif marked.count(_CLOZE_OPEN) != marked.count(_CLOZE_CLOSE) or _CLOZE_OPEN not in marked:
                _issue(
                    issues,
                    "error",
                    "card.cloze_unbalanced",
                    "markedJa needs at least one balanced ⟦…⟧ pair marking the blank.",
                    ref,
                )
            _audit_markup(marked, issues, "card", ref)

        if prompt_type == "usage":
            _audit_usage_card(template, entry, pack_id, known_ids, issues, ref)


def _audit_usage_card(
    template: dict[str, Any],
    entry: dict[str, Any],
    pack_id: str,
    known_ids: set[str],
    issues: list[dict[str, Any]],
    ref: str,
) -> None:
    """A usage card grades a choice, so every wrong choice needs a reviewed reason.

    LEXICON.md §9: ``confusables`` can supply candidates but cannot prove why one is
    wrong. Without the reasons the card can mark a learner wrong and say nothing, which
    is the exam-key failure in a different costume.
    """
    choices = template.get("choiceRefs")
    if not isinstance(choices, list) or len(choices) < 2:
        _issue(issues, "error", "card.usage_choices_missing", "A usage card needs at least two choiceRefs.", ref)
        return
    answer = str(template.get("answerRef") or "")
    if answer not in {str(choice) for choice in choices}:
        _issue(issues, "error", "card.usage_answer_unlisted", "answerRef is not one of the choices.", ref)

    rationales = {
        str(item.get("choiceRef")): str(item.get("reason") or "")
        for item in template.get("rationales") or []
        if isinstance(item, dict)
    }
    for choice in choices:
        reference = str(choice)
        if reference != "self":
            resolved = parse_source_ref(reference)
            if resolved is None:
                _issue(issues, "error", "card.usage_choice_invalid", f"choiceRef {reference!r} is malformed.", ref)
                continue
            other_pack, other_entry = resolved
            if other_pack == pack_id and other_entry not in known_ids:
                _issue(issues, "error", "card.usage_choice_unknown", f"choiceRef {reference!r} is not in this pack.", ref)
        if reference != answer and not rationales.get(reference, "").strip():
            _issue(
                issues,
                "error",
                "card.usage_rationale_missing",
                f"Wrong choice {reference!r} has no reviewed reason.",
                ref,
            )


def _audit_markup(text: str, issues: list[dict[str, Any]], scope: str, ref: str) -> None:
    if text.count(_RUBY_OPEN) != text.count(_RUBY_CLOSE):
        _issue(issues, "error", f"{scope}.ruby_unbalanced", "Unbalanced 《》 furigana markup.", ref)
    if text.count(_SLOT_OPEN) != text.count(_SLOT_CLOSE):
        _issue(issues, "error", f"{scope}.slot_unbalanced", "Unbalanced 【】 connection markup.", ref)
    if text.count(_CLOZE_OPEN) != text.count(_CLOZE_CLOSE):
        _issue(issues, "error", f"{scope}.cloze_unbalanced", "Unbalanced ⟦⟧ blank markup.", ref)
    if text.count(_UNDERLINE_OPEN) != text.count(_UNDERLINE_CLOSE):
        _issue(issues, "error", f"{scope}.underline_unbalanced", "Unbalanced <u> markup.", ref)
    stray = _STRAY_TAG.search(text)
    if stray:
        _issue(issues, "error", f"{scope}.stray_markup", f"Only <u>…</u> is allowed; found {stray.group(0)!r}.", ref)
    if "〓" in text:
        _issue(issues, "warning", f"{scope}.illegible_glyph", "Contains 〓, an unread character.", ref)


def _issue(
    issues: list[dict[str, Any]],
    severity: str,
    code: str,
    message: str,
    ref: str | None = None,
) -> None:
    issue: dict[str, Any] = {"severity": severity, "code": code, "message": message}
    if ref is not None:
        issue["ref"] = ref
    issues.append(issue)


# ---------------------------------------------------------------------------
# Card generation
# ---------------------------------------------------------------------------


def default_card_templates(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """The templates an entry gets when the importer is not told otherwise.

    Grammar leads with ``cloze``, not ``recall``: reciting 「〜てたまらない＝……得受不了」
    is not the same skill as choosing the right form inside a sentence, and the 文法 part
    of the exam tests the second one. ``usage`` is never generated here — it needs
    reviewed reasons for each wrong choice, and generating one without them produces a
    card that can mark a learner wrong and not say why.
    """
    templates: list[dict[str, Any]] = [{"variantKey": "default", "promptType": "recall"}]
    if str(entry.get("kind")) != "grammar":
        return templates
    for example in entry.get("examples") or []:
        if not isinstance(example, dict):
            continue
        marked = str(example.get("markedJa") or "")
        if _CLOZE_OPEN not in marked:
            continue
        example_id = str(example.get("exampleId") or "")
        if not SLUG_PATTERN.fullmatch(example_id):
            continue
        templates.append(
            {
                "variantKey": f"cloze-{example_id}",
                "promptType": "cloze",
                "exampleId": example_id,
                "markedJa": marked,
            }
        )
    return templates
