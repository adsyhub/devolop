"""Identity, audit rules and the copyright boundary for lexicon packs.

Two things are being defended here.

The first is the learner's history. An entry id that changes when a typo is fixed
silently detaches every card the learner has been reviewing for weeks, and nothing in the
interface can show that it happened. So the id must come from the frozen key and nothing
else, and the audit must refuse a pack where that stopped being true.

The second is the copyright boundary. A pack built from a scanned textbook is that
textbook; the rules that say so are only worth anything if they cannot be turned off by
setting a flag.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR / "tests"))

from distribution_policy import (  # noqa: E402
    audit_entry_key_registry,
    audit_release_artifact,
    describe_pack_distribution,
    forbidden_release_paths,
)
from lexicon_fixtures import PACK_ID, make_meta, make_pack, make_word_pack  # noqa: E402
from lexicon_schema import (  # noqa: E402
    ConnectionError_,
    audit_pack,
    content_revision,
    default_card_templates,
    entry_id,
    normalized_headword,
    parse_connection,
    parse_source_ref,
    prepare_pack,
)


def codes(report):
    return {issue["code"] for issue in report["issues"]}


class PreparePackTests(unittest.TestCase):
    def test_a_clean_pack_passes_its_audit(self):
        report = audit_pack(make_pack())
        self.assertEqual(report["status"], "passed", report["issues"])
        self.assertEqual(report["summary"]["errors"], 0)
        self.assertEqual(report["summary"]["warnings"], 0)

    def test_ids_are_deterministic_across_machines(self):
        first = [entry["id"] for entry in make_pack()["entries"]]
        second = [entry["id"] for entry in make_pack()["entries"]]
        self.assertEqual(first, second)
        self.assertEqual(first[0], entry_id(PACK_ID, "e0001", "grammar"))

    def test_id_is_96_bits_and_kind_tagged(self):
        word = make_word_pack()["entries"][0]["id"]
        grammar = make_pack()["entries"][0]["id"]
        self.assertTrue(word.startswith("w_"))
        self.assertTrue(grammar.startswith("g_"))
        self.assertEqual(len(word.split("_")[1]), 24)

    def test_correcting_the_headword_does_not_change_the_id(self):
        """The whole point of entryKey: an OCR fix must not orphan the learner's cards."""
        pack = make_pack()
        before = [entry["id"] for entry in pack["entries"]]
        pack["entries"][0]["headword"] = "〜てたまらない（訂正）"
        after = [entry["id"] for entry in prepare_pack(pack)["entries"]]
        self.assertEqual(before, after)

    def test_moving_an_entry_to_another_unit_does_not_change_the_id(self):
        pack = make_pack()
        before = {entry["entryKey"]: entry["id"] for entry in pack["entries"]}
        pack["units"][0]["entryIds"] = [before["e0001"]]
        pack["units"][1]["entryIds"] = [before["e0002"], before["e0003"]]
        pack["entries"][1]["unitId"] = "w1d2"
        after = {entry["entryKey"]: entry["id"] for entry in prepare_pack(pack)["entries"]}
        self.assertEqual(before, after)

    def test_adding_an_example_does_not_change_the_id(self):
        pack = make_pack()
        before = [entry["id"] for entry in pack["entries"]]
        pack["entries"][0]["examples"].append({"exampleId": "ex2", "ja": "追加の文です。", "zh": "补充例句。"})
        after = [entry["id"] for entry in prepare_pack(pack)["entries"]]
        self.assertEqual(before, after)

    def test_a_hand_edited_id_is_refused_rather_than_rewritten(self):
        pack = make_pack()
        pack["entries"][0]["id"] = "g_" + "0" * 24
        with self.assertRaises(ValueError) as caught:
            prepare_pack(pack)
        self.assertIn("idAliases", str(caught.exception))

    def test_order_follows_the_unit_lists(self):
        pack = make_pack()
        self.assertEqual([entry["order"] for entry in pack["entries"]], [1, 2, 3])
        self.assertEqual([unit["entryCount"] for unit in pack["units"]], [2, 1])

    def test_content_revision_covers_glosses_and_rights(self):
        pack = make_pack()
        original = pack["contentRevision"]
        self.assertEqual(len(original), 64)

        glossed = copy.deepcopy(pack)
        glossed["entries"][0]["gloss"]["zh"] = "改过的释义"
        self.assertNotEqual(content_revision(glossed), original)

        rights = copy.deepcopy(pack)
        rights["attribution"]["publisher"] = "別の出版社"
        self.assertNotEqual(content_revision(rights), original)

    def test_content_revision_ignores_a_stale_revision_field(self):
        """Two machines with the same content must agree, whatever was in the file."""
        pack = make_pack()
        stale = copy.deepcopy(pack)
        stale["contentRevision"] = "f" * 64
        self.assertEqual(content_revision(stale), content_revision(pack))

    def test_readings_without_a_source_are_dropped_not_invented(self):
        pack = make_pack()
        pack["entries"][0]["examples"][0]["reading"] = "これはぶんです"
        prepared = prepare_pack(pack)
        self.assertNotIn("reading", prepared["entries"][0]["examples"][0])

    def test_a_sourced_reading_survives(self):
        pack = make_pack()
        pack["entries"][0]["examples"][0].update({"reading": "これはぶんです", "readingSource": "manual"})
        prepared = prepare_pack(pack)
        self.assertEqual(prepared["entries"][0]["examples"][0]["reading"], "これはぶんです")


