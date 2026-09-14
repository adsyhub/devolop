from __future__ import annotations

import tempfile
from pathlib import Path

from eju_bank.assets import AssetStore
from scripts.build_and_publish_all import build_japanese_forms, ingest_booklet_pages, load_session_ocr_data


def test_build_japanese_forms_with_ocr_data():
    manifest = {
        "sourceId": "src_test_ja",
        "files": [],
        "rights": {"status": "PUBLIC_LICENSED"},
    }
    page_assets = {p: f"asset_p{p:02d}" for p in range(1, 50)}
    page_ocr_data = {
        6: {
            "passage_ast": [{"type": "paragraph", "value": "テスト本文：琵琶湖の自然環境について。"}],
            "stem": "下線部に関する説明として最も適当なものはどれか。",
            "options": {
                "1": "選択肢Aの記述",
                "2": "選択肢Bの記述",
                "3": "選択肢Cの記述",
                "4": "選択肢Dの記述",
            },
        },
        9: {
            "passage_ast": [{"type": "paragraph", "value": "ヒトは白目をもって目立つようにできている。"}],
            "figures": [
                {
                    "assetId": "asset_eye_crop",
                    "sourceBbox": [0.1381, 0.5112, 0.5985, 0.6305],
                    "alt": "読解 第9ページ 挿絵図版",
                }
            ],
            "stem": "IV 下線部「この心理」とありますが、どんな心理を指していますか。",
            "options": {
                "1": "選択肢1",
                "2": "選択肢2",
                "3": "選択肢3",
                "4": "選択肢4",
            },
        },
    }

    forms = build_japanese_forms(
        session_code="2023-1",
        manifest=manifest,
        page_count=49,
        page_assets=page_assets,
        page_ocr_data=page_ocr_data,
    )

    assert len(forms) == 1
    groups = {g["groupCode"]: g for g in forms[0]["groups"]}
    assert "READING" in groups
    assert "LISTENING" in groups
    assert "WRITING" in groups

    # Reading material for P6 has OCR text only -> should contain paragraph and NO figure
    reading_mats = {m["localKey"]: m for m in groups["READING"]["materials"]}
    assert "read-mat-p06" in reading_mats
    p6_ast = reading_mats["read-mat-p06"]["contentAst"]
    assert any(n["type"] == "paragraph" and "テスト本文" in n["value"] for n in p6_ast)
    assert not any(n["type"] == "figure" for n in p6_ast)

    # Reading material for P9 has both OCR text and cropped figure -> should contain BOTH paragraph AND figure
    assert "read-mat-p09" in reading_mats
    p9_ast = reading_mats["read-mat-p09"]["contentAst"]
    assert any(n["type"] == "paragraph" and "白目" in n["value"] for n in p9_ast)
    assert any(n["type"] == "figure" and n["assetId"] == "asset_eye_crop" for n in p9_ast)

    # Reading material for P7 has NO OCR text -> falls back to figure
    assert "read-mat-p07" in reading_mats
    p7_ast = reading_mats["read-mat-p07"]["contentAst"]
    assert any(n["type"] == "figure" and n["assetId"] == "asset_p07" for n in p7_ast)

    # Question 1 should have real stem and options
    q1 = groups["READING"]["questions"][0]
    assert "下線部に関する説明" in q1["stemAst"][0]["value"]
    assert len(q1["options"]) == 4
    assert q1["options"][0]["contentAst"][0]["value"] == "選択肢Aの記述"
    assert q1["options"][1]["contentAst"][0]["value"] == "選択肢Bの記述"


def test_ingest_booklet_pages_prefers_remastered(tmp_path: Path):
    store = AssetStore(tmp_path / "media")
    work_dir = tmp_path / "session"
    qb_render = work_dir / "renders" / "question_booklet" / "qb_hash" / "page-0001"
    qb_render.mkdir(parents=True, exist_ok=True)
    (qb_render / "full-180dpi.png").write_bytes(b"raw_scanned_image")

    remaster_dir = work_dir / "remastered_renders"
    remaster_dir.mkdir(parents=True, exist_ok=True)
    (remaster_dir / "remastered_p0001.png").write_bytes(b"remastered_pure_white_image")

    assets = ingest_booklet_pages(work_dir, store, prefer_remastered=True)
    assert 1 in assets
    # Asset should match remastered content hash
    import hashlib
    expected_hash = hashlib.sha256(b"remastered_pure_white_image").hexdigest()
    assert assets[1] == expected_hash
