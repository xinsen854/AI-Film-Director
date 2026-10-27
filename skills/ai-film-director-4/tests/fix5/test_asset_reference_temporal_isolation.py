from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from validate_current_gu_only import validate_current_gu_only

_spec = importlib.util.spec_from_file_location('item3_helpers', ROOT / 'tests' / 'item3' / 'test_final_hard_qc.py')
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)
two_shot_storyboard = _mod.two_shot_storyboard


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def make_root(tmp_path: Path) -> tuple[Path, dict]:
    root = tmp_path / 'project'
    payload = two_shot_storyboard(cross_allowed=True)
    for i, shot in enumerate(payload['edit_shots'], start=1):
        shot['edit_shot_id'] = f'SH{i:03d}'
        shot['scene_id'] = f'SC{i:02d}'
        shot.setdefault('coverage', {})['revealed_info_ids'] = []
    for i, gu in enumerate(payload['generation_units'], start=1):
        gu['member_edit_shots'] = [f'SH{i:03d}']
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', payload)
    dump(root / 'state' / 'information_ledger.json', {'items': []})
    dump(root / 'assets' / 'ASSET_LIBRARY.json', {
        'ASSET_LIBRARY': {
            'contract_version': '4.3',
            'project_asset_policy': {},
            'character_assets': [],
            'voice_assets': [],
            'persistent_states': [],
            'location_assets': [],
            'prop_assets': [],
            'g_assets': [],
        }
    })
    return root, payload


def save_storyboard(root: Path, payload: dict) -> None:
    dump(root / 'storyboard' / 'EP01_STORYBOARD.json', payload)


def load_assets(root: Path) -> dict:
    return json.loads((root / 'assets' / 'ASSET_LIBRARY.json').read_text(encoding='utf-8'))


def save_assets(root: Path, payload: dict) -> None:
    dump(root / 'assets' / 'ASSET_LIBRARY.json', payload)


def test_current_asset_reference_prompt_cannot_contain_hidden_protected_literal(tmp_path: Path):
    root, payload = make_root(tmp_path)
    payload['edit_shots'][0]['visual_asset_calls'] = [
        {'asset_id': 'P003', 'name': '黄色信封', 'file': 'assets/generated/P003.png', 'role': 'prop', 'shot_use': '只露信封一角'}
    ]
    save_storyboard(root, payload)
    assets = load_assets(root)
    assets['ASSET_LIBRARY']['prop_assets'] = [{
        'asset_id': 'P003', 'name': '黄色信封', 'image_prompt': '黄色牛皮纸信封，打开后首页清晰写着《商铺租赁终止协议》',
        'image_status': 'PROMPT_ONLY',
    }]
    save_assets(root, assets)
    dump(root / 'state' / 'information_ledger.json', {'items': [{
        'info_id': 'I001', 'truth': '信封内是商铺租赁终止协议', 'status': 'HIDDEN',
        'planned_reveal': 'EP01/SC02/SH002', 'protected_literals': ['商铺租赁终止协议'],
    }]})

    errors = validate_current_gu_only(root)
    assert any('ASSET_REVEAL' in e and 'P003' in e for e in errors), errors


def test_revealed_asset_reference_literal_is_allowed(tmp_path: Path):
    root, payload = make_root(tmp_path)
    payload['edit_shots'][1]['visual_asset_calls'] = [
        {'asset_id': 'P003', 'name': '黄色信封', 'file': 'assets/generated/P003.png', 'role': 'prop', 'shot_use': '协议被取出并读到标题'}
    ]
    payload['edit_shots'][1]['coverage']['revealed_info_ids'] = ['I001']
    save_storyboard(root, payload)
    assets = load_assets(root)
    assets['ASSET_LIBRARY']['prop_assets'] = [{
        'asset_id': 'P003', 'name': '黄色信封', 'image_prompt': '黄色牛皮纸信封，打开后首页清晰写着《商铺租赁终止协议》',
        'image_status': 'PROMPT_ONLY',
    }]
    save_assets(root, assets)
    dump(root / 'state' / 'information_ledger.json', {'items': [{
        'info_id': 'I001', 'truth': '信封内是商铺租赁终止协议', 'status': 'HIDDEN',
        'planned_reveal': 'EP01/SC02/SH002', 'protected_literals': ['商铺租赁终止协议'],
    }]})

    errors = validate_current_gu_only(root)
    assert not any('ASSET_REVEAL' in e for e in errors), errors


def test_unused_asset_with_future_reveal_does_not_block(tmp_path: Path):
    root, _ = make_root(tmp_path)
    assets = load_assets(root)
    assets['ASSET_LIBRARY']['prop_assets'] = [{
        'asset_id': 'P003', 'name': '黄色信封', 'image_prompt': '首页写着《商铺租赁终止协议》',
        'image_status': 'PROMPT_ONLY',
    }]
    save_assets(root, assets)
    dump(root / 'state' / 'information_ledger.json', {'items': [{
        'info_id': 'I001', 'truth': '信封内容', 'status': 'HIDDEN', 'planned_reveal': 'SH002',
        'protected_literals': ['商铺租赁终止协议'],
    }]})

    errors = validate_current_gu_only(root)
    assert not any('ASSET_REVEAL' in e for e in errors), errors