class RightsTests(unittest.TestCase):
    def test_a_textbook_pack_may_not_claim_to_be_redistributable(self):
        pack = make_pack()
        pack["attribution"]["redistributable"] = True
        with self.assertRaises(ValueError):
            prepare_pack(pack)

    def test_the_audit_flags_the_claim_rather_than_correcting_it(self):
        """Rewriting the flag would hide the fact that a pack was built believing it."""
        pack = make_pack()
        pack["attribution"]["redistributable"] = True
        pack["contentRevision"] = content_revision(pack)
        report = audit_pack(pack)
        self.assertIn("pack.redistributable_claim", codes(report))
        self.assertEqual(report["status"], "failed")

    def test_distribution_verdict_refuses_a_textbook_pack(self):
        verdict = describe_pack_distribution(make_pack())
        self.assertFalse(verdict["redistributable"])
        self.assertTrue(any("textbook" in reason.lower() for reason in verdict["reasons"]))

    def test_unknown_provenance_publishes_nothing(self):
        verdict = describe_pack_distribution({"packId": "x", "attribution": {"sourceType": "scraped"}})
        self.assertFalse(verdict["redistributable"])

    def test_release_artifacts_may_not_contain_pack_text(self):
        offenders = forbidden_release_paths(
            [
                "web/app.js",
                "lexicon/N2-grammar-soumatome/pack.json",
                "lexicon/N2-grammar-soumatome/pages/p0018.json",
                "lexicon/N2-grammar-soumatome/units.txt",
                "lexicon/N2-grammar-soumatome/pack-meta.json",
                "lexicon/N2-grammar-soumatome/entry-keys.json",
            ]
        )
        self.assertEqual(
            offenders,
            [
                "lexicon/N2-grammar-soumatome/pack.json",
                "lexicon/N2-grammar-soumatome/pages/p0018.json",
                "lexicon/N2-grammar-soumatome/units.txt",
            ],
        )
        self.assertFalse(audit_release_artifact(offenders)["passed"])

    def test_windows_separators_do_not_slip_past_the_scan(self):
        self.assertEqual(
            forbidden_release_paths(["lexicon\\N2-grammar\\pages\\p0018.json"]),
            ["lexicon/N2-grammar/pages/p0018.json"],
        )

    def test_no_textbook_content_is_tracked_in_this_repository(self):
        """The rule is only worth anything if something checks the real repository.

        LEXICON.md §8.4 asks for a scan before committing, so it runs here rather than
        in a hook nobody installed. It reads what git actually tracks, not .gitignore:
        a file added with `git add -f` is ignored *and* committed.
        """
        try:
            tracked = subprocess.run(
                ["git", "ls-files", "lexicon/"],
                cwd=PROJECT_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            ).stdout.splitlines()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.skipTest("git is not available")
        self.assertEqual(forbidden_release_paths(tracked), [])

        for path in tracked:
            if path.endswith("entry-keys.json"):
                registry = json.loads((PROJECT_DIR / path).read_text(encoding="utf-8"))
                self.assertTrue(audit_entry_key_registry(registry)["passed"], path)

    def test_the_ignore_rules_keep_pack_text_untracked(self):
        rules = (PROJECT_DIR / ".gitignore").read_text(encoding="utf-8")
        for pattern in (
            "lexicon/*/pages/",
            "lexicon/*/pack.json",
            "lexicon/*/units.txt",
            "lexicon/*/match-report.json",
            "lexicon/*/match-resolutions.json",
        ):
            self.assertIn(pattern, rules)

    def test_the_committed_registry_may_carry_identity_only(self):
        clean = {
            "schemaVersion": 1,
            "packId": PACK_ID,
            "nextKey": 4,
            "entries": [{"entryKey": "e0001", "sourceAnchor": "pdf:18:block:2"}],
        }
        self.assertTrue(audit_entry_key_registry(clean)["passed"])

        leaky = copy.deepcopy(clean)
        leaky["entries"][0]["headwordHint"] = "〜てたまらない"
        verdict = audit_entry_key_registry(leaky)
        self.assertFalse(verdict["passed"])
        self.assertIn("entries[].headwordHint", verdict["offenders"])


