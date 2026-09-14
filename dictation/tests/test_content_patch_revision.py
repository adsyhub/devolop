import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from content_patch import apply_content_patch, sentences_digest
from course_schema import content_revision


class ContentPatchRevisionTests(unittest.TestCase):
    def test_source_text_patch_updates_content_revision_but_preserves_sentence_id(self):
        sentence = {
            "id": "s_0123456789abcdef01234567",
            "startTime": 1.0,
            "endTime": 2.0,
            "jaText": "国際を買う",
            "sourceText": "国際を買う",
            "zhTranslation": "购买国债",
            "translationText": "购买国债",
            "explanationText": "需要校对。",
            "contentType": "dialogue",
            "practiceEligible": True,
        }
        manifest = {
            "sourceLanguage": "ja",
            "contentRevision": content_revision([sentence], "ja"),
            "sentences": [sentence],
        }
        original_revision = manifest["contentRevision"]
        patch = {
            "schemaVersion": 1,
            "sourceSentencesDigest": sentences_digest(manifest["sentences"]),
            "operations": [
                {
                    "type": "replace_range",
                    "startIndex": 0,
                    "endIndex": 0,
                    "expectedStartTime": 1.0,
                    "expectedEndTime": 2.0,
                    "items": [
                        {
                            "startTime": 1.0,
                            "endTime": 2.0,
                            "jaText": "国債を買う",
                        }
                    ],
                }
            ],
        }

        result = apply_content_patch(copy.deepcopy(manifest), patch, patch_name="repair.json")

        self.assertEqual(result["sentences"][0]["id"], sentence["id"])
        self.assertNotEqual(result["contentRevision"], original_revision)
        self.assertEqual(result["contentRevision"], content_revision(result["sentences"], "ja"))


if __name__ == "__main__":
    unittest.main()
