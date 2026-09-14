from __future__ import annotations

import sys
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from build_pdf_course import build, classify_document, make_parser, resolve_vision_profile  # noqa: E402


def document(*pages: str) -> dict:
    return {"pages": [{"page": index, "markdown": text} for index, text in enumerate(pages, 1)]}


class DocumentClassificationTests(unittest.TestCase):
    def test_jlpt_paper_is_classified_as_exam_and_level_is_read(self) -> None:
        detected = classify_document(document(
            "日本語能力試験 N2\n問題1 文字・語彙\n問題2 文法\n読解\n聴解\n正解"
        ))
        self.assertEqual(detected["kind"], "exam")
        self.assertEqual(detected["level"], "N2")

    def test_weekly_grammar_book_is_classified_as_grammar(self) -> None:
        detected = classify_document(document(
            "第1週\n1日目\n文法 文型 接続 活用",
            "第1週\n2日目\n接続 文型",
        ))
        self.assertEqual(detected["kind"], "grammar")

    def test_weekly_vocabulary_book_is_not_misclassified_as_grammar(self) -> None:
        detected = classify_document(document(
            "第1週\n1日目\n語彙 単語 ことば",
            "第1週\n2日目\n語彙 単語",
        ))
        self.assertEqual(detected["kind"], "word")

    def test_ambiguous_document_fails_closed_to_plain_document(self) -> None:
        detected = classify_document(document("これは普通の短い資料です。"))
        self.assertEqual(detected["kind"], "document")
        self.assertEqual(detected["confidence"], "low")


class VisionProfileTests(unittest.TestCase):
    def test_named_profile_is_resolved_from_trusted_config(self) -> None:
        profile = resolve_vision_profile(
            {
                "visionProfiles": {
                    "local": {
                        "kind": "openai-vlm",
                        "baseUrl": "http://127.0.0.1:8102/v1/",
                        "model": "ocr-model",
                    }
                }
            },
            "local",
        )
        self.assertEqual(profile.base_url, "http://127.0.0.1:8102/v1")
        self.assertEqual(profile.model, "ocr-model")

    def test_unknown_or_non_http_profile_is_rejected(self) -> None:
        with self.assertRaises(SystemExit):
            resolve_vision_profile({"visionProfiles": {}}, "missing")
        with self.assertRaises(SystemExit):
            resolve_vision_profile(
                {"visionProfiles": {"bad": {"baseUrl": "file:///etc/passwd", "model": "x"}}},
                "bad",
            )


class _FakeVisionHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        return

    def do_GET(self):  # noqa: N802
        body = json.dumps({"data": [{"id": "fake-vlm"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        json.loads(self.rfile.read(length))
        markdown = "普通の学習資料です。" * 10
        body = json.dumps({"choices": [{"message": {"content": markdown}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class PdfBuildIntegrationTests(unittest.TestCase):
    def test_one_page_pdf_runs_to_a_reviewable_document_artifact(self) -> None:
        try:
            import pymupdf
        except ImportError:
            self.skipTest("pymupdf not installed")

        with tempfile.TemporaryDirectory(prefix="pdf-workbench-") as raw:
            root = Path(raw)
            pdf = root / "source.pdf"
            doc = pymupdf.open()
            page = doc.new_page()
            page.insert_text((72, 72), "local pipeline integration test")
            doc.save(pdf)
            doc.close()

            server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeVisionHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(server.server_close)
            self.addCleanup(lambda: thread.join(timeout=5))
            self.addCleanup(server.shutdown)

            config = root / "providers.json"
            config.write_text(
                json.dumps({
                    "visionProfiles": {
                        "fake": {
                            "kind": "openai-vlm",
                            "baseUrl": f"http://127.0.0.1:{server.server_address[1]}/v1",
                            "model": "fake-vlm",
                        }
                    }
                }),
                encoding="utf-8",
            )
            result_path = root / "build-result.json"
            args = make_parser().parse_args([
                "--pdf", str(pdf),
                "--out", str(root / "artifact"),
                "--result", str(result_path),
                "--config", str(config),
                "--source-name", "资料.pdf",
                "--kind", "document",
                "--vision-profile", "fake",
            ])
            result = build(args)
            self.assertTrue(result["reviewRequired"])
            self.assertEqual(result["kind"], "document")
            self.assertEqual(result["ocr"]["usedProfiles"], ["fake"])
            self.assertTrue((root / "artifact" / "ocr" / "document.json").is_file())
            self.assertEqual(json.loads(result_path.read_text())["status"], "needs_review")

    def test_exam_printed_answer_evidence_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ocr_dir = root / "ocr"
            ocr_dir.mkdir()
            draft = root / "draft"
            draft.mkdir()

            doc_content = {
                "pages": [
                    {
                        "page": 1,
                        "pageType": "content",
                        "markdown": "問題1 1. 本を読む\n1 ほん 2 ぼん 3 もん 4 ぽん",
                    },
                    {
                        "page": 2,
                        "pageType": "answers",
                        "markdown": "# 正解一覧\n1 1\n2 3\n3 2\n4 4\n5 1\n",
                    },
                ]
            }
            (ocr_dir / "document.json").write_text(json.dumps(doc_content), encoding="utf-8")
            from build_pdf_course import _try_extract_printed_answer_key
            evidence = _try_extract_printed_answer_key(ocr_dir, draft)
            self.assertIsNotNone(evidence)
            self.assertEqual(evidence["source"], "printed_answer_table")
            self.assertEqual(evidence["page"], 2)
            self.assertEqual(evidence["extractedCount"], 5)
            self.assertTrue((draft / "answer-evidence.json").is_file())
            self.assertTrue((draft / "answer-key.txt").is_file())
            self.assertIn("written 1-5 1 13241", (draft / "answer-key.txt").read_text(encoding="utf-8"))

    def test_extraction_empty_quarantined_without_review_required(self) -> None:
        try:
            import pymupdf
        except ImportError:
            self.skipTest("pymupdf not installed")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "empty_grammar.pdf"
            doc = pymupdf.open()
            page = doc.new_page()
            page.insert_text((72, 72), "Sample page with no grammar entries")
            doc.save(pdf)
            doc.close()

            server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeVisionHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(lambda: thread.join(timeout=5))
            self.addCleanup(server.shutdown)

            config = root / "providers.json"
            config.write_text(
                json.dumps({
                    "visionProfiles": {
                        "fake": {
                            "kind": "openai-vlm",
                            "baseUrl": f"http://127.0.0.1:{server.server_address[1]}/v1",
                            "model": "fake-vlm",
                        }
                    }
                }),
                encoding="utf-8",
            )
            result_path = root / "build-result.json"
            args = make_parser().parse_args([
                "--pdf", str(pdf),
                "--out", str(root / "artifact"),
                "--result", str(result_path),
                "--config", str(config),
                "--source-name", "empty_grammar.pdf",
                "--kind", "grammar",
                "--vision-profile", "fake",
            ])
            result = build(args)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["outcomeCode"], "extraction_empty")
            self.assertFalse(result["reviewRequired"])
            self.assertEqual(json.loads(result_path.read_text())["status"], "failed")


if __name__ == "__main__":
    unittest.main()
