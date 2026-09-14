"""A pack and everything describing it are published together (LEX-14, §6.5).

The shipped grammar pack carries a `match-report.json` for revision `109a4721…` while
the pack itself is `24adb2f2…`: the report was stamped before `supplement_pack()` ran.
Per-file `os.replace` also only made each file individually atomic, and `pack.json` was
written with a plain truncating write.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src"), str(Path(__file__).parent)]

from lexicon_content import load_seed_registry, resolve_seed_keys, seed_key  # noqa: E402
from lexicon_fixtures import make_pack  # noqa: E402
from lexicon_schema import audit_pack, content_revision, publish_pack  # noqa: E402


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "pack"
        self.pack = make_pack()

    def publish(self, **extra):
        return publish_pack(self.directory, {
            "pack.json": self.pack,
            "match-report.json": {"contentRevision": self.pack["contentRevision"], **extra},
            "quality-report.json": audit_pack(self.pack),
        }, revision=self.pack["contentRevision"])

    def test_the_manifest_records_the_revision_and_every_file(self):
        manifest = self.publish()
        stored = json.loads((self.directory / "publish.json").read_text(encoding="utf-8"))
        self.assertEqual(stored["contentRevision"], self.pack["contentRevision"])
        self.assertEqual(set(stored["files"]), {"pack.json", "match-report.json", "quality-report.json"})
        self.assertEqual(manifest["files"], stored["files"])

    def test_every_report_describes_the_revision_that_was_published(self):
        self.publish()
        pack = json.loads((self.directory / "pack.json").read_text(encoding="utf-8"))
        report = json.loads((self.directory / "match-report.json").read_text(encoding="utf-8"))
        manifest = json.loads((self.directory / "publish.json").read_text(encoding="utf-8"))
        self.assertEqual(pack["contentRevision"], report["contentRevision"])
        self.assertEqual(pack["contentRevision"], manifest["contentRevision"])

    def test_a_failed_publish_leaves_the_previous_version_in_place(self):
        self.publish(note="first")
        original = (self.directory / "pack.json").read_text(encoding="utf-8")

        class Unserialisable:
            pass

        with self.assertRaises(TypeError):
            publish_pack(self.directory, {"pack.json": {"bad": Unserialisable()}},
                         revision="deadbeef")
        # Nothing was replaced, and no staging directory was left behind.
        self.assertEqual((self.directory / "pack.json").read_text(encoding="utf-8"), original)
        self.assertEqual(
            json.loads((self.directory / "match-report.json").read_text(encoding="utf-8"))["note"], "first")
        self.assertEqual([p.name for p in self.directory.iterdir() if p.name.startswith(".publish-")], [])

    def test_the_build_time_is_not_part_of_the_content_revision(self):
        first = self.publish()
        second = self.publish()
        self.assertNotEqual(first["publishedAt"], second["publishedAt"])
        # Same inputs, same revision: the timestamp lives in the manifest only (§6.5).
        self.assertEqual(content_revision(self.pack), self.pack["contentRevision"])
        self.assertEqual(first["contentRevision"], second["contentRevision"])
        self.assertEqual(first["files"]["pack.json"], second["files"]["pack.json"])


class SeedRegistryTests(unittest.TestCase):
    """LEX-14 / §6.4.4: a seed's key is allocated once and never moves."""

    def test_a_seed_is_identified_by_its_word_not_its_position(self):
        self.assertEqual(seed_key("承る", "うけたまわる"), seed_key("承る", "ウケタマワル"))
        self.assertNotEqual(seed_key("承る", "うけたまわる"), seed_key("受ける", "うける"))

    def test_inserting_a_word_does_not_renumber_the_ones_after_it(self):
        registry = load_seed_registry(Path("does-not-exist.json"), "Everyday-words")
        first = resolve_seed_keys(registry, ["a|a", "b|b", "c|c"])
        self.assertEqual([first[k] for k in ("a|a", "b|b", "c|c")], ["e0001", "e0002", "e0003"])

        # The same registry, with a new word inserted at the front of the seed list.
        second = resolve_seed_keys(registry, ["new|new", "a|a", "b|b", "c|c"])
        self.assertEqual(second["a|a"], "e0001")
        self.assertEqual(second["c|c"], "e0003")
        self.assertEqual(second["new|new"], "e0004", "new seeds append")

    def test_reordering_the_seed_list_changes_nothing(self):
        registry = load_seed_registry(Path("does-not-exist.json"), "Everyday-words")
        before = dict(resolve_seed_keys(registry, ["a|a", "b|b", "c|c"]))
        after = resolve_seed_keys(registry, ["c|c", "a|a", "b|b"])
        self.assertEqual(after, before)

    def test_a_registry_for_another_pack_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "word-keys.json"
            path.write_text(json.dumps({"packId": "Other", "entries": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_seed_registry(path, "Everyday-words")

    def test_the_registry_round_trips_through_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "word-keys.json"
            registry = load_seed_registry(path, "Everyday-words")
            resolve_seed_keys(registry, ["a|a", "b|b"])
            path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
            reloaded = load_seed_registry(path, "Everyday-words")
            self.assertEqual(resolve_seed_keys(reloaded, ["b|b", "a|a"]),
                             {"a|a": "e0001", "b|b": "e0002"})


if __name__ == "__main__":
    unittest.main()