class ConnectionTests(unittest.TestCase):
    def test_the_books_own_notation_parses(self):
        self.assertEqual(
            parse_connection("Aくて"),
            {"slot": "i-adjective", "form": "くて", "display": "イAくて", "tail": ""},
        )
        self.assertEqual(parse_connection("naで")["slot"], "na-adjective")
        self.assertEqual(parse_connection("Vたくて")["slot"], "verb-desiderative")

    def test_the_pattern_tail_stays_in_the_display_form(self):
        parsed = parse_connection("Vます気味")
        self.assertEqual(parsed["form"], "ます")
        self.assertEqual(parsed["display"], "Vます気味")

    def test_the_longest_marker_wins(self):
        """Vたくて is the desiderative, not Vた with a stray くて."""
        self.assertEqual(parse_connection("Vたくて")["form"], "たくて")
        self.assertEqual(parse_connection("Vた")["form"], "た")

    def test_the_ocr_confusion_this_book_actually_produced_is_an_error(self):
        with self.assertRaises(ConnectionError_) as caught:
            parse_connection("なで")
        self.assertIn("naで", str(caught.exception))

    def test_two_connections_run_together_are_refused(self):
        with self.assertRaises(ConnectionError_):
            parse_connection("AくてVたくて")

    def test_an_unrecognised_base_is_not_guessed_at(self):
        with self.assertRaises(ConnectionError_):
            parse_connection("けれども")

    def test_an_ordinary_word_starting_with_the_plain_form_marker_is_not_a_connection(self):
        """普 is also a kanji: 普通の話 must not be read as a connection abbreviation."""
        with self.assertRaises(ConnectionError_):
            parse_connection("普通の話")
        self.assertEqual(parse_connection("普")["slot"], "plain-form")

    def test_a_discourse_connector_uses_a_clause_slot(self):
        parsed = parse_connection("文。それなのに")
        self.assertEqual(parsed["slot"], "clause")
        self.assertEqual(parsed["display"], "文。それなのに")
        with self.assertRaises(ConnectionError_):
            parse_connection("文章")

    def test_noun_connection_supports_forms_printed_in_this_book(self):
        self.assertEqual(parse_connection("Nなものだから")["form"], "な")
        self.assertEqual(parse_connection("Nであるものの")["form"], "である")

    def test_the_audit_rejects_a_grammar_entry_with_no_connection(self):
        pack = make_pack()
        pack["entries"][0]["grammar"]["connection"] = []
        pack["contentRevision"] = content_revision(pack)
        self.assertIn("grammar.connection_missing", codes(audit_pack(pack)))


