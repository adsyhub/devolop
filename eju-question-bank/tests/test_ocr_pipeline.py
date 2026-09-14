from __future__ import annotations

from pathlib import Path

from eju_bank.constants import PAGE_CONTRACT_VERSION
from eju_bank.db import Database
from eju_bank.ocr.pipeline import compute_ocr_cache_key, extract_pages
from eju_bank.source import create_source_manifest
from eju_bank.util import sha256_file, write_json


class FakeProvider:
    def __init__(self, model: str = "fake-vlm-v1", fail_pages: set[int] | None = None) -> None:
        self.model = model
        self.fail_pages = fail_pages or set()

    def identity(self) -> dict:
        return {
            "providerType": "fake",
            "model": self.model,
            "revision": "UNKNOWN",
            "imageMode": "full",
        }

    def transcribe(self, *, images, prompt, page, role):
        assert images
        assert "EJU" in prompt
        if page in self.fail_pages:
            # Return an invalid contract with mismatching coverage regions
            return {
                "schemaVersion": PAGE_CONTRACT_VERSION,
                "page": page,
                "sourceFileRole": role,
                "blocks": [],
                "coverage": {
                    "inkRegions": 1,
                    "accountedRegions": 0,
                    "regionIds": ["r1"],
                    "accountedRegionIds": [],
                },
                "issues": [],
            }
        return {
            "schemaVersion": PAGE_CONTRACT_VERSION,
            "page": page,
            "sourceFileRole": role,
            "blocks": [
                {
                    "kind": "ignored",
                    "reason": "test page",
                    "bbox": [0.0, 0.0, 1.0, 1.0],
                }
            ],
            "coverage": {
                "inkRegions": 1,
                "accountedRegions": 1,
                "regionIds": ["r1"],
                "accountedRegionIds": ["r1"],
            },
            "issues": [],
        }


def _setup_test_source(tmp_path: Path, num_pages: int = 1):
    question = tmp_path / "q.pdf"
    question.write_bytes(b"%PDF-1.4 mock")
    manifest_path = tmp_path / "manifest.json"
    manifest = create_source_manifest(
        session="2023-2", subject="SCIENCE", language="ja", syllabus_version="2015",
        question_booklet=question, answer_key=None, rights_status="PRIVATE_STUDY",
        rights_note="test", output_path=manifest_path,
    )
    render_root = tmp_path / "renders"
    pages_meta = []
    for p in range(1, num_pages + 1):
        image = render_root / f"question_booklet/page-{p:04d}/full-180dpi.png"
        image.parent.mkdir(parents=True, exist_ok=True)
        image.write_bytes(f"page-{p}-bytes".encode("utf-8"))
        pages_meta.append({
            "page": p,
            "full": {"path": str(image.relative_to(render_root)).replace("\\", "/"), "sha256": sha256_file(image)},
            "tiles": [],
        })
    index_path = render_root / "render-index-question_booklet.json"
    write_json(index_path, {
        "schemaVersion": 1,
        "sourceId": manifest["sourceId"],
        "sourceHash": manifest["files"][0]["sha256"],
        "role": "QUESTION_BOOKLET",
        "settings": {"fullDpi": 180, "tileDpi": 320},
        "pages": pages_meta,
    })
    return manifest_path, index_path


def test_extract_is_resumable(tmp_path: Path) -> None:
    manifest_path, index_path = _setup_test_source(tmp_path, num_pages=1)
    out = tmp_path / "pages"
    first = extract_pages(manifest_path=manifest_path, render_index_path=index_path, output_dir=out, provider=FakeProvider())
    second = extract_pages(manifest_path=manifest_path, render_index_path=index_path, output_dir=out, provider=FakeProvider())
    assert first["status"] == "passed"
    assert second["pages"][0]["cached"] is True


def test_compute_ocr_cache_key():
    key1 = compute_ocr_cache_key(
        source_hash="sha_src",
        page_number=1,
        role="QUESTION_BOOKLET",
        image_hashes=["sha_img1"],
        render_profile={"dpi": 200},
        provider_identity={"providerType": "fake", "model": "m1"},
        prompt_hash="sha_prompt1",
    )
    key2 = compute_ocr_cache_key(
        source_hash="sha_src",
        page_number=1,
        role="QUESTION_BOOKLET",
        image_hashes=["sha_img1"],
        render_profile={"dpi": 200},
        provider_identity={"providerType": "fake", "model": "m1"},
        prompt_hash="sha_prompt1",
    )
    assert key1 == key2

    # Different prompt produces different key
    key3 = compute_ocr_cache_key(
        source_hash="sha_src",
        page_number=1,
        role="QUESTION_BOOKLET",
        image_hashes=["sha_img1"],
        render_profile={"dpi": 200},
        provider_identity={"providerType": "fake", "model": "m1"},
        prompt_hash="sha_prompt2",
    )
    assert key1 != key3


def test_extract_with_pages_filter_and_db(tmp_path: Path) -> None:
    manifest_path, index_path = _setup_test_source(tmp_path, num_pages=3)
    out = tmp_path / "pages"
    db = Database(tmp_path / "eju.db")

    # Only extract page 2
    res = extract_pages(
        manifest_path=manifest_path,
        render_index_path=index_path,
        output_dir=out,
        provider=FakeProvider(),
        pages=[2],
        database=db,
    )
    assert len(res["pages"]) == 1
    assert res["pages"][0]["page"] == 2
    assert (out / "p0002-question_booklet.json").exists()
    assert not (out / "p0001-question_booklet.json").exists()

    # Check database tracking
    runs = db.connection.execute("SELECT * FROM extraction_runs").fetchall()
    assert len(runs) == 1
    attempts = db.connection.execute("SELECT * FROM extraction_page_attempts").fetchall()
    assert len(attempts) == 1
    assert attempts[0]["page_number"] == 2
    assert attempts[0]["status"] == "SUCCEEDED"
    db.close()


