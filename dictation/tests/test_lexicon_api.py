"""The `/api/lexicon*` routes, against a real server on an ephemeral port.

Phase A is read-only, so what is defended here is narrower than the exam bank's API
tests but the same in kind:

* the fail-closed gate — a pack whose audit found errors is not served for study, for
  the reason a broken exam is not: a grammar table missing a branch teaches a rule that
  is wrong in exactly the cases the exam asks about;
* the boundary — pack content is a scanned copyrighted textbook on a loopback port, so
  "it is only a read" earns it no exemption from the Host allowlist or the token;
* the path handling — a slug arrives from a URL and must never reach a file outside
  `lexicon/`.
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR / "tests"))

from lexicon_fixtures import make_pack, make_word_pack  # noqa: E402
from lexicon_schema import content_revision  # noqa: E402
from support import RunningServer, write_course  # noqa: E402


def write_pack(root: Path, slug: str, pack: dict) -> Path:
    directory = root / slug
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "pack.json"
    path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


class LexiconApiTestCase(unittest.TestCase):
    """A server with one course, one clean pack and one that failed its audit."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        root = Path(self._temp.name)
        manifest = write_course(root / "courses" / "demo")
        self.lexicon_root = root / "lexicon"

        self.pack = make_pack()
        write_pack(self.lexicon_root, "N2-grammar-fixture", self.pack)
        write_pack(self.lexicon_root, "N2-words-fixture", make_word_pack())

        broken = copy.deepcopy(self.pack)
        broken["packId"] = "N2-broken-fixture"
        broken["entries"][0]["grammar"]["connection"] = []
        broken["contentRevision"] = content_revision(broken)
        write_pack(self.lexicon_root, "N2-broken-fixture", broken)

        self.server = RunningServer(manifest, root / "data", lexicon_root=self.lexicon_root)
        self.server.__enter__()
        self.addCleanup(self._teardown)

    def _teardown(self):
        self.server.__exit__(None, None, None)
        self._temp.cleanup()

    def call(self, method, path, **kwargs):
        origin = kwargs.pop("origin", f"http://127.0.0.1:{self.server.port}")
        status, body = self.server.request(method, path, origin=origin, **kwargs)
        return status, (json.loads(body) if body else {})


class PackListTests(LexiconApiTestCase):
    def test_the_listing_names_every_pack_and_its_verdict(self):
        status, data = self.call("GET", "/api/lexicon/packs")
        self.assertEqual(status, 200)
        by_slug = {pack["slug"]: pack for pack in data["packs"]}
        self.assertEqual(
            sorted(by_slug), ["N2-broken-fixture", "N2-grammar-fixture", "N2-words-fixture"]
        )
        self.assertFalse(by_slug["N2-grammar-fixture"]["broken"])
        self.assertTrue(by_slug["N2-broken-fixture"]["broken"])

    def test_the_listing_carries_unit_counts_without_the_entries(self):
        """The shelf view needs the shape of a pack, not a megabyte of textbook text."""
        _status, data = self.call("GET", "/api/lexicon/packs")
        summary = next(pack for pack in data["packs"] if pack["slug"] == "N2-grammar-fixture")
        self.assertEqual(summary["entryCount"], 3)
        self.assertEqual([unit["entryCount"] for unit in summary["units"]], [2, 1])
        self.assertNotIn("entries", summary)

    def test_every_pack_states_whether_it_may_be_redistributed(self):
        _status, data = self.call("GET", "/api/lexicon/packs")
        for pack in data["packs"]:
            self.assertFalse(pack["distribution"]["redistributable"], pack["slug"])

    def test_one_unreadable_pack_does_not_hide_the_rest(self):
        (self.lexicon_root / "N2-corrupt").mkdir()
        (self.lexicon_root / "N2-corrupt" / "pack.json").write_text("{not json", encoding="utf-8")
        status, data = self.call("GET", "/api/lexicon/packs")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["packs"]), 4)
        corrupt = next(pack for pack in data["packs"] if pack["slug"] == "N2-corrupt")
        self.assertTrue(corrupt["broken"])

    def test_an_absent_lexicon_directory_is_not_an_error(self):
        for child in self.lexicon_root.iterdir():
            for file in child.iterdir():
                file.unlink()
            child.rmdir()
        self.lexicon_root.rmdir()
        status, data = self.call("GET", "/api/lexicon/packs")
        self.assertEqual(status, 200)
        self.assertEqual(data["packs"], [])


