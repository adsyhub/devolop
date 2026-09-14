"""What may leave this machine, and what may not.

Two rules, one module, because they are the same rule read from both ends:

* Content derived from a copyrighted textbook never enters a release artifact. OCR
  changes the carrier, not the rights — ``dist/N2语法  新日语能力考试考前对策_12684449.pdf``
  is ISBN 978-7-5100-2795-6 with its copyright page intact, and a pack built from it is
  that book in another format.
* Content taken from an open dictionary *may* be redistributed, and therefore *must*
  carry its attribution and its licence version. A permissive licence is a set of
  obligations, not an absence of them. (The dictionary layer arrives in Phase B; the
  rule it will have to satisfy is written down in ADR-LEX-002, not stubbed here — a
  check with no caller reads as protection while protecting nothing.)

``release_readiness.py`` calls this, and so must any future packager whose inputs can
reach ``lexicon/``. It is deliberately not wired into ``make_zip.py`` or
``repack_offline_bundle.py``: those take one course directory and cannot see a pack, and
a guard on a path that does not exist reads as protection while protecting nothing.

The verdicts here describe this project's publishing and version-control boundary. They
are not a legal opinion, and "not redistributable" is not the same claim as "not usable
by the person who owns the book".
"""

from __future__ import annotations

import re
from typing import Any, Iterable

POLICY_VERSION = 1

#: Files inside a pack directory that carry textbook text, the transcribed table of
#: contents, or a mapping that reveals which items the book selected. None of them may
#: be committed or shipped; ``pack-meta.json``, ``source.pdf.sha256`` and
#: ``entry-keys.json`` may, because they describe identity rather than content.
FORBIDDEN_PACK_FILES = ("pack.json", "units.txt", "match-report.json", "match-resolutions.json")
FORBIDDEN_PACK_DIRS = ("pages",)

#: ``entry-keys.json`` is the one pack file that is committed, because rebuilding a pack
#: on another machine has to produce the same identities. It may therefore contain only
#: identity: a key, where it was found, and how it was migrated. A headword would put the
#: book's own selection of items into version control, and an ``entSeq`` would do the same
#: for the dictionary matching that selection.
REGISTRY_ALLOWED_ENTRY_FIELDS = frozenset({"entryKey", "sourceAnchor", "retired", "aliasOf"})
REGISTRY_ALLOWED_TOP_FIELDS = frozenset({"schemaVersion", "packId", "nextKey", "entries"})

_LEXICON_SEGMENT = re.compile(r"(^|[\\/])lexicon[\\/]")


def describe_pack_distribution(meta: dict[str, Any]) -> dict[str, Any]:
    """Decide whether one pack may be redistributed, and say why.

    Takes ``pack-meta.json`` or a whole ``pack.json`` — both carry ``attribution``.
    A textbook pack is refused even when it claims otherwise; the claim is reported as
    the defect rather than quietly corrected, so the pack that made it can be found.
    """
    attribution = meta.get("attribution") if isinstance(meta, dict) else None
    if not isinstance(attribution, dict):
        return {
            "packId": str((meta or {}).get("packId") or ""),
            "redistributable": False,
            "reasons": ["No attribution block: provenance is unknown, so nothing may be published."],
        }

    source_type = str(attribution.get("sourceType") or "")
    claimed = attribution.get("redistributable")
    reasons: list[str] = []

    if source_type == "textbook-ocr":
        redistributable = False
        reasons.append(
            "Derived from a copyrighted textbook by OCR. Changing the carrier does not "
            "change who owns the text."
        )
        if claimed is not False:
            reasons.append(
                f"attribution.redistributable is {claimed!r}; a textbook pack must declare false."
            )
    elif source_type == "open-dictionary":
        redistributable = bool(claimed)
        missing = [field for field in ("licence", "attribution") if not str(attribution.get(field) or "").strip()]
        if missing:
            redistributable = False
            reasons.append(f"Open-dictionary content is missing required fields: {', '.join(missing)}.")
        if redistributable:
            reasons.append("Open dictionary data: publishable while attribution and ShareAlike are preserved.")
    elif source_type == "original":
        redistributable = bool(claimed)
        if not redistributable:
            reasons.append("Original content, but not marked redistributable.")
    else:
        redistributable = False
        reasons.append(f"Unknown sourceType {source_type!r}; the default is to publish nothing.")

    return {
        "packId": str(meta.get("packId") or meta.get("slug") or ""),
        "sourceType": source_type,
        "redistributable": redistributable,
        "reasons": reasons,
    }


def forbidden_release_paths(paths: Iterable[str]) -> list[str]:
    """Return the entries of a release artifact that must not be in it.

    *paths* is a listing — ``ZipFile.namelist()``, or the relative paths under a staging
    directory. Matching is on the path shape, so it works before anything is unpacked.
    """
    offenders: list[str] = []
    for raw in paths:
        text = str(raw).replace("\\", "/")
        if not _LEXICON_SEGMENT.search("/" + text):
            continue
        name = text.rsplit("/", 1)[-1]
        segments = text.split("/")
        if name in FORBIDDEN_PACK_FILES or any(segment in FORBIDDEN_PACK_DIRS for segment in segments):
            offenders.append(text)
    return sorted(offenders)


def audit_release_artifact(paths: Iterable[str]) -> dict[str, Any]:
    """A check row in the shape ``release_readiness.add_check`` consumes."""
    offenders = forbidden_release_paths(paths)
    return {
        "policyVersion": POLICY_VERSION,
        "passed": not offenders,
        "offenders": offenders,
        "detail": "no textbook-derived lexicon content"
        if not offenders
        else f"{len(offenders)} forbidden entries: {', '.join(offenders[:5])}",
    }


def audit_entry_key_registry(registry: Any) -> dict[str, Any]:
    """Check that ``entry-keys.json`` carries identity and nothing else.

    Run before the file is written and again by the test suite, so a field added for
    debugging convenience cannot reach a commit. The failure this prevents is quiet:
    ``"headwordHint"`` looks helpful in a diff right up until the diff is public.
    """
    if not isinstance(registry, dict):
        return {"policyVersion": POLICY_VERSION, "passed": False, "offenders": ["<not an object>"]}
    offenders = sorted(str(field) for field in set(registry) - REGISTRY_ALLOWED_TOP_FIELDS)
    entries = registry.get("entries")
    if not isinstance(entries, list):
        offenders.append("entries (must be an array)")
        entries = []
    for item in entries:
        if not isinstance(item, dict):
            offenders.append("<entry is not an object>")
            continue
        for field in sorted(set(item) - REGISTRY_ALLOWED_ENTRY_FIELDS):
            offenders.append(f"entries[].{field}")
    offenders = sorted(set(offenders))
    return {
        "policyVersion": POLICY_VERSION,
        "passed": not offenders,
        "offenders": offenders,
        "detail": "identity only" if not offenders else f"content fields present: {', '.join(offenders)}",
    }
