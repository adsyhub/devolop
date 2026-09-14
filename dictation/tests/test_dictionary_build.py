"""Publishing a dictionary is one step, and an install is a job you can see and stop.

Covers LEX-18 (§9.3 degradation, §9.4 install jobs): the XML restrictions must survive
into the built rows, a missing FTS5 must degrade rather than fail, a failed or cancelled
build must leave the previous version serving, and a job must be recognisable after the
process that started it is gone.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import dictionary_build  # noqa: E402
from dictionary_jobs import InstallJobs  # noqa: E402
from dictionary_store import DictionaryStore  # noqa: E402

SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<JMdict>
  <entry>
    <ent_seq>1414870</ent_seq>
    <k_ele><keb>大人</keb></k_ele>
    <k_ele><keb>成人</keb></k_ele>
    <r_ele><reb>おとな</reb></r_ele>
    <r_ele><reb>せいじん</reb><re_restr>成人</re_restr></r_ele>
    <r_ele><reb>たいじん</reb><re_restr>大人</re_restr></r_ele>
    <sense><pos>&n;</pos><gloss>adult</gloss><stagr>おとな</stagr></sense>
    <sense><pos>&n;</pos><gloss>person of magnanimity</gloss><stagk>大人</stagk>
      <stagr>たいじん</stagr><s_inf>archaic</s_inf></sense>
  </entry>
  <entry>
    <ent_seq>1578850</ent_seq>
    <k_ele><keb>承る</keb><ke_pri>ichi1</ke_pri></k_ele>
    <r_ele><reb>うけたまわる</reb></r_ele>
    <sense><pos>&v5r;</pos><gloss>to hear</gloss><gloss>to accept</gloss></sense>
  </entry>
</JMdict>
"""


class DictionaryBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "JMdict_e.xml"
        self.source.write_text(SAMPLE, encoding="utf-8")
        self.target = self.root / "dictionary" / "jmdict.sqlite3"

    def build(self, **kwargs):
        return dictionary_build.build(self.source, self.target, lambda *a, **k: None, **kwargs)

    def rows(self, path):
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        try:
            return {row["id"]: json.loads(row["data"])
                    for row in connection.execute("SELECT id, data FROM entries")}
        finally:
            connection.close()

    # ---- content ---------------------------------------------------------

    def test_the_xml_restrictions_survive_into_the_built_rows(self):
        self.build()
        entry = self.rows(DictionaryStore(self.target).path)["1414870"]
        readings = {reading["text"]: reading["restrictions"] for reading in entry["readings"]}
        self.assertEqual(readings["せいじん"], ["成人"])
        self.assertEqual(readings["たいじん"], ["大人"])
        self.assertEqual(readings["おとな"], [])
        magnanimity = next(s for s in entry["senses"] if "person of magnanimity" in s["gloss"])
        self.assertEqual(magnanimity["writtenRestrictions"], ["大人"])
        self.assertEqual(magnanimity["readingRestrictions"], ["たいじん"])
        self.assertEqual(magnanimity["notes"], ["archaic"])
        self.assertTrue(magnanimity["key"])

    def test_part_of_speech_entities_stay_as_codes(self):
        self.build()
        self.assertEqual(self.rows(DictionaryStore(self.target).path)["1578850"]["pos"], ["v5r"])

    def test_the_priority_marker_becomes_the_common_flag(self):
        self.build()
        entries = self.rows(DictionaryStore(self.target).path)
        self.assertTrue(entries["1578850"]["common"])
        self.assertFalse(entries["1414870"]["common"])

    # ---- publishing ------------------------------------------------------

    def test_a_build_is_published_as_one_version_directory(self):
        metadata = self.build()
        pointer = json.loads((self.target.parent / "current.json").read_text(encoding="utf-8"))
        version = self.target.parent / f"versions/{metadata['sourceSha256'][:32]}"
        self.assertEqual(pointer["path"], f"versions/{metadata['sourceSha256'][:32]}/dictionary.sqlite3")
        # The database and its SOURCES sidecar become current together, so they can
        # never describe different builds.
        for name in ("dictionary.sqlite3", "SOURCES.json", "SOURCES.md"):
            self.assertTrue((version / name).is_file(), name)
        self.assertEqual(DictionaryStore(self.target).path, version / "dictionary.sqlite3")

    def test_the_store_reads_the_pointer_rather_than_the_fixed_path(self):
        self.build()
        store = DictionaryStore(self.target)
        self.assertTrue(store.status()["available"])
        self.assertEqual(store.status()["entries"], "2")
        self.assertFalse(self.target.is_file(), "the fixed path is not where the data lives now")

    def test_a_broken_pointer_falls_back_instead_of_failing(self):
        self.build()
        (self.target.parent / "current.json").write_text("{not json", encoding="utf-8")
        store = DictionaryStore(self.target)
        # No usable pointer and no file at the nominal path: report unavailable, do not raise.
        self.assertFalse(store.status()["available"])

    def test_a_failed_build_leaves_the_previous_version_serving(self):
        first = self.build()
        store = DictionaryStore(self.target)
        self.source.write_text("<JMdict><entry><ent_seq>oops</ent_seq></entry></JMdict>", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.build()
        self.assertEqual(store.status()["sourceSha256"], first["sourceSha256"])
        self.assertEqual(store.status()["entries"], "2")

    def test_a_cancelled_build_leaves_the_previous_version_serving(self):
        first = self.build()
        store = DictionaryStore(self.target)
        with self.assertRaises(dictionary_build.Cancelled):
            self.build(cancelled=lambda: True)
        self.assertEqual(store.status()["sourceSha256"], first["sourceSha256"])

    def test_a_missing_full_text_index_degrades_and_says_so(self):
        class WithoutFts5:
            """A build on a SQLite without the FTS5 module compiled in."""

            def __init__(self, wrapped):
                self._wrapped = wrapped

            def execute(self, sql, *args, **kwargs):
                if "fts5" in str(sql).lower():
                    raise sqlite3.OperationalError("no such module: fts5")
                return self._wrapped.execute(sql, *args, **kwargs)

            def __getattr__(self, name):
                return getattr(self._wrapped, name)

        original = dictionary_build.sqlite3.connect
        dictionary_build.sqlite3.connect = lambda *a, **k: WithoutFts5(original(*a, **k))
        try:
            metadata = self.build()
        finally:
            dictionary_build.sqlite3.connect = original
        self.assertEqual(metadata["fts"], "none")
        status = DictionaryStore(self.target).status()
        self.assertTrue(status["available"], "exact and prefix lookup still work")
        self.assertTrue(status["degraded"])
        self.assertFalse(status["glossSearch"])
        self.assertIn("FTS5", status["degradedReason"])
        # And the lookup path still answers, without the gloss index.
        self.assertTrue(DictionaryStore(self.target).search("承る"))


class InstallJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.jobs = InstallJobs(Path(self.temp.name) / "dictionary" / "jmdict.sqlite3")

    def test_an_idle_manager_reports_idle(self):
        self.assertEqual(self.jobs.status()["status"], "idle")

    def test_a_job_records_its_stages_and_counters(self):
        release = threading.Event()
        reported = threading.Event()

        def worker(progress, _cancelled):
            progress("下载中", stage="download", bytes=1048576)
            progress("建立索引", stage="build", entries=1234)
            reported.set()
            release.wait(5)
            return {"entries": "1234"}

        started = self.jobs.start(worker)
        self.assertEqual(started["status"], "running")
        self.assertTrue(started["jobId"].startswith("dj_"))
        self.assertTrue(reported.wait(5), "the worker must get to report progress")
        mid = self.jobs.status()
        self.assertEqual(mid["stage"], "build")
        self.assertEqual(mid["bytes"], 1048576)
        self.assertEqual(mid["entriesProcessed"], 1234)
        release.set()
        self.jobs._thread.join(5)
        self.assertEqual(self.jobs.status()["status"], "complete")

    def test_a_second_start_joins_the_running_job(self):
        release = threading.Event()
        self.jobs.start(lambda progress, cancelled: (release.wait(5), {})[1])
        first = self.jobs.status()["jobId"]
        self.assertEqual(self.jobs.start(lambda p, c: {})["jobId"], first)
        release.set(); self.jobs._thread.join(5)

    def test_a_cancel_request_reaches_the_worker(self):
        observed = threading.Event()

        def worker(progress, cancelled):
            from dictionary_build import Cancelled
            for _ in range(500):
                if cancelled():
                    observed.set()
                    raise Cancelled("已按请求取消安装。")
            return {}

        self.jobs.start(worker)
        self.jobs.cancel()
        self.jobs._thread.join(5)
        self.assertTrue(observed.is_set())
        state = self.jobs.status()
        self.assertEqual(state["status"], "cancelled")
        self.assertTrue(state["resumable"])

    def test_cancelling_nothing_is_an_error_not_a_silent_success(self):
        with self.assertRaises(ValueError):
            self.jobs.cancel()

    def test_a_failure_records_its_code_and_stays_restartable(self):
        def worker(progress, cancelled):
            raise RuntimeError("网络中断")

        self.jobs.start(worker)
        self.jobs._thread.join(5)
        state = self.jobs.status()
        self.assertEqual(state["status"], "failed")
        self.assertEqual(state["errorCode"], "RuntimeError")
        self.assertTrue(state["resumable"])
        self.assertIn("原词典未改变", state["message"])

    def test_a_job_from_a_dead_process_is_reported_as_interrupted(self):
        # What a restart mid-download leaves behind: a file saying `running` and no worker.
        self.jobs._write({"jobId": "dj_old", "status": "running", "stage": "download",
                          "bytes": 42, "entriesProcessed": 0, "cancelRequested": False,
                          "startedAt": "2026-01-01T00:00:00+00:00"})
        state = self.jobs.status()
        self.assertEqual(state["status"], "interrupted")
        self.assertEqual(state["errorCode"], "interrupted")
        self.assertFalse(state["active"])
        self.assertTrue(state["resumable"])

    def test_a_finished_job_can_be_cleared_but_a_running_one_cannot(self):
        self.jobs._write({"jobId": "dj_done", "status": "complete", "stage": "complete"})
        self.assertEqual(self.jobs.clear()["status"], "idle")
        release = threading.Event()
        self.jobs.start(lambda progress, cancelled: (release.wait(5), {})[1])
        with self.assertRaises(ValueError):
            self.jobs.clear()
        release.set(); self.jobs._thread.join(5)


if __name__ == "__main__":
    unittest.main()
