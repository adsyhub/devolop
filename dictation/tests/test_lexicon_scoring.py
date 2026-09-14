import json
from pathlib import Path
import unittest
from lexicon_exercise import score

class SharedScoringTests(unittest.TestCase):
    def test_shared_browser_vectors(self):
        cases=json.loads((Path(__file__).parent/'fixtures/lexicon_scoring_cases.json').read_text())
        for case in cases:
            with self.subTest(case=case['name']):
                if case.get('error'):
                    with self.assertRaises(ValueError):score(case['question'],case['answer'],**case['options'])
                else:
                    result=score(case['question'],case['answer'],**case['options'])
                    self.assertEqual({k:result[k] for k in case['expected']},case['expected'])
