"""Measure lexicon search latency at a given content-card scale (LEX-18/LEX-20, §9.3).

Not a test: it records numbers for an environment rather than asserting a threshold, so
a slow machine reports a slow result instead of failing a build.

    python scripts/lexicon_search_bench.py --cards 1000 --queries 200
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]

import lexicon_search  # noqa: E402
from lexicon_api import LexiconServices  # noqa: E402
from lexicon_store import LexiconStore  # noqa: E402
from local_backend import LearningStore, source_card_id  # noqa: E402

# A mix of shapes: exact headword, reading, romaji, gloss substring, and a miss.
QUERIES = ['承る', 'うけたまわる', 'uketamawaru', '恭听', '的', 'ない', 'zzzznope',
           'テスト', 'たべる', '文型']


def seed_cards(store: LearningStore, count: int) -> None:
    """Personal review cards, so the search runs against a populated database."""
    with store.atomic():
        for index in range(count):
            ref = f'user:bench-{index:06d}'
            store.connection.execute(
                """
                INSERT OR IGNORE INTO vocab
                    (id, term, reading, meaning, note, course_id, sentence_id, source_text,
                     tags, level, next_review_at, last_reviewed_at, created_at, updated_at,
                     entry_kind, source_ref, prompt_type, variant_key, card_payload_json)
                VALUES (?, ?, '', '', '', '', '', '', '[]', '', '', '', '', '', 'word', ?, 'recall', 'default', '{}')
                """,
                (source_card_id(ref, 'recall', 'default'), f'語{index}', ref),
            )
            store.connection.execute(
                'INSERT OR IGNORE INTO lex_user_entries VALUES (?,?,1,0,?)',
                (ref, json.dumps({'headword': f'語{index}', 'gloss': {'zh': f'测试释义{index}'}},
                                 ensure_ascii=False), '2026-01-01T00:00:00+00:00'),
            )


def run(cards: int, queries: int, lexicon: Path) -> dict:
    with tempfile.TemporaryDirectory() as directory:
        store = LearningStore(Path(directory) / 'bench.sqlite3')
        try:
            seed_cards(store, cards)
            services = LexiconServices(store, LexiconStore(lexicon))

            cold_start = time.perf_counter()
            lexicon_search.search(services, {'q': QUERIES[0], 'limit': '30'})
            cold = (time.perf_counter() - cold_start) * 1000

            samples = []
            for index in range(queries):
                query = QUERIES[index % len(QUERIES)]
                started = time.perf_counter()
                lexicon_search.search(services, {'q': query, 'limit': '30'})
                samples.append((time.perf_counter() - started) * 1000)
            samples.sort()
            return {
                'cards': cards, 'queries': queries,
                'dictionaryAvailable': services.dictionary.status()['available'],
                'indexedEntries': services.index.db.execute('SELECT COUNT(*) FROM entries').fetchone()[0],
                'coldMs': round(cold, 1),
                'medianMs': round(statistics.median(samples), 1),
                'p95Ms': round(samples[int(len(samples) * 0.95) - 1], 1),
                'maxMs': round(samples[-1], 1),
            }
        finally:
            store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cards', type=int, nargs='+', default=[1000, 5000, 10000])
    parser.add_argument('--queries', type=int, default=200)
    parser.add_argument('--lexicon', type=Path, default=ROOT / 'lexicon')
    args = parser.parse_args()
    for scale in args.cards:
        print(json.dumps(run(scale, args.queries, args.lexicon), ensure_ascii=False))


if __name__ == '__main__':
    main()