def test_current_master_reference_cannot_embed_future_state_delta(tmp_path: Path):
    root, payload = make_root(tmp_path)
    payload['edit_shots'][0]['visual_asset_calls'] = [
        {'asset_id': 'S001', 'name': '钟表店', 'file': 'assets/generated/S001.png', 'role': 'location', 'shot_use': '当前店内'}
    ]
    save_storyboard(root, payload)
    assets = load_assets(root)
    assets['ASSET_LIBRARY']['location_assets'] = [{
        'asset_id': 'S001', 'name': '钟表店', 'image_prompt': '旧钟表店，货架半空，玻璃门上的营业牌已经摘下',
        'image_status': 'PROMPT_ONLY',
    }]
    assets['ASSET_LIBRARY']['persistent_states'] = [{
        'state_id': 'S001-ST002', 'inherits_from': 'S001', 'state_category': 'location_function_state',
        'state_start': 'SH002', 'state_end': 'ongoing', 'visible_change': '营业牌已经摘下',
        'image_prompt': '玻璃门上的营业牌已经摘下', 'image_status': 'PROMPT_ONLY',
    }]
    save_assets(root, assets)

    errors = validate_current_gu_only(root)
    assert any('ASSET_FUTURE_STATE_CONTENT' in e and 'S001-ST002' in e for e in errors), errors


def test_current_state_reference_cannot_embed_future_sibling_state_delta(tmp_path: Path):
    root, payload = make_root(tmp_path)
    payload['edit_shots'][0]['visual_asset_calls'] = [
        {'asset_id': 'S001-ST001', 'name': '钟表店半空状态', 'file': 'assets/generated/S001-ST001.png', 'role': 'state', 'shot_use': '当前半空'}
    ]
    save_storyboard(root, payload)
    assets = load_assets(root)
    assets['ASSET_LIBRARY']['location_assets'] = [{
        'asset_id': 'S001', 'name': '钟表店', 'image_prompt': '正常营业的旧钟表店', 'image_status': 'PROMPT_ONLY',
    }]
    assets['ASSET_LIBRARY']['persistent_states'] = [
        {
            'state_id': 'S001-ST001', 'inherits_from': 'S001', 'state_category': 'location_function_state',
            'state_start': 'SH001', 'state_end': 'ongoing', 'visible_change': '货架半空',
            'image_prompt': '货架半空，同时玻璃门上的营业牌已经摘下', 'image_status': 'PROMPT_ONLY',
        },
        {
            'state_id': 'S001-ST002', 'inherits_from': 'S001', 'state_category': 'location_function_state',
            'state_start': 'SH002', 'state_end': 'ongoing', 'visible_change': '营业牌已经摘下',
            'image_prompt': '玻璃门上的营业牌已经摘下', 'image_status': 'PROMPT_ONLY',
        },
    ]
    save_assets(root, assets)

    errors = validate_current_gu_only(root)
    assert any('ASSET_FUTURE_STATE_CONTENT' in e and 'S001-ST002' in e for e in errors), errors


def test_current_state_own_delta_is_allowed_and_not_overrestricted(tmp_path: Path):
    root, payload = make_root(tmp_path)
    payload['edit_shots'][0]['visual_asset_calls'] = [
        {'asset_id': 'S001-ST001', 'name': '钟表店半空状态', 'file': 'assets/generated/S001-ST001.png', 'role': 'state', 'shot_use': '当前半空'}
    ]
    save_storyboard(root, payload)
    assets = load_assets(root)
    assets['ASSET_LIBRARY']['location_assets'] = [{
        'asset_id': 'S001', 'name': '钟表店', 'image_prompt': '正常营业的旧钟表店', 'image_status': 'PROMPT_ONLY',
    }]
    assets['ASSET_LIBRARY']['persistent_states'] = [
        {
            'state_id': 'S001-ST001', 'inherits_from': 'S001', 'state_category': 'location_function_state',
            'state_start': 'SH001', 'state_end': 'ongoing', 'visible_change': '货架半空',
            'image_prompt': '保持同一钟表店几何，货架半空', 'image_status': 'PROMPT_ONLY',
        },
        {
            'state_id': 'S001-ST002', 'inherits_from': 'S001', 'state_category': 'location_function_state',
            'state_start': 'SH002', 'state_end': 'ongoing', 'visible_change': '营业牌已经摘下',
            'image_prompt': '玻璃门上的营业牌已经摘下', 'image_status': 'PROMPT_ONLY',
        },
    ]
    save_assets(root, assets)

    errors = validate_current_gu_only(root)
    assert not any('ASSET_FUTURE_STATE_CONTENT' in e for e in errors), errors


def test_state_declared_to_start_in_future_cannot_be_called_now(tmp_path: Path):
    root, payload = make_root(tmp_path)
    payload['edit_shots'][0]['visual_asset_calls'] = [
        {'asset_id': 'S001-ST002', 'name': '营业牌摘除状态', 'file': 'assets/generated/S001-ST002.png', 'role': 'state', 'shot_use': '错误提前调用'}
    ]
    save_storyboard(root, payload)
    assets = load_assets(root)
    assets['ASSET_LIBRARY']['location_assets'] = [{
        'asset_id': 'S001', 'name': '钟表店', 'image_prompt': '正常营业的旧钟表店', 'image_status': 'PROMPT_ONLY',
    }]
    assets['ASSET_LIBRARY']['persistent_states'] = [{
        'state_id': 'S001-ST002', 'inherits_from': 'S001', 'state_category': 'location_function_state',
        'state_start': 'SH002', 'state_end': 'ongoing', 'visible_change': '营业牌已经摘下',
        'image_prompt': '玻璃门上的营业牌已经摘下', 'image_status': 'PROMPT_ONLY',
    }]
    save_assets(root, assets)

    errors = validate_current_gu_only(root)
    assert any('ASSET_STATE_TOO_EARLY' in e and 'S001-ST002' in e for e in errors), errors
