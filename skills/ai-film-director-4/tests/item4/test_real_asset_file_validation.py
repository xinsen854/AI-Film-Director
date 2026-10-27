from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from build_exports import _verify_delivery_gate

spec = importlib.util.spec_from_file_location('item3_helpers', ROOT / 'tests' / 'item3' / 'test_final_hard_qc.py')
helpers = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(helpers)
make_series_root = helpers.make_series_root
write_asset_library = helpers.write_asset_library
dump = helpers.dump


def _record(root: Path) -> dict:
    path = root / 'assets' / 'ASSET_LIBRARY.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    return data['ASSET_LIBRARY']['character_assets'][0]


def _update_record(root: Path, **changes) -> dict:
    path = root / 'assets' / 'ASSET_LIBRARY.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    record = data['ASSET_LIBRARY']['character_assets'][0]
    record.update(changes)
    dump(path, data)
    return record


def _real_png(root: Path, name: str = 'A001_主角_人物母板_V01.png', size=(8, 6)) -> tuple[Path, dict]:
    path = root / 'assets' / 'generated' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new('RGB', size, 'white').save(path, format='PNG')
    raw = path.read_bytes()
    return path, {
        'file_size': len(raw),
        'width': size[0],
        'height': size[1],
        'mime_type': 'image/png',
        'sha256': hashlib.sha256(raw).hexdigest(),
    }


def test_generated_status_cannot_point_to_missing_file(tmp_path: Path):
    root = make_series_root(tmp_path)
    write_asset_library(root, mode='core_assets', status='GENERATED')
    _update_record(root, image_file='assets/generated/not-there.png')
    with pytest.raises(ValueError, match='ASSET_FILE_INVALID|资产|文件'):
        _verify_delivery_gate(root)


def test_fake_png_bytes_cannot_masquerade_as_generated_asset(tmp_path: Path):
    root = make_series_root(tmp_path)
    write_asset_library(root, mode='core_assets', status='GENERATED')
    path = root / 'assets' / 'generated' / 'A001_主角_人物母板_V01.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'not a real png')
    raw = path.read_bytes()
    _update_record(
        root,
        image_file='assets/generated/A001_主角_人物母板_V01.png',
        file_size=len(raw), width=8, height=6, mime_type='image/png',
        sha256=hashlib.sha256(raw).hexdigest(),
    )
    with pytest.raises(ValueError, match='ASSET_FILE_INVALID|解码|图片'):
        _verify_delivery_gate(root)


def test_generated_asset_path_cannot_escape_generated_directory(tmp_path: Path):
    root = make_series_root(tmp_path)
    write_asset_library(root, mode='core_assets', status='GENERATED')
    outside = tmp_path / 'outside.png'
    Image.new('RGB', (8, 6), 'white').save(outside, format='PNG')
    _update_record(root, image_file=str(outside))
    with pytest.raises(ValueError, match='ASSET_FILE_INVALID|路径|generated'):
        _verify_delivery_gate(root)


def test_generated_asset_requires_recorded_file_metadata(tmp_path: Path):
    root = make_series_root(tmp_path)
    write_asset_library(root, mode='core_assets', status='GENERATED')
    _real_png(root)
    _update_record(root, image_file='assets/generated/A001_主角_人物母板_V01.png')
    with pytest.raises(ValueError, match='file_size|width|height|mime_type|sha256|验证字段'):
        _verify_delivery_gate(root)


@pytest.mark.parametrize(
    ('field', 'bad_value'),
    [
        ('width', 999),
        ('height', 999),
        ('mime_type', 'image/jpeg'),
        ('sha256', '0' * 64),
        ('file_size', 1),
    ],
)
def test_generated_asset_metadata_must_match_real_file(tmp_path: Path, field: str, bad_value):
    root = make_series_root(tmp_path)
    write_asset_library(root, mode='core_assets', status='GENERATED')
    _, meta = _real_png(root)
    meta[field] = bad_value
    _update_record(root, image_file='assets/generated/A001_主角_人物母板_V01.png', **meta)
    with pytest.raises(ValueError, match=f'{field}|ASSET_FILE_INVALID'):
        _verify_delivery_gate(root)


def test_real_generated_png_with_matching_metadata_passes(tmp_path: Path):
    root = make_series_root(tmp_path)
    write_asset_library(root, mode='core_assets', status='GENERATED')
    _, meta = _real_png(root)
    _update_record(root, image_file='assets/generated/A001_主角_人物母板_V01.png', **meta)
    _verify_delivery_gate(root)


def test_prompts_only_mode_does_not_require_media_metadata(tmp_path: Path):
    root = make_series_root(tmp_path)
    write_asset_library(root, mode='prompts_only', status='PROMPT_ONLY')
    _verify_delivery_gate(root)


def test_generated_persistent_state_is_validated_too(tmp_path: Path):
    root = make_series_root(tmp_path)
    write_asset_library(root, mode='prompts_only', status='PROMPT_ONLY')
    path = root / 'assets' / 'ASSET_LIBRARY.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data['ASSET_LIBRARY']['persistent_states'] = [{
        'state_id': 'A001-ST001', 'inherits_from': 'A001', 'state_category': 'wet',
        'visible_change': '衣服湿润', 'unchanged_facts': ['身份不变'],
        'image_prompt': '同一人物衣服湿润', 'image_status': 'GENERATED',
        'image_file': 'assets/generated/A001-ST001_主角_湿润状态_V01.png',
    }]
    dump(path, data)
    fake = root / 'assets' / 'generated' / 'A001-ST001_主角_湿润状态_V01.png'
    fake.parent.mkdir(parents=True, exist_ok=True)
    fake.write_bytes(b'fake state image')
    with pytest.raises(ValueError, match='A001-ST001|ASSET_FILE_INVALID|图片'):
        _verify_delivery_gate(root)
