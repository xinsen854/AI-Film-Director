from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from render_storyboard import render_storyboard
from validate_unit_consistency import _validate_storyboard_authority

_spec = importlib.util.spec_from_file_location('item3_helpers_for_fix4', ROOT / 'tests' / 'item3' / 'test_final_hard_qc.py')
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)
minimal_storyboard = _mod.minimal_storyboard


def _write_storyboard(root: Path, payload: dict) -> None:
    (root / 'storyboard').mkdir(parents=True, exist_ok=True)
    (root / 'storyboard' / 'EP01_STORYBOARD.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    (root / 'storyboard' / 'EP01_STORYBOARD.md').write_text(
        render_storyboard(payload), encoding='utf-8'
    )


def _character_record(*, status: str = 'PROMPT_ONLY', image_file: str = '') -> dict:
    return {
        'asset_id': 'A001',
        'asset_class': 'VISUAL_ASSET',
        'name': '许程',
        'visual_identity': {
            'silhouette': '33岁男性，中等身材',
            'hair': '短黑发',
            'base_wardrobe': '深灰夹克',
            'primary_colors': '深灰与黑色',
            'distinguishing_marks': ['眉骨略高'],
        },
        'execution_anchor_summary': {
            'identity': '33岁中国男性，面部成熟但不显老',
            'silhouette': '中等身材',
            'wardrobe': '深灰夹克',
            'persistent_state': '无明显伤痕',
            'distinguishing_marks': ['眉骨略高'],
            'performance_identity': '克制，反应延迟半拍',
        },
        'image_prompt': '33岁中国男性，短黑发，深灰夹克，眉骨略高，现实主义电影人物资产',
        'image_status': status,
        'image_file': image_file,
    }


def _payload_with_current_character(reference_roles: list[str]) -> dict:
    payload = minimal_storyboard()
    payload['edit_shots'][0]['visual_asset_calls'] = [{
        'asset_id': 'A001', 'name': '许程', 'file': 'PROMPT_ONLY',
        'role': '人物身份', 'shot_use': '当前镜头保持人物脸型、年龄感与服装身份',
    }]
    payload['generation_units'][0]['prompt_sections']['reference_roles'] = reference_roles
    return payload


def test_prompt_only_current_asset_rejects_internal_id_only_reference_role(tmp_path: Path):
    root = tmp_path / 'project'
    payload = _payload_with_current_character(['A001 identity'])
    _write_storyboard(root, payload)
    errors: list[str] = []

    _validate_storyboard_authority(root, 'EP01', {'A001': _character_record()}, set(), errors)

    assert any('GU_ASSET_IDENTITY_ANCHOR' in error and 'A001' in error for error in errors), errors


def test_prompt_only_current_asset_accepts_specific_text_identity_anchor(tmp_path: Path):
    root = tmp_path / 'project'
    payload = _payload_with_current_character([
        'A001｜许程｜文字身份锚：33岁中国男性，中等身材，短黑发，深灰夹克，眉骨略高；只负责当前镜头人物身份，不引入其他场景信息。'
    ])
    _write_storyboard(root, payload)
    errors: list[str] = []

    _validate_storyboard_authority(root, 'EP01', {'A001': _character_record()}, set(), errors)

    assert not any('GU_ASSET_IDENTITY_ANCHOR' in error or 'FAKE_MEDIA_REFERENCE' in error for error in errors), errors


def test_prompt_only_asset_cannot_be_presented_as_fake_uploaded_image(tmp_path: Path):
    root = tmp_path / 'project'
    payload = _payload_with_current_character([
        '@图片1 对应 A001｜许程：只负责脸型、发型、年龄感与当前服装。'
    ])
    _write_storyboard(root, payload)
    errors: list[str] = []

    _validate_storyboard_authority(root, 'EP01', {'A001': _character_record()}, set(), errors)

    assert any('FAKE_MEDIA_REFERENCE' in error and 'A001' in error for error in errors), errors


def test_real_active_media_requires_explicit_binding_and_accepts_it(tmp_path: Path):
    root = tmp_path / 'project'
    media = root / 'assets' / 'generated' / 'A001.png'
    media.parent.mkdir(parents=True, exist_ok=True)
    media.write_bytes(b'not-decoded-here')
    record = _character_record(status='GENERATED', image_file='assets/generated/A001.png')
    payload = _payload_with_current_character([
        '@图片1 对应 A001｜许程：只负责脸型、短黑发、33岁年龄感、中等身材与深灰夹克；不采用参考图背景和原姿态。'
    ])
    payload['generation_units'][0]['active_media_references'] = ['A001']
    _write_storyboard(root, payload)
    errors: list[str] = []

    _validate_storyboard_authority(root, 'EP01', {'A001': record}, set(), errors)

    assert not any('GU_ASSET_IDENTITY_ANCHOR' in error or 'REFERENCE_BINDING_FAILURE' in error for error in errors), errors


def test_real_active_media_without_explicit_reference_binding_is_rejected(tmp_path: Path):
    root = tmp_path / 'project'
    media = root / 'assets' / 'generated' / 'A001.png'
    media.parent.mkdir(parents=True, exist_ok=True)
    media.write_bytes(b'not-decoded-here')
    record = _character_record(status='GENERATED', image_file='assets/generated/A001.png')
    payload = _payload_with_current_character([
        'A001｜许程｜保持身份一致。'
    ])
    payload['generation_units'][0]['active_media_references'] = ['A001']
    _write_storyboard(root, payload)
    errors: list[str] = []

    _validate_storyboard_authority(root, 'EP01', {'A001': record}, set(), errors)

    assert any('REFERENCE_BINDING_FAILURE' in error and 'A001' in error for error in errors), errors


def test_unrelated_asset_not_used_by_current_member_sh_is_not_forced_into_gu(tmp_path: Path):
    root = tmp_path / 'project'
    payload = minimal_storyboard()
    _write_storyboard(root, payload)
    errors: list[str] = []

    _validate_storyboard_authority(root, 'EP01', {'A001': _character_record()}, set(), errors)

    assert not any('GU_ASSET_IDENTITY_ANCHOR' in error or 'REFERENCE_BINDING_FAILURE' in error for error in errors), errors
