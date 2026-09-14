import pytest
from pathlib import Path
from eju_bank.assets import AssetStore, clip_figure_from_pdf
from eju_bank.audio import parse_range_header, validate_audio_cues
from eju_bank.errors import MediaError

def test_asset_store(tmp_path):
    store = AssetStore(tmp_path / "media")
    data = b"test binary payload for figure"
    meta = store.put_bytes(data, mime_type="image/png", ext=".png")
    assert "assetId" in meta
    assert store.has(meta["assetId"])
    assert store.get_bytes(meta["assetId"]) == data

def test_clip_figure_from_pdf():
    pdf_path = Path("sources/2023令和5年第2回理科.pdf")
    if pdf_path.exists():
        data, w, h = clip_figure_from_pdf(pdf_path, 3, [0.31, 0.34, 0.77, 0.63], dpi=150)
        assert len(data) > 1000
        assert w > 0 and h > 0

def test_parse_range_header():
    s, e = parse_range_header("bytes=0-499", 1000)
    assert s == 0 and e == 499
    
    s, e = parse_range_header("bytes=500-", 1000)
    assert s == 500 and e == 999
    
    s, e = parse_range_header("bytes=-200", 1000)
    assert s == 800 and e == 999
    
    with pytest.raises(MediaError):
        parse_range_header("invalid", 1000)
    with pytest.raises(MediaError):
        parse_range_header("bytes=1500-2000", 1000)

def test_validate_audio_cues():
    cues = [
        {"cueId": "c1", "startMs": 1000, "endMs": 5000},
        {"cueId": "c2", "startMs": 6000, "endMs": 10000},
    ]
    issues = validate_audio_cues(cues, total_duration_ms=12000)
    assert len(issues) == 0
    
    issues_bad = validate_audio_cues([{"cueId": "c1", "startMs": 5000, "endMs": 15000}], total_duration_ms=10000)
    assert len(issues_bad) > 0


def test_probe_audio_rejects_corrupted_or_fake_file(tmp_path):
    from eju_bank.audio import probe_audio
    fake_mp3 = tmp_path / "fake.mp3"
    fake_mp3.write_text("This is plain text, not a valid audio file.")
    with pytest.raises(MediaError):
        probe_audio(fake_mp3)




from test_content_review import workspace

def test_crop_origin_matches_migrated_schema_and_survives_reopen(workspace):
    from eju_bank.assets import register_asset_origin
    from eju_bank.db import Database
    from eju_bank.source import source_file
    ws,db,sid=workspace
    path,manifest=ws.source(sid)
    data,width,height=clip_figure_from_pdf(source_file(manifest,path,'QUESTION_BOOKLET'),1,[.05,.05,.8,.3],dpi=150)
    asset=AssetStore(db.media_dir).put_bytes(data,mime_type='image/png',ext='.png')
    origin=register_asset_origin(db,asset['assetId'],sid,manifest['files'][0]['sha256'],1,[.05,.05,.8,.3],dpi=150)
    reopened=Database(db.path)
    try:
        row=reopened.connection.execute('SELECT * FROM asset_origins WHERE id=?',(origin,)).fetchone()
        assert row['source_id']==sid and row['role']=='QUESTION_BOOKLET'
        meta=reopened.connection.execute('SELECT width,height FROM assets WHERE id=?',(asset['assetId'],)).fetchone()
        assert (meta['width'],meta['height'])==(width,height)
    finally:reopened.close()


def test_asset_write_cannot_escape_via_symlink(tmp_path):
    import hashlib
    data=b'known-content';digest=hashlib.sha256(data).hexdigest()
    outside=tmp_path/'outside';outside.mkdir()
    store=AssetStore(tmp_path/'media');(store.root/digest[:2]).symlink_to(outside,target_is_directory=True)
    with pytest.raises(MediaError):store.put_bytes(data,mime_type='application/octet-stream',ext='.bin')
    assert not list(outside.iterdir())


def test_audio_cues_reject_boolean_times_and_do_not_mutate_input():
    cues=[{'cueId':'one','startMs':0,'endMs':1000},{'cueId':'two','startMs':500,'endMs':1400}]
    import copy
    before=copy.deepcopy(cues)
    assert any(i['code']=='cue.overlap' for i in validate_audio_cues(cues,2000))
    assert cues==before
    assert validate_audio_cues([{'cueId':'x','startMs':False,'endMs':True}],2000)
    assert validate_audio_cues(None,2000)