def test_extract_retry_failed(tmp_path: Path) -> None:
    manifest_path, index_path = _setup_test_source(tmp_path, num_pages=2)
    out = tmp_path / "pages"

    # Run 1: Page 2 fails
    provider1 = FakeProvider(fail_pages={2})
    res1 = extract_pages(
        manifest_path=manifest_path,
        render_index_path=index_path,
        output_dir=out,
        provider=provider1,
    )
    assert res1["status"] == "failed"
    assert res1["pages"][0]["status"] == "passed"
    assert res1["pages"][1]["status"] == "failed"

    # Run 2: Without retry_failed, cached failed result is kept
    res2 = extract_pages(
        manifest_path=manifest_path,
        render_index_path=index_path,
        output_dir=out,
        provider=FakeProvider(),  # fixed provider
        retry_failed=False,
    )
    assert res2["pages"][1]["cached"] is True

    # Run 3: With retry_failed, page 2 is re-extracted and passes, while page 1 stays cached
    res3 = extract_pages(
        manifest_path=manifest_path,
        render_index_path=index_path,
        output_dir=out,
        provider=FakeProvider(),
        retry_failed=True,
    )
    assert res3["status"] == "passed"
    assert res3["pages"][0]["cached"] is True
    assert res3["pages"][1]["cached"] is False
    assert res3["pages"][1]["status"] == "passed"


def test_cache_sidecar_does_not_become_a_page(tmp_path):
    from eju_bank.page_contract import load_page_contracts
    manifest, index = _setup_test_source(tmp_path)
    out = tmp_path / 'pages'
    extract_pages(manifest_path=manifest, render_index_path=index, output_dir=out, provider=FakeProvider())
    assert len(load_page_contracts(out)) == 1


def test_stale_render_and_wrong_model_page_are_rejected(tmp_path):
    import pytest
    from eju_bank.errors import ContractError
    from eju_bank.util import load_json
    manifest, index = _setup_test_source(tmp_path)
    data = load_json(index); data['sourceHash'] = '0' * 64; write_json(index, data)
    with pytest.raises(ContractError, match='source hash'):
        extract_pages(manifest_path=manifest, render_index_path=index, output_dir=tmp_path/'pages', provider=FakeProvider())
    data['sourceHash'] = load_json(manifest)['files'][0]['sha256']; write_json(index,data)
    class WrongPage(FakeProvider):
        def transcribe(self, **kwargs):
            result = super().transcribe(**kwargs); result['page'] = 2; return result
    result = extract_pages(manifest_path=manifest, render_index_path=index, output_dir=tmp_path/'pages', provider=WrongPage())
    assert result['status'] == 'failed'
    assert not (tmp_path/'pages/p0001-question_booklet.json').exists()
    (index.parent/data['pages'][0]['full']['path']).write_bytes(b'changed')
    result = extract_pages(manifest_path=manifest, render_index_path=index, output_dir=tmp_path/'pages', provider=FakeProvider())
    assert result['status'] == 'failed'


# ── F13：缓存必须绑定它的输入 ────────────────────────────────────────────────

def test_ocr_cache_is_not_reused_across_models(tmp_path):
    """换了模型还沿用旧缓存，等于把另一次运行的产物当成本次的结果。"""
    from eju_bank.ocr.local_vision import _has_reading, cache_identity
    from eju_bank.util import write_json

    image = tmp_path / "p0001.png"
    image.write_bytes(b"fake-png-bytes")
    cache = tmp_path / "p0001.json"

    old_model = cache_identity(image, "model-a", "question_booklet")
    write_json(cache, {"raw_text": "读到的内容", **old_model})

    assert _has_reading(cache, "question_booklet", old_model), "同样的输入应当复用"
    new_model = cache_identity(image, "model-b", "question_booklet")
    assert not _has_reading(cache, "question_booklet", new_model), "换了模型不能复用"


def test_ocr_cache_is_not_reused_after_the_page_is_re_rendered(tmp_path):
    """原页重新渲染过，旧的识别结果说的是另一张图。"""
    from eju_bank.ocr.local_vision import _has_reading, cache_identity
    from eju_bank.util import write_json

    image = tmp_path / "p0001.png"
    image.write_bytes(b"first-render")
    cache = tmp_path / "p0001.json"
    write_json(cache, {"raw_text": "读到的内容",
                       **cache_identity(image, "model-a", "question_booklet")})

    image.write_bytes(b"second-render-different-bytes")
    expected = cache_identity(image, "model-a", "question_booklet")
    assert not _has_reading(cache, "question_booklet", expected)


def test_a_legacy_cache_without_provenance_is_still_reused(tmp_path):
    """这套机制之前留下的缓存没有来历记录。把它们一律作废等于整库重跑 OCR。"""
    from eju_bank.ocr.local_vision import _has_reading, cache_identity
    from eju_bank.util import write_json

    image = tmp_path / "p0001.png"
    image.write_bytes(b"bytes")
    cache = tmp_path / "p0001.json"
    write_json(cache, {"raw_text": "旧缓存，没有记来历"})
    assert _has_reading(cache, "question_booklet",
                        cache_identity(image, "model-a", "question_booklet"))
