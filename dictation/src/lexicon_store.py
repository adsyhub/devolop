"""Lexicon pack storage and its read-only HTTP API.

``LexiconStore``      reads ``lexicon/<slug>/pack.json`` off disk and audits it, the way
                      ``ExamStore`` reads ``exams/<slug>/exam.json``.
``LexiconApiMixin``   the ``/api/lexicon*`` routes, mixed into the request handler beside
                      ``ExamApiMixin`` and ``LearningApiMixin``.

Besides browse and read, the mixin now exposes study-plan lifecycle and daily delivery.
The durable card/SRS state stays in ``LearningStore`` so it shares one SQLite connection,
one lock and one backup story with the rest of the learner's data.

Fail-closed, again
------------------
A pack whose audit reports errors is not served (HTTP 422), for the reason the exam bank
refuses a broken paper: a grammar table missing a connection branch teaches a rule that
is wrong in exactly the cases the exam asks about, and the learner has no way to notice.
A pack with *warnings* is served with its report attached, so the interface can say what
is unverified without hiding the entry.

What the browse API deliberately does not do
--------------------------------------------
It does not merge packs. A learner browsing N2 grammar is inside one book's sequence, and
the book's order is the pedagogy. Cross-pack views are a search problem, and search needs
the dictionary layer.
"""

from __future__ import annotations

import json
import re
import copy
import threading
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import SplitResult, parse_qs, unquote

from distribution_policy import describe_pack_distribution
from lexicon_schema import (
    LEVELS,
    PACK_ID_PATTERN,
    audit_pack,
    entry_index,
    iter_entries,
    normalized_headword,
    source_ref,
)


class PackQualityError(ValueError):
    """An existing source is structurally unsafe to serve for learning."""

#: A browse request can ask for one unit at a time; the cap is a guard on the response
#: size, not a product decision — 48 units of 4 entries is the whole book.
MAX_SEARCH_RESULTS = 100