class AuditTests(unittest.TestCase):
    def _broken(self, mutate):
        pack = make_pack()
        mutate(pack)
        pack["contentRevision"] = content_revision(pack)
        return audit_pack(pack)

    def test_an_entry_in_no_unit_is_an_error(self):
        report = self._broken(lambda pack: pack["units"][1].update({"entryIds": []}))
        self.assertIn("unit.entries_missing", codes(report))
        self.assertIn("entry.unit_missing", codes(report))

    def test_an_entry_in_two_units_is_an_error(self):
        def mutate(pack):
            pack["units"][1]["entryIds"] = list(pack["units"][0]["entryIds"])

        self.assertIn("entry.unit_duplicate", codes(self._broken(mutate)))

    def test_a_unit_naming_an_unknown_entry_is_an_error(self):
        def mutate(pack):
            pack["units"][0]["entryIds"] = ["g_" + "a" * 24] + pack["units"][0]["entryIds"]

        self.assertIn("unit.entry_unknown", codes(self._broken(mutate)))

    def test_entry_kind_must_match_the_pack(self):
        self.assertIn(
            "entry.kind_mismatch",
            codes(self._broken(lambda pack: pack["entries"][0].update({"kind": "word"}))),
        )

    def test_a_missing_chinese_gloss_is_an_error(self):
        self.assertIn(
            "entry.gloss_zh_missing",
            codes(self._broken(lambda pack: pack["entries"][0]["gloss"].pop("zh"))),
        )

    def test_a_reading_with_no_accountable_source_is_an_error(self):
        def mutate(pack):
            pack["entries"][0]["examples"][0]["reading"] = "でっちあげ"

        report = self._broken(mutate)
        self.assertIn("example.reading_unsourced", codes(report))

    def test_a_cloze_card_needs_a_balanced_blank(self):
        def mutate(pack):
            pack["entries"][0]["cardTemplates"][1]["markedJa"] = "これは⟦てたまらない文です。"

        self.assertIn("card.cloze_unbalanced", codes(self._broken(mutate)))

    def test_two_templates_may_not_share_a_card_identity(self):
        def mutate(pack):
            pack["entries"][0]["cardTemplates"][1]["promptType"] = "recall"
            pack["entries"][0]["cardTemplates"][1]["variantKey"] = "default"

        self.assertIn("card.identity_duplicate", codes(self._broken(mutate)))

    def test_a_usage_card_without_reasons_is_refused(self):
        def mutate(pack):
            other = pack["entries"][1]["id"]
            pack["entries"][0]["cardTemplates"].append(
                {
                    "variantKey": "usage-ex1",
                    "promptType": "usage",
                    "exampleId": "ex1",
                    "choiceRefs": ["self", f"lex:{PACK_ID}#{other}"],
                    "answerRef": "self",
                    "rationales": [],
                }
            )

        self.assertIn("card.usage_rationale_missing", codes(self._broken(mutate)))

    def test_a_usage_card_with_reviewed_reasons_passes(self):
        pack = make_pack()
        other = pack["entries"][1]["id"]
        pack["entries"][0]["cardTemplates"].append(
            {
                "variantKey": "usage-ex1",
                "promptType": "usage",
                "exampleId": "ex1",
                "choiceRefs": ["self", f"lex:{PACK_ID}#{other}"],
                "answerRef": "self",
                "rationales": [{"choiceRef": f"lex:{PACK_ID}#{other}", "reason": "感情ではなく自然発生の意味。"}],
            }
        )
        pack["contentRevision"] = content_revision(pack)
        self.assertEqual(audit_pack(pack)["summary"]["errors"], 0)

    def test_a_usage_choice_outside_the_pack_is_an_error(self):
        def mutate(pack):
            pack["entries"][0]["cardTemplates"].append(
                {
                    "variantKey": "usage-ex1",
                    "promptType": "usage",
                    "choiceRefs": ["self", f"lex:{PACK_ID}#g_" + "b" * 24],
                    "answerRef": "self",
                    "rationales": [{"choiceRef": f"lex:{PACK_ID}#g_" + "b" * 24, "reason": "だめ"}],
                }
            )

        self.assertIn("card.usage_choice_unknown", codes(self._broken(mutate)))

    def test_an_error_level_flag_may_not_ship_with_an_entry(self):
        def mutate(pack):
            pack["entries"][0]["flags"] = [{"severity": "error", "code": "x", "message": "y"}]

        self.assertIn("entry.flag_severity_invalid", codes(self._broken(mutate)))

    def test_a_stale_content_revision_is_an_error(self):
        pack = make_pack()
        pack["entries"][0]["headword"] = "〜てしかたがない"
        self.assertIn("pack.revision_stale", codes(audit_pack(pack)))

    def test_stray_markup_in_entry_text_is_an_error(self):
        def mutate(pack):
            pack["entries"][0]["gloss"]["zh"] = "<script>alert(1)</script>"

        self.assertIn("entry.stray_markup", codes(self._broken(mutate)))

    def test_duplicate_headwords_are_a_warning_not_a_merge(self):
        def mutate(pack):
            pack["entries"][1]["headword"] = "～てたまらない"  # different wave dash

        report = self._broken(mutate)
        self.assertIn("entry.headword_duplicate", codes(report))
        self.assertEqual(report["summary"]["errors"], 0)


class HelperTests(unittest.TestCase):
    def test_normalisation_folds_wave_dashes_but_not_identity(self):
        self.assertEqual(normalized_headword("〜てたまらない"), normalized_headword("～てたまらない"))
        self.assertEqual(normalized_headword("Ｖます"), "Vます")

    def test_source_refs_round_trip(self):
        pack = make_pack()
        reference = f"lex:{PACK_ID}#{pack['entries'][0]['id']}"
        self.assertEqual(parse_source_ref(reference), (PACK_ID, pack["entries"][0]["id"]))
        self.assertIsNone(parse_source_ref("lex:bad ref"))

    def test_default_templates_lead_with_cloze_for_grammar(self):
        entry = {
            "kind": "grammar",
            "examples": [{"exampleId": "ex1", "markedJa": "これは⟦テスト⟧です。"}],
        }
        templates = default_card_templates(entry)
        self.assertEqual([item["promptType"] for item in templates], ["recall", "cloze"])

    def test_no_usage_card_is_generated_automatically(self):
        entry = {"kind": "grammar", "examples": [{"exampleId": "ex1", "markedJa": "⟦x⟧"}]}
        self.assertNotIn("usage", [item["promptType"] for item in default_card_templates(entry)])

    def test_a_word_pack_audits_under_the_same_rules(self):
        report = audit_pack(make_word_pack())
        self.assertEqual(report["summary"]["errors"], 0, report["issues"])

    def test_meta_fixture_matches_the_pack_it_describes(self):
        self.assertEqual(make_meta()["packId"], make_pack()["packId"])


if __name__ == "__main__":
    unittest.main()
