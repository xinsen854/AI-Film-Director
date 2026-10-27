from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from qc_routing import build_issue, write_qc_issues
from build_exports import build_exports

_spec = importlib.util.spec_from_file_location('item3_helpers', ROOT / 'tests' / 'item3' / 'test_final_hard_qc.py')
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)
make_series_root = _mod.make_series_root


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def test_explicit_error_code_maps_asset_to_asset_owner():
    issue = build_issue('HARD_REQUIRED_ASSET_MISSING：A001为必要资产，当前状态=PROMPT_ONLY', severity='HARD')
    assert issue['error_code'] == 'HARD_REQUIRED_ASSET_MISSING'
    assert issue['owner_layer'] == 'ASSET'
    assert issue['affected_ids'] == ['A001']
    assert issue['rerun_path'][0] == 'ASSET'
    assert 'STORY' in issue['do_not_rerun']


def test_explicit_current_gu_code_maps_to_shot_segment_not_old_prompt_compiler():
    issue = build_issue('CURRENT_GU_ONLY_DIALOGUE：EP02/GU007 提前包含未来对白', severity='HARD')
    assert issue['error_code'] == 'CURRENT_GU_ONLY_DIALOGUE'
    assert issue['owner_layer'] == 'SHOT_SEGMENT'
    assert issue['affected_ids'] == ['EP02', 'GU007']
    assert issue['rerun_path'][:2] == ['SHOT_SEGMENT', 'QUALITY']
    assert 'AUTHORITY' in issue['do_not_rerun']


def test_unknown_code_does_not_guess_owner_from_chinese_words():
    issue = build_issue('SOME_NEW_ERROR：资产看起来有问题，但这是未知错误码', severity='HARD')
    assert issue['error_code'] == 'SOME_NEW_ERROR'
    assert issue['owner_layer'] == 'DELIVERY'
    assert issue['rerun_path'][0] == 'DELIVERY'


def test_message_without_code_uses_delivery_gate_fallback_not_keyword_guess():
    issue = build_issue('资产文件看起来不对', severity='HARD')
    assert issue['error_code'] == 'DELIVERY_GATE_ERROR'
    assert issue['owner_layer'] == 'DELIVERY'


def test_item7_routing_remains_stable_after_item8_localization_expansion():
    issue = build_issue('CURRENT_GU_ONLY_DIALOGUE：EP03/SC08/DB023/GU018', severity='HARD')
    assert issue['affected_ids'] == ['EP03', 'SC08', 'DB023', 'GU018']
    assert issue['owner_layer'] == 'SHOT_SEGMENT'


def test_write_qc_issues_persists_required_rerun_fields(tmp_path: Path):
    write_qc_issues(tmp_path, [
        'HARD_SH_GU_PROMPT_MISSING：EP01/SH003没有被有效GU完整承接',
        'ASSET_FILE_INVALID：A001 sha256与真实文件不一致',
    ])
    data = load(tmp_path / 'state' / 'qc' / 'QC_ISSUES.json')
    assert len(data['issues']) == 2
    for item in data['issues']:
        assert set(['issue_id', 'severity', 'error_code', 'owner_layer', 'affected_ids', 'reason', 'rerun_path', 'do_not_rerun']).issubset(item)
    assert data['issues'][0]['owner_layer'] == 'SHOT_SEGMENT'
    assert data['issues'][1]['owner_layer'] == 'ASSET'


def test_failed_final_export_writes_structured_owner_issue(tmp_path: Path):
    root = make_series_root(tmp_path, count=1, runtime=10.0)
    brief_path = root / 'state' / 'project_brief.json'
    brief = load(brief_path)
    brief['asset_production_mode'] = 'core_assets'
    dump(brief_path, brief)

    asset_path = root / 'assets' / 'ASSET_LIBRARY.json'
    asset_data = {'ASSET_LIBRARY': {'character_assets': [], 'location_assets': [], 'prop_assets': [], 'g_assets': [], 'persistent_states': []}}
    lib = asset_data['ASSET_LIBRARY']
    lib['character_assets'] = [{
        'asset_id': 'A001', 'name': '许程', 'identity': '主角', 'appearance': '33岁男性', 'wardrobe': '深色夹克',
        'recognition_points': ['短发'], 'use_scope': ['EP01'], 'image_prompt': '现实主义人物定妆',
        'image_status': 'PROMPT_ONLY', 'image_file': '', 'downstream_metadata': {'default_reference_role': 'character'}
    }]
    dump(asset_path, asset_data)

    (root / 'state').mkdir(parents=True, exist_ok=True)
    (root / 'state' / 'runtime_contract.json').write_text(json.dumps({'runtime_state_version':'2.0','authority_profile':'AFD_CW_SINGLE_AUTHORITY'}, ensure_ascii=False), encoding='utf-8')
    (root / 'state' / 'pipeline_state.json').write_text(json.dumps({'runtime_state_version':'2.0'}, ensure_ascii=False), encoding='utf-8')
    with pytest.raises(ValueError, match='HARD_REQUIRED_ASSET_MISSING|Final Hard QC'):
        build_exports(root)

    qc = load(root / 'state' / 'qc' / 'QC_ISSUES.json')
    hit = next(i for i in qc['issues'] if i['error_code'] == 'HARD_REQUIRED_ASSET_MISSING')
    assert hit['owner_layer'] == 'ASSET'
    assert hit['affected_ids'] == ['A001']
    assert hit['rerun_path'][0] == 'ASSET'
    assert 'STORY' in hit['do_not_rerun']


def test_analysis_artifact_leak_routes_only_to_shot_segment_owner():
    issue = build_issue('ANALYSIS_ARTIFACT_LEAK：EP01/SH010 包含内部情绪图谱UI', severity='HARD')
    assert issue['owner_layer'] == 'SHOT_SEGMENT'
    assert issue['rerun_path'][:2] == ['SHOT_SEGMENT', 'QUALITY']
    assert 'STORY' in issue['do_not_rerun']