class PackFetchTests(LexiconApiTestCase):
    def test_a_clean_pack_is_served_whole(self):
        status, data = self.call("GET", "/api/lexicon/packs/N2-grammar-fixture")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["pack"]["entries"]), 3)
        self.assertEqual(data["pack"]["contentRevision"], self.pack["contentRevision"])
        self.assertEqual(data["pack"]["quality"]["status"], "passed")

    def test_a_pack_that_failed_its_audit_is_refused_with_422(self):
        status, data = self.call("GET", "/api/lexicon/packs/N2-broken-fixture")
        self.assertEqual(status, 422)
        self.assertIn("quality", data)
        self.assertNotIn("pack", data)

    def test_a_missing_pack_is_404(self):
        status, _data = self.call("GET", "/api/lexicon/packs/N2-nope")
        self.assertEqual(status, 404)

    def test_a_single_entry_carries_its_pack_and_unit_context(self):
        entry_id = self.pack["entries"][0]["id"]
        status, data = self.call("GET", f"/api/lexicon/entries/N2-grammar-fixture/{entry_id}")
        self.assertEqual(status, 200)
        self.assertEqual(data["entry"]["id"], entry_id)
        self.assertEqual(data["unit"]["unitId"], "w1d1")
        self.assertEqual(data["packSlug"], "N2-grammar-fixture")

    def test_an_unknown_entry_is_404(self):
        status, _data = self.call("GET", "/api/lexicon/entries/N2-grammar-fixture/g_" + "0" * 24)
        self.assertEqual(status, 404)


class SearchTests(LexiconApiTestCase):
    def test_search_matches_headwords(self):
        status, data = self.call("GET", "/api/lexicon/search?q=%E3%81%9F%E3%81%BE%E3%82%89%E3%81%AA%E3%81%84")
        self.assertEqual(status, 200)
        self.assertEqual([result["headword"] for result in data["results"]], ["〜てたまらない"])

    def test_search_matches_the_chinese_gloss_too(self):
        _status, data = self.call("GET", "/api/lexicon/search?q=%E6%B5%8B%E8%AF%95%E9%87%8A%E4%B9%89")
        self.assertGreaterEqual(len(data["results"]), 1)

    def test_search_ignores_wave_dash_variants(self):
        """〜 ～ ~ are printed interchangeably and OCR picks whichever it feels like."""
        _status, plain = self.call("GET", "/api/lexicon/search?q=%EF%BD%9E%E3%81%8C%E3%81%A1")  # ～がち
        self.assertEqual([result["headword"] for result in plain["results"]], ["〜がち"])

    def test_a_broken_pack_contributes_no_results(self):
        _status, data = self.call("GET", "/api/lexicon/search?q=%E3%81%9F%E3%81%BE%E3%82%89%E3%81%AA%E3%81%84")
        self.assertNotIn("N2-broken-fixture", {result["packSlug"] for result in data["results"]})

    def test_search_says_what_it_does_not_cover(self):
        """A search box that quietly covers a fraction of the language is a trap."""
        _status, data = self.call("GET", "/api/lexicon/search?q=%E3%81%8C%E3%81%A1")
        # `scope` now echoes what was asked for; the coverage actually searched is
        # `availableSources`, which omits the dictionary when none is installed.
        self.assertEqual(data["scope"], "all")
        self.assertEqual(data["availableSources"], ["packs", "personal"])
        self.assertNotIn("dictionary", data["availableSources"])
        self.assertFalse(data["dictionaryAvailable"])
        self.assertEqual(data["totalRelation"], "eq")

    def test_an_unknown_level_filter_is_rejected(self):
        status, _data = self.call("GET", "/api/lexicon/search?q=a&level=N9")
        self.assertEqual(status, 400)

    def test_an_empty_query_returns_nothing_rather_than_everything(self):
        _status, data = self.call("GET", "/api/lexicon/search?q=")
        self.assertEqual(data["results"], [])


class BoundaryTests(LexiconApiTestCase):
    def test_a_read_without_a_token_is_refused(self):
        status, _body = self.server.request("GET", "/api/lexicon/packs", token=None)
        self.assertEqual(status, 403)

    def test_a_read_with_the_wrong_token_is_refused(self):
        status, _body = self.server.request("GET", "/api/lexicon/packs", token="not-the-token")
        self.assertEqual(status, 403)

    def test_a_forged_host_header_is_refused(self):
        status, _body = self.server.request("GET", "/api/lexicon/packs", host="evil.example")
        self.assertEqual(status, 403)

    def test_a_traversal_slug_cannot_read_a_file_outside_the_root(self):
        for slug in ("..%2F..%2Fetc%2Fpasswd", "..", "%2e%2e%2f%2e%2e%2fmanifest"):
            status, _data = self.call("GET", f"/api/lexicon/packs/{slug}")
            self.assertIn(status, (400, 404), slug)

    def test_an_entry_path_with_extra_segments_is_rejected(self):
        status, _data = self.call("GET", "/api/lexicon/entries/a/b/c")
        self.assertEqual(status, 400)

    def test_the_workspace_route_serves_the_lexicon_page(self):
        status, body = self.server.request("GET", "/lexicon")
        self.assertEqual(status, 200)
        self.assertIn(b"lexicon.js", body)


