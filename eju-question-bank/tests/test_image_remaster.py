from __future__ import annotations

from pathlib import Path
import numpy as np
from PIL import Image

from eju_bank.image_remaster import (
    clean_and_whiten_image,
    crop_and_whiten_figure,
    crop_tight_bbox,
    detect_reading_illustrations,
    remaster_image_file,
    render_table_to_svg,
)
from eju_bank.ocr.glm_ocr_worker import GlmOcrWorker


def test_clean_and_whiten_image(tmp_path: Path):
    arr = np.full((200, 200), 210, dtype=np.uint8)
    arr[95:105, 50:150] = 30
    img = Image.fromarray(arr)

    cleaned = clean_and_whiten_image(img)
    arr_out = np.array(cleaned)

    assert arr_out[10, 10] >= 240
    assert arr_out[100, 100] < 100


def test_crop_tight_bbox():
    arr = np.full((300, 300), 255, dtype=np.uint8)
    arr[120:180, 120:180] = 20
    img = Image.fromarray(arr)

    cropped = crop_tight_bbox(img, margin=10)
    assert cropped.width < 300
    assert cropped.height < 300
    assert 60 <= cropped.width <= 120
    assert 60 <= cropped.height <= 120


def test_remaster_image_file(tmp_path: Path):
    src = tmp_path / "raw.png"
    out = tmp_path / "remastered.png"

    arr = np.full((150, 150), 220, dtype=np.uint8)
    arr[50:100, 50:100] = 10
    Image.fromarray(arr).save(str(src))

    remaster_image_file(src, out, tight_crop=True)
    assert out.exists()
    assert out.stat().st_size > 0


def test_render_table_to_svg():
    rows = [
        ["区分", "1回目", "2回目"],
        ["項目A", "10.5", "20.3"],
        ["項目B", "15.0", "25.2"],
    ]
    svg = render_table_to_svg(rows, title="実験データ測定結果")
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert "実験データ測定結果" in svg
    assert "項目A" in svg
    assert "20.3" in svg


def test_parse_reading_page():
    raw_ocr = """
山本登志哉「発達心理学研究」より

人は他者との関わりの中で自己を形成していく。
幼児期の模倣行動は、単なる真似ではなく共感の芽生えである。

問1 本文の内容として、最も適当なものはどれか。
1 他者の行動を批判的に観察すること
2 模倣を通じて共感的な他者理解を深めること
3 生まれつきの自己主張を貫くこと
4 集団生活を避けて個別に行動すること
"""
    worker = GlmOcrWorker(device="cpu")
    parsed = worker.parse_reading_page(raw_ocr)

    assert len(parsed["passage_ast"]) >= 1
    assert "山本登志哉" in parsed["passage_ast"][0]["value"]
    assert "問1" in (parsed["stem"] or "")
    assert len(parsed["options"]) == 4
    assert parsed["options"]["1"] == "他者の行動を批判的に観察すること"
    assert parsed["options"]["2"] == "模倣を通じて共感的な他者理解を深めること"


def test_detect_reading_illustrations():
    # Construct a synthetic page: 800x1200 with small text lines and one large illustration block
    page = np.full((1200, 800), 255, dtype=np.uint8)
    # Simulate text lines (height ~20px, small glyphs)
    for y in range(100, 400, 40):
        page[y : y + 20, 100:700] = 50

    # Simulate an illustration block with drawing strokes (150x150)
    page[600:750, 300:450] = 40
    # Simulate a leader line from (300, 650) to (200, 600)
    for step in range(50):
        page[650 - step, 300 - step * 2] = 20
    # Simulate label "*説明"
    page[590:610, 150:220] = 30

    bboxes = detect_reading_illustrations(page)
    assert len(bboxes) == 1
    x0, y0, x1, y1 = bboxes[0]
    # The detected bounding box should encompass the label, pointer, and figure core
    assert x0 <= 160
    assert y0 <= 600
    assert x1 >= 440
    assert y1 >= 740


def test_crop_and_whiten_figure():
    page = np.full((500, 500), 220, dtype=np.uint8)
    page[200:300, 200:300] = 30
    img = Image.fromarray(page)

    cropped = crop_and_whiten_figure(img, (200, 200, 300, 300), padding=10)
    assert isinstance(cropped, Image.Image)
    assert cropped.width == 120
    assert cropped.height == 120
    arr = np.array(cropped)
    # Background should be pure white
    assert arr[5, 5] >= 240
    # Center stroke should be dark
    assert arr[60, 60] < 100

