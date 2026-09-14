"""Fixtures for the vocabulary / grammar pack suite.

The fixture is a grammar pack because grammar is what Phase A ships, and because it is
the harder of the two shapes: it carries connections, cloze cards and confusables, none
of which a word entry has. A word entry is added by ``make_word_pack`` for the rules that
are about the tagged union rather than about grammar.

No text here is copied from the textbook: these are invented patterns in the same shape,
so the fixtures can live in version control while real packs cannot.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from lexicon_schema import prepare_pack  # noqa: E402

PACK_ID = "N2-grammar-fixture"


def make_pack(**overrides: Any) -> dict[str, Any]:
    """A clean grammar pack that passes its audit with no issues at all."""
    pack: dict[str, Any] = {
        "packId": PACK_ID,
        "kind": "grammar",
        "level": "N2",
        "title": "テスト文法パック",
        "attribution": {
            "sourceType": "textbook-ocr",
            "publisher": "テスト出版",
            "sourceSha256": "0" * 64,
            "redistributable": False,
        },
        "units": [
            {"unitId": "w1d1", "label": "第1週 1日目", "title": "テスト", "entryIds": ["e0001", "e0002"]},
            {"unitId": "w1d2", "label": "第1週 2日目", "title": "テスト2", "entryIds": ["e0003"]},
        ],
        "entries": [
            _grammar_entry(
                "e0001",
                headword="〜てたまらない",
                connection=[
                    {"slot": "i-adjective", "form": "くて", "display": "イAくて"},
                    {"slot": "na-adjective", "form": "で", "display": "ナAで"},
                    {"slot": "verb-desiderative", "form": "たくて", "display": "Vたくて"},
                ],
                unit="w1d1",
            ),
            _grammar_entry("e0002", headword="〜てならない", unit="w1d1"),
            _grammar_entry("e0003", headword="〜がち", unit="w1d2"),
        ],
    }
    pack.update(copy.deepcopy(overrides))
    return prepare_pack(pack)


def _grammar_entry(
    key: str,
    *,
    headword: str,
    unit: str,
    connection: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    sentence = f"これは{headword.lstrip('〜')}文です。"
    core = headword.lstrip("〜")
    marked = sentence.replace(core, f"⟦{core}⟧", 1)
    return {
        "entryKey": key,
        "kind": "grammar",
        "level": "N2",
        "headword": headword,
        "unitId": unit,
        "gloss": {"zh": "测试释义", "en": "test gloss"},
        "grammar": {
            "connection": connection or [{"slot": "verb", "form": "て", "display": "Vて"}],
            "notes": "テスト用の説明。",
            "confusables": [],
        },
        "examples": [
            {
                "exampleId": "ex1",
                "ja": sentence,
                "zh": "这是一个测试句子。",
                "en": "This is a test sentence.",
                "paraphrase": "テスト",
            }
        ],
        "cardTemplates": [
            {"variantKey": "default", "promptType": "recall"},
            {"variantKey": "cloze-ex1", "promptType": "cloze", "exampleId": "ex1", "markedJa": marked},
        ],
        "source": {"pdfPages": [18], "blockIds": ["p0018-b2"]},
        "flags": [],
    }


def make_word_pack() -> dict[str, Any]:
    """The other half of the tagged union, for the rules that must cover both kinds."""
    return prepare_pack(
        {
            "packId": "N2-words-fixture",
            "kind": "word",
            "level": "N2",
            "title": "テスト単語パック",
            "attribution": {"sourceType": "textbook-ocr", "publisher": "テスト出版", "redistributable": False},
            "units": [{"unitId": "u1", "label": "第1課", "title": "テスト", "entryIds": ["e0001"]}],
            "entries": [
                {
                    "entryKey": "e0001",
                    "kind": "word",
                    "level": "N2",
                    "headword": "承る",
                    "unitId": "u1",
                    "gloss": {"zh": "恭听、接受", "en": "to hear, to accept"},
                    "dictRef": {
                        "source": "jmdict",
                        "entSeq": 1610980,
                        "writtenForm": "承る",
                        "reading": "うけたまわる",
                        "senseIndexes": [0, 1],
                    },
                    "snapshot": {"reading": "うけたまわる", "pos": ["v5r", "vt"], "glossEn": ["to hear"]},
                    "word": {"writtenForms": ["承る", "うけたまわる"], "commonness": "ichi1"},
                    "examples": [
                        {"exampleId": "ex1", "ja": "ご意見を承ります。", "zh": "恭听您的意见。"}
                    ],
                    "cardTemplates": [{"variantKey": "default", "promptType": "recall"}],
                    "source": {"pdfPages": [4]},
                    "flags": [],
                }
            ],
        }
    )


def make_meta() -> dict[str, Any]:
    """``pack-meta.json`` as the importer reads it."""
    return {
        "packId": PACK_ID,
        "kind": "grammar",
        "level": "N2",
        "title": "テスト文法パック",
        "attribution": {
            "sourceType": "textbook-ocr",
            "publisher": "テスト出版",
            "sourceSha256": "0" * 64,
            "redistributable": False,
        },
    }