class LexiconStore:
    """Lists and loads packs from a ``lexicon/`` directory.

    Layout mirrors ``exams/``::

        lexicon/
          N2-grammar-soumatome/
            pack.json          <- the only file the page needs
            pack-meta.json     <- book, ISBN, rights declaration (hand-written)
            entry-keys.json    <- frozen identities (the one committed file)
            units.txt          <- the printed 目次, transcribed by a person
            pages/p0018.json … <- extraction source of truth, hand-editable
    """

    def __init__(self, lexicon_root: Path) -> None:
        self.root = Path(lexicon_root)
        self._cache = {}
        self._lock = threading.RLock()

    # -- listing ------------------------------------------------------------

    def list_packs(self) -> list[dict[str, Any]]:
        if not self.root.is_dir():
            return []
        summaries: list[dict[str, Any]] = []
        for directory in sorted(self.root.iterdir()):
            if not directory.is_dir() or not PACK_ID_PATTERN.fullmatch(directory.name):
                continue
            try:
                from studio_artifacts import resolve_lexicon_pack_path
                path = resolve_lexicon_pack_path(directory)
            except Exception:
                path = directory / "pack.json"
            if not path or not path.is_file():
                continue
            try:
                pack = self._load_json(path)
            except Exception as exc:  # noqa: BLE001 - one broken pack must not hide the rest
                summaries.append({"slug": directory.name, "title": directory.name, "broken": True, "error": str(exc)})
                continue
            report = audit_pack(pack)
            summaries.append(
                {
                    "slug": directory.name,
                    "packId": pack.get("packId"),
                    "kind": pack.get("kind"),
                    "level": pack.get("level"),
                    "title": pack.get("title"),
                    "entryCount": pack.get("entryCount"),
                    "unitCount": pack.get("unitCount"),
                    "contentRevision": pack.get("contentRevision"),
                    "units": [
                        {
                            "unitId": unit.get("unitId"),
                            "label": unit.get("label"),
                            "title": unit.get("title"),
                            "entryCount": len(unit.get("entryIds") or []),
                        }
                        for unit in pack.get("units") or []
                        if isinstance(unit, dict)
                    ],
                    "distribution": describe_pack_distribution(pack),
                    "quality": {"status": report["status"], **report["summary"]},
                    "broken": bool(report["summary"]["errors"]),
                }
            )
        return summaries

    # -- one pack -----------------------------------------------------------

    def get_pack(self, slug: str) -> dict[str, Any] | None:
        path = self.pack_path(slug)
        if path is None:
            return None
        stamp = (path.stat().st_mtime_ns, path.stat().st_size)
        with self._lock:
            cached = self._cache.get(slug)
            if cached and cached[0] == stamp:
                return copy.deepcopy(cached[1])
        pack = self._load_json(path)
        report = audit_pack(pack)
        pack["quality"] = {
            "status": report["status"],
            "blocked": bool(report["summary"]["errors"]),
            **report["summary"],
        }
        pack["slug"] = slug
        pack["distribution"] = describe_pack_distribution(pack)
        pack["publication"] = self._publication(path.parent, pack)
        with self._lock:
            self._cache[slug] = (stamp, copy.deepcopy(pack))
        return pack

    @staticmethod
    def _publication(directory: Path, pack: dict[str, Any]) -> dict[str, Any]:
        """Whether the reports beside a pack describe the pack that is actually there.

        Reports used to be stamped before the last build step, so a pack could ship with
        a `match-report.json` for a revision it no longer was. The publish manifest makes
        that disagreement visible instead of leaving it to be believed (LEX-14, §6.5).
        """
        revision = str(pack.get("contentRevision") or "")
        result: dict[str, Any] = {"contentRevision": revision, "manifest": None, "staleReports": []}
        manifest_path = directory / "publish.json"
        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                result["manifest"] = {"contentRevision": manifest.get("contentRevision"),
                                      "publishedAt": manifest.get("publishedAt")}
                if str(manifest.get("contentRevision") or "") != revision:
                    result["staleReports"].append("publish.json")
            except (OSError, ValueError):
                result["staleReports"].append("publish.json")
        for name in ("match-report.json", "quality-report.json"):
            report_path = directory / name
            if not report_path.is_file():
                continue
            try:
                recorded = str(json.loads(report_path.read_text(encoding="utf-8")).get("contentRevision") or "")
            except (OSError, ValueError):
                result["staleReports"].append(name)
                continue
            # A report with no revision at all predates the contract; one with a
            # different revision describes a build this is not.
            if recorded and recorded != revision:
                result["staleReports"].append(name)
            elif not recorded:
                result["staleReports"].append(name + " (未记录 revision)")
        result["reportsCurrent"] = not result["staleReports"]
        return result

    def find_pack(self, identifier: str) -> dict[str, Any] | None:
        """Resolve either a directory slug or the pack's stable packId."""
        direct = self.get_pack(identifier)
        if direct is not None:
            return direct
        for summary in self.list_packs():
            if not summary.get("broken") and summary.get("packId") == identifier:
                return self.get_pack(str(summary["slug"]))
        return None

    def get_entry(self, slug: str, entry_id: str) -> dict[str, Any] | None:
        pack = self.get_pack(slug)
        if pack is None:
            return None
        if pack["quality"].get("blocked"):
            raise PackQualityError("内容包未通过质量审计。")
        entry = entry_index(pack).get(entry_id)
        if entry is None:
            return None
        unit = next(
            (
                item
                for item in pack.get("units") or []
                if isinstance(item, dict) and entry_id in (item.get("entryIds") or [])
            ),
            None,
        )
        return {
            "entry": entry,
            "packId": pack.get("packId"),
            "packTitle": pack.get("title"),
            "packSlug": slug,
            "contentRevision": pack.get("contentRevision"),
            "unit": {key: unit.get(key) for key in ("unitId", "label", "title")} if unit else None,
        }

    def search(
        self,
        query: str,
        *,
        kind: str = "",
        level: str = "",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Match packs' own entries by headword and gloss.

        Phase A search is pack-local and substring-based on purpose: it is the browse
        view's filter box, not the dictionary lookup. The lookup that de-inflects a word
        and asks JMdict needs the dictionary layer, and a search box that answers half a
        question without saying so is worse than one that says what it covers.
        """
        needle = normalized_headword(query)
        if not needle:
            return []
        results: list[dict[str, Any]] = []
        for summary in self.list_packs():
            if summary.get("broken"):
                continue
            if kind and summary.get("kind") != kind:
                continue
            if level and summary.get("level") != level:
                continue
            pack = self.get_pack(str(summary["slug"]))
            if pack is None or pack["quality"].get("blocked"):
                continue
            for entry in iter_entries(pack):
                haystacks = [normalized_headword(str(entry.get("headword") or ""))]
                haystacks.extend(
                    normalized_headword(str(value)) for value in (entry.get("gloss") or {}).values()
                )
                if not any(needle in text for text in haystacks if text):
                    continue
                results.append(
                    {
                        "id": entry.get("id"),
                        "sourceRef": source_ref(str(pack.get("packId")), str(entry.get("id"))),
                        "packSlug": summary["slug"],
                        "packTitle": pack.get("title"),
                        "kind": entry.get("kind"),
                        "level": entry.get("level"),
                        "headword": entry.get("headword"),
                        "gloss": entry.get("gloss"),
                        "unitId": entry.get("unitId"),
                    }
                )
                if len(results) >= min(int(limit or 20), MAX_SEARCH_RESULTS):
                    return results
        return results

    def pack_path(self, slug: str) -> Path | None:
        """Resolve ``slug`` to its ``pack.json``, refusing anything that escapes the root.

        ``PACK_ID_PATTERN`` already excludes ``/``, ``\\`` and ``..``; the resolved path
        is then checked to be inside the root as well, so a future loosening of the
        pattern cannot become a traversal.
        """
        if not PACK_ID_PATTERN.fullmatch(slug or ""):
            return None
        folder = (self.root / slug).resolve()
        try:
            folder.relative_to(self.root.resolve())
        except ValueError:
            return None
        if not folder.is_dir():
            return None
        try:
            from studio_artifacts import resolve_lexicon_pack_path

            candidate = resolve_lexicon_pack_path(folder)
            if candidate and candidate.is_file():
                return candidate
        except Exception:
            pass
        candidate = folder / "pack.json"
        return candidate if candidate.is_file() else None

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"{path.name} must contain a JSON object.")
        return data


# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------


class LexiconApiMixin:
    """``/api/lexicon*`` routing.

    Behind the same ``SecurityContext`` gate as everything else on this server: loopback
    Host, session token on every call including reads, Origin plus Fetch Metadata on
    writes. Pack content is derived from a copyrighted book, so "it is only a read" is
    not a reason to leave it open to a rebound origin.
    """

    lexicon_store: LexiconStore
    store: Any

    @staticmethod
    def _slug_from(path: str, prefix: str, suffix: str = "") -> str | None:
        if not path.startswith(prefix):
            return None
        rest = path[len(prefix) :]
        if suffix:
            if not rest.endswith(suffix):
                return None
            rest = rest[: -len(suffix)]
        return unquote(rest) if rest and "/" not in rest else None

    def handle_lexicon_get(self, parsed: SplitResult) -> bool:
        path = parsed.path

        if path == "/api/lexicon/packs":
            self.send_learning_json({"packs": self.lexicon_store.list_packs()})
            return True

        if path == "/api/lexicon/search":
            params = parse_qs(parsed.query)
            query = (params.get("q") or [""])[0]
            kind = (params.get("kind") or [""])[0]
            level = (params.get("level") or [""])[0]
            if level and level not in LEVELS:
                self.send_learning_json({"error": "unknown level"}, HTTPStatus.BAD_REQUEST)
                return True
            try:
                limit = int((params.get("limit") or ["20"])[0])
            except ValueError:
                limit = 20
            results = self.lexicon_store.search(query, kind=kind, level=level, limit=limit)
            self.send_learning_json(
                {
                    "results": results,
                    "query": query,
                    # The offline story has to be stated, not implied. Phase A searches
                    # installed packs only; a learner typing a word that is in JMdict but
                    # not in a pack must be told why nothing came back.
                    "scope": "packs",
                    "dictionaryAvailable": False,
                }
            )
            return True

        slug = self._slug_from(path, "/api/lexicon/packs/")
        if slug is not None:
            return self._send_pack(slug)

        if path.startswith("/api/lexicon/entries/"):
            rest = unquote(path[len("/api/lexicon/entries/") :])
            if rest.count("/") != 1:
                self.send_learning_json({"error": "entry reference must be <slug>/<entryId>"}, HTTPStatus.BAD_REQUEST)
                return True
            pack_slug, entry_id = rest.split("/", 1)
            try:
                found = self.lexicon_store.get_entry(pack_slug, entry_id)
            except PackQualityError as exc:
                self.send_learning_json({"error": str(exc)}, HTTPStatus.UNPROCESSABLE_ENTITY)
                return True
            except Exception as exc:  # noqa: BLE001
                self.send_learning_json({"error": f"pack could not be read: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
                return True
            if found is None:
                self.send_learning_json({"error": "entry not found"}, HTTPStatus.NOT_FOUND)
                return True
            self.send_learning_json(found)
            return True

        return False

    def handle_deck_get(self, parsed: SplitResult) -> bool:
        if parsed.path == "/api/decks":
            self.send_learning_json({"decks": self.store.list_decks()})
            return True
        deck_id = self._deck_id(parsed.path)
        if deck_id is None:
            return False
        try:
            deck = self.store.get_deck(deck_id)
        except KeyError:
            self.send_learning_json({"error": "deck not found"}, HTTPStatus.NOT_FOUND)
            return True
        self.send_learning_json({"deck": deck})
        return True

    def handle_deck_post(self, parsed: SplitResult) -> bool:
        try:
            if parsed.path == "/api/decks":
                payload = self.read_learning_json()
                identifier = str(payload.get("packSlug") or payload.get("packId") or "").strip()
                pack = self.lexicon_store.find_pack(identifier)
                if pack is None:
                    self.send_learning_json({"error": "pack not found"}, HTTPStatus.NOT_FOUND)
                    return True
                if (pack.get("quality") or {}).get("blocked"):
                    self.send_learning_json({"error": "pack failed its quality audit"}, HTTPStatus.UNPROCESSABLE_ENTITY)
                    return True
                deck = self.store.create_deck(payload, pack)
                self.send_learning_json({"deck": deck}, HTTPStatus.CREATED)
                return True

            suffix = "/serve"
            if not parsed.path.endswith(suffix):
                return False
            deck_id = self._deck_id(parsed.path[:-len(suffix)])
            if deck_id is None:
                return False
            deck = self.store.get_deck(deck_id)
            pack = self.lexicon_store.find_pack(str(deck["packId"]))
            if pack is None:
                self.send_learning_json(
                    {"error": "source pack is unavailable; existing reviews remain usable"},
                    HTTPStatus.CONFLICT,
                )
                return True
            result = self.store.serve_deck(deck_id, pack)
            self.send_learning_json(result)
            return True
        except KeyError:
            self.send_learning_json({"error": "deck not found"}, HTTPStatus.NOT_FOUND)
            return True
        except ValueError as exc:
            self.send_learning_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return True

    def handle_deck_patch(self, parsed: SplitResult) -> bool:
        deck_id = self._deck_id(parsed.path)
        if deck_id is None:
            return False
        try:
            deck = self.store.update_deck(deck_id, self.read_learning_json())
        except KeyError:
            self.send_learning_json({"error": "deck not found"}, HTTPStatus.NOT_FOUND)
            return True
        except ValueError as exc:
            self.send_learning_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return True
        self.send_learning_json({"deck": deck})
        return True

    def handle_deck_delete(self, parsed: SplitResult) -> bool:
        deck_id = self._deck_id(parsed.path)
        if deck_id is None:
            return False
        try:
            self.store.delete_deck(deck_id)
        except KeyError:
            self.send_learning_json({"error": "deck not found"}, HTTPStatus.NOT_FOUND)
            return True
        self.send_learning_json({"ok": True})
        return True

    @staticmethod
    def _deck_id(path: str) -> str | None:
        prefix = "/api/decks/"
        if not path.startswith(prefix):
            return None
        deck_id = unquote(path[len(prefix):])
        return deck_id if re.fullmatch(r"deck_[A-Za-z0-9_-]{1,120}", deck_id) else None

    def _send_pack(self, slug: str) -> bool:
        try:
            pack = self.lexicon_store.get_pack(slug)
        except Exception as exc:  # noqa: BLE001
            self.send_learning_json({"error": f"pack could not be read: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return True
        if pack is None:
            self.send_learning_json({"error": "pack not found"}, HTTPStatus.NOT_FOUND)
            return True
        if pack["quality"].get("blocked"):
            self.send_learning_json(
                {
                    "error": "This pack failed its quality audit and will not be served.",
                    "quality": pack["quality"],
                },
                HTTPStatus.UNPROCESSABLE_ENTITY,
            )
            return True
        self.send_learning_json({"pack": pack})
        return True
