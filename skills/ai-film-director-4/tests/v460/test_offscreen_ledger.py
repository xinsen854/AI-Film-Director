import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))

from validate_continuity import validate_continuity


def shot(sid, present, *, carry=None, scene='SC01'):
    calls = [{'asset_id': aid} for aid in present]
    handoff = {'type': 'CS', 'start_state': {}, 'do_not_reset': []}
    if carry is not None:
        handoff['offscreen_carry'] = carry
    return {
        'edit_shot_id': sid,
        'scene_id': scene,
        'visual_asset_calls': calls,
        'axis_and_gaze': {},
        'spatial_blocking': {},
        'first_last_frame_anchors': {},
        'next_shot_handoff': handoff,
    }


def project(tmp_path, shots):
    (tmp_path / 'storyboard').mkdir()
    (tmp_path / 'assets').mkdir()
    (tmp_path / 'PRODUCTION_LEDGER.json').write_text(json.dumps({
        'scope_type': 'episodes', 'completed_episodes': ['EP01']
    }, ensure_ascii=False), encoding='utf-8')
    (tmp_path / 'storyboard' / 'EP01_STORYBOARD.json').write_text(json.dumps({
        'edit_shots': shots
    }, ensure_ascii=False), encoding='utf-8')
    (tmp_path / 'assets' / 'ASSET_LIBRARY.json').write_text(json.dumps({
        'ASSET_LIBRARY': {
            'contract_version': '4.3',
            'character_assets': [{'asset_id': 'A001'}, {'asset_id': 'A002'}],
            'voice_assets': [], 'persistent_states': [], 'location_assets': [], 'prop_assets': [], 'g_assets': [],
            'project_asset_policy': {}
        }
    }, ensure_ascii=False), encoding='utf-8')


def test_valid_offscreen_carry_is_accepted(tmp_path):
    project(tmp_path, [
        shot('SH001', ['A001', 'A002'], carry=[{'asset_id': 'A002', 'exit_side': 'frame-left', 'last_visible_state': 'still carrying the crate'}]),
        shot('SH002', ['A001']),
    ])
    assert validate_continuity(tmp_path) == []


def test_offscreen_carry_requires_explicit_exit_side_and_last_state(tmp_path):
    project(tmp_path, [
        shot('SH001', ['A001', 'A002'], carry=[{'asset_id': 'A002'}]),
        shot('SH002', ['A001']),
    ])
    errors = validate_continuity(tmp_path)
    assert any('OFFSCREEN_CARRY_STRUCTURE' in e for e in errors)


def test_offscreen_carry_rejects_non_character_asset(tmp_path):
    project(tmp_path, [
        shot('SH001', ['A001'], carry=[{'asset_id': 'P001', 'exit_side': 'frame-left', 'last_visible_state': 'on table'}]),
        shot('SH002', ['A001']),
    ])
    errors = validate_continuity(tmp_path)
    assert any('OFFSCREEN_CARRY_ASSET' in e for e in errors)


def test_offscreen_carry_rejects_duplicate_character(tmp_path):
    carry = [
        {'asset_id': 'A002', 'exit_side': 'frame-left', 'last_visible_state': 'crate in both hands'},
        {'asset_id': 'A002', 'exit_side': 'frame-left', 'last_visible_state': 'same state'},
    ]
    project(tmp_path, [shot('SH001', ['A001', 'A002'], carry=carry), shot('SH002', ['A001'])])
    errors = validate_continuity(tmp_path)
    assert any('OFFSCREEN_CARRY_DUPLICATE' in e for e in errors)


def test_offscreen_carry_cannot_claim_character_is_offscreen_when_next_shot_shows_them(tmp_path):
    carry = [{'asset_id': 'A002', 'exit_side': 'frame-left', 'last_visible_state': 'crate in both hands'}]
    project(tmp_path, [shot('SH001', ['A001', 'A002'], carry=carry), shot('SH002', ['A001', 'A002'])])
    errors = validate_continuity(tmp_path)
    assert any('OFFSCREEN_CARRY_VISIBLE_CONFLICT' in e for e in errors)


def test_offscreen_carry_does_not_become_mandatory_for_every_absent_character(tmp_path):
    project(tmp_path, [shot('SH001', ['A001', 'A002']), shot('SH002', ['A001'])])
    assert validate_continuity(tmp_path) == []


def test_contract_documents_offscreen_carry_without_new_owner():
    schema = (ROOT / 'references/cineweaver/Shot_Segment_Engine_V1.3/schema/STORYBOARD_SHOT_RESULT.yaml').read_text(encoding='utf-8')
    handoff = (ROOT / 'references/cineweaver/Shot_Segment_Engine_V1.3/runtime/CUT_HANDOFF.md').read_text(encoding='utf-8')
    prompt = (ROOT / 'references/cineweaver/Shot_Segment_Engine_V1.3/runtime/VIDEO_PROMPT_COMPILER.md').read_text(encoding='utf-8')
    combined = (schema + handoff + prompt).lower()
    assert 'offscreen_carry' in combined
    assert 'exit_side' in combined
    assert 'last_visible_state' in combined
    assert 'next_shot_handoff' in combined
    assert 'new owner' not in combined

def test_offscreen_carry_rejects_hidden_extra_fields(tmp_path):
    carry = [{'asset_id': 'A002', 'exit_side': 'frame-left', 'last_visible_state': 'crate', 'future_secret': 'invented'}]
    project(tmp_path, [shot('SH001', ['A001', 'A002'], carry=carry), shot('SH002', ['A001'])])
    errors = validate_continuity(tmp_path)
    assert any('OFFSCREEN_CARRY_STRUCTURE' in e and 'unknown fields' in e for e in errors)


def test_offscreen_visibility_check_cannot_be_bypassed_by_omitting_visual_asset_call(tmp_path):
    carry = [{'asset_id': 'A002', 'exit_side': 'frame-left', 'last_visible_state': 'crate'}]
    first = shot('SH001', ['A001', 'A002'], carry=carry)
    second = shot('SH002', ['A001'])
    second['spatial_blocking'] = {'start_positions': {'A002': 'left doorway'}}
    project(tmp_path, [first, second])
    errors = validate_continuity(tmp_path)
    assert any('OFFSCREEN_CARRY_VISIBLE_CONFLICT' in e for e in errors)
