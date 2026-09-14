"""Paging is over the match set, not over a truncated candidate list (LEX-08).

The old route read the first 100 index rows, mixed in up to 100 dictionary rows and then
sliced by cursor, so a 242-match query reported `total=100` and returned nothing from
`cursor=100`, and the favourites filter only ever saw the surviving 100.
"""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src"), str(Path(__file__).parent)]

import lexicon_search  # noqa: E402
from lexicon_api import LexiconServices  # noqa: E402
from lexicon_fixtures import make_word_pack  # noqa: E402
from lexicon_schema import prepare_pack  # noqa: E402
from lexicon_store import LexiconStore  # noqa: E402
from local_backend import LearningStore  # noqa: E402
from test_lexicon_api import write_pack  # noqa: E402

WORD = "承る"


def many_entries(count, pack_id="Bulk-words-fixture"):
    """A pack whose entries all match one query, so paging has something to page."""
    base = make_word_pack()["entries"][0]
    entries = []
    for index in range(count):
        entry = copy.deepcopy(base)
        entry.pop("id", None)
        entry.pop("sourceRef", None)
        entry.pop("order", None)
        entry["entryKey"] = f"e{index + 1:04d}"
        entry["gloss"] = {"zh": f"共同词根 第{index + 1}条", "en": "shared stem"}
        entries.append(entry)
    return prepare_pack({
        "packId": pack_id, "kind": "word", "level": "N2", "title": "批量测试包",
        "attribution": {"sourceType": "textbook-ocr", "publisher": "テスト出版", "redistributable": False},
        "units": [{"unitId": "u1", "label": "第1課", "title": "テスト",
                   "entryIds": [e["entryKey"] for e in entries]}],
        "entries": entries,
    })


class SearchPagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pack = many_entries(137)
        write_pack(self.root / "lexicon", "bulk", self.pack)
        self.store = LearningStore(self.root / "learning.sqlite3"); self.addCleanup(self.store.close)
        self.s = LexiconServices(self.store, LexiconStore(self.root / "lexicon"))

    def page(self, **params):
        return lexicon_search.search(self.s, {"q": "共同词根", **params})

    def walk(self, **params):
        collected, cursor, pages = [], "", 0
        while True:
            page = self.page(cursor=cursor, **params)
            collected.extend(item["sourceRef"] for item in page["results"])
            pages += 1
            if not page["nextCursor"] or pages > 60:
                break
            cursor = page["nextCursor"]
        return collected, page, pages

    def test_every_match_is_reachable_exactly_once(self):
        first = self.page(limit="30")
        self.assertEqual(first["total"], 137)
        self.assertEqual(first["totalRelation"], "eq")
        self.assertTrue(first["hasMore"])
        collected, last, pages = self.walk(limit="30")
        self.assertEqual(len(collected), 137)
        self.assertEqual(len(set(collected)), 137, "pages must not overlap")
        self.assertFalse(last["hasMore"])
        self.assertIsNone(last["nextCursor"])
        self.assertGreater(pages, 4)

    def test_the_page_after_the_hundredth_match_is_not_empty(self):
        cursor = ""
        for _ in range(4):
            page = self.page(limit="25", cursor=cursor)
            cursor = page["nextCursor"]
        # This is the exact shape of the old defect: page five of a >100 match query.
        self.assertTrue(page["results"])
        self.assertEqual(len(self.page(limit="25", cursor=cursor)["results"]), 25)

    def test_paging_covers_the_match_set_in_a_frozen_order(self):
        by_thirty, _, _ = self.walk(limit="30")
        by_seven, _, _ = self.walk(limit="7")
        self.assertEqual(by_thirty, by_seven, "page size must not change the order")

    def test_the_favourites_filter_reaches_beyond_the_first_page(self):
        refs = [f"lex:{self.pack['packId']}#{entry['id']}" for entry in self.pack["entries"]]
        late = refs[130]
        self.s.practice.save_user_entry({"sourceRef": late, "headword": WORD, "starred": True})
        result = self.page(starred="1", limit="30")
        # Filtering after truncation could never have found an entry this far down.
        self.assertEqual(result["total"], 1)
        self.assertEqual([item["sourceRef"] for item in result["results"]], [late])
        self.assertTrue(result["results"][0]["starred"])

    def test_a_favourite_of_nothing_returns_nothing_rather_than_everything(self):
        self.assertEqual(self.page(starred="1")["results"], [])
        self.assertEqual(self.page(starred="1")["total"], 0)

    def test_a_stale_cursor_is_rejected_with_its_own_code(self):
        first = self.page(limit="30")
        write_pack(self.root / "lexicon", "bulk", many_entries(140))
        self.s.index.store = LexiconStore(self.root / "lexicon")
        with self.assertRaises(lexicon_search.CursorError):
            self.page(limit="30", cursor=first["nextCursor"])

    def test_the_old_numeric_cursor_is_refused_rather_than_misread(self):
        with self.assertRaises(lexicon_search.CursorError):
            self.page(cursor="100")
        with self.assertRaises(lexicon_search.CursorError):
            self.page(cursor="not-a-cursor")

    def test_a_unit_filter_must_name_its_pack(self):
        with self.assertRaises(ValueError):
            self.page(unit="u1")
        scoped = self.page(pack="bulk", unit="u1", limit="5")
        self.assertEqual(scoped["total"], 137)

    def test_the_dictionary_scope_refuses_grammar_instead_of_returning_words(self):
        result = lexicon_search.search(self.s, {"q": "承", "scope": "dictionary", "kind": "grammar"})
        self.assertEqual(result["results"], [])
        self.assertTrue(result["notes"])

    def test_unknown_scopes_and_fields_are_rejected(self):
        for bad in ({"scope": "everything"}, {"field": "nonsense"}, {"level": "N9"}, {"kind": "kanji"}):
            with self.assertRaises(ValueError):
                self.page(**bad)

    def test_a_personal_entry_is_not_listed_twice_alongside_its_pack_row(self):
        ref = f"lex:{self.pack['packId']}#{self.pack['entries'][0]['id']}"
        self.s.practice.save_user_entry({"sourceRef": ref, "headword": WORD, "note": "共同词根 我的笔记"})
        collected, _, _ = self.walk(limit="30")
        self.assertEqual(len(collected), len(set(collected)))
        self.assertEqual(collected.count(ref), 1)

    def test_a_personal_only_entry_is_searchable_and_counted(self):
        self.s.practice.save_user_entry(
            {"sourceRef": "user:mine", "headword": "自造词", "gloss": {"zh": "共同词根 个人条目"}})
        result = self.page(scope="personal")
        self.assertEqual([item["sourceRef"] for item in result["results"]], ["user:mine"])
        self.assertEqual(result["total"], 1)
        merged, _, _ = self.walk(limit="30")
        self.assertIn("user:mine", merged)
        self.assertEqual(len(merged), 138)


if __name__ == "__main__":
    unittest.main()