class DeckAndReviewTests(LexiconApiTestCase):
    def create_deck(self, **overrides):
        payload = {
            "packSlug": "N2-grammar-fixture", "name": "N2 grammar",
            "dailyNew": 2, "orderMode": "source", "studyTimezone": "Asia/Shanghai",
            **overrides,
        }
        status, data = self.call("POST", "/api/decks", body=payload)
        self.assertEqual(status, 201, data)
        return data["deck"]

    def test_daily_serve_is_idempotent_and_cards_are_reviewable(self):
        deck = self.create_deck()
        self.assertEqual(deck["progress"]["total"], 6)
        status, first = self.call("POST", f"/api/decks/{deck['id']}/serve")
        self.assertEqual(status, 200, first)
        self.assertEqual(len(first["items"]), 2)
        _status, second = self.call("POST", f"/api/decks/{deck['id']}/serve")
        self.assertEqual([item["id"] for item in first["items"]], [item["id"] for item in second["items"]])

        card = first["items"][0]
        self.assertEqual(card["entryKind"], "grammar")
        self.assertTrue(card["sourceRef"].startswith("lex:"))
        status, reviewed = self.call("POST", "/api/vocab/review", body={
            "vocabId": card["id"], "grade": "easy", "reviewedAt": "2026-09-03T12:00:00+00:00",
        }, headers={"X-Learning-Operation-Id": "op_lex_review_1"})
        self.assertEqual(status, 200, reviewed)
        self.assertEqual(reviewed["item"]["srsStage"], 3)

    def test_two_decks_share_one_global_card_and_delete_preserves_it(self):
        one = self.create_deck(dailyNew=1)
        two = self.create_deck(name="second", dailyNew=1)
        _, served_one = self.call("POST", f"/api/decks/{one['id']}/serve")
        _, served_two = self.call("POST", f"/api/decks/{two['id']}/serve")
        card_id = served_one["items"][0]["id"]
        self.assertEqual(card_id, served_two["items"][0]["id"])
        status, _ = self.call("DELETE", f"/api/decks/{one['id']}")
        self.assertEqual(status, 200)
        status, vocab = self.call("GET", "/api/vocab")
        self.assertEqual(status, 200)
        self.assertIn(card_id, {item["id"] for item in vocab["items"]})

    def test_unknown_grade_is_rejected_without_mutating_srs(self):
        deck = self.create_deck(dailyNew=1)
        _, served = self.call("POST", f"/api/decks/{deck['id']}/serve")
        card = served["items"][0]
        status, _ = self.call("POST", "/api/vocab/review", body={
            "vocabId": card["id"], "grade": "almost", "reviewedAt": "2026-09-03T12:00:00Z",
        })
        self.assertEqual(status, 400)
        _, vocab = self.call("GET", "/api/vocab")
        unchanged = next(item for item in vocab["items"] if item["id"] == card["id"])
        self.assertEqual(unchanged["srsRepetitions"], 0)

    def test_review_time_conflicts_and_mature_due_semantics(self):
        deck = self.create_deck(dailyNew=1)
        _, served = self.call("POST", f"/api/decks/{deck['id']}/serve")
        card_id = served["items"][0]["id"]
        headers = {"X-Learning-Operation-Id": "op_time_order_1"}
        payload = {"vocabId": card_id, "grade": "easy", "reviewedAt": "2026-09-03T12:00:00Z"}
        status, _ = self.call("POST", "/api/vocab/review", body=payload, headers=headers)
        self.assertEqual(status, 200)
        # The same operation hits its receipt before stale-event validation.
        status, replay = self.call("POST", "/api/vocab/review", body=payload, headers=headers)
        self.assertEqual(status, 200)
        self.assertEqual(replay["item"]["srsRepetitions"], 1)
        status, _ = self.call("POST", "/api/vocab/review", body={
            "vocabId": card_id, "grade": "good", "reviewedAt": "2026-09-02T12:00:00Z",
        }, headers={"X-Learning-Operation-Id": "op_time_order_2"})
        self.assertEqual(status, 409)
        status, _ = self.call("POST", "/api/vocab/review", body={
            "vocabId": card_id, "grade": "good", "reviewedAt": "2099-01-01T00:00:00Z",
        })
        self.assertEqual(status, 400)

        connection = self.server.preview._store.connection
        connection.execute("UPDATE vocab SET next_review_at = '2000-01-01T00:00:00+00:00' WHERE id = ?", (card_id,))
        connection.commit()
        _, due = self.call("GET", f"/api/review/due?scope=grammar&deckId={deck['id']}")
        self.assertEqual([item["id"] for item in due["dueVocab"]], [card_id])
        self.call("POST", "/api/vocab/batch", body={"action": "mark_mastered", "ids": [card_id]})
        _, paused = self.call("GET", f"/api/review/due?scope=grammar&deckId={deck['id']}")
        self.assertEqual(paused["dueVocab"], [])


if __name__ == "__main__":
    unittest.main()
