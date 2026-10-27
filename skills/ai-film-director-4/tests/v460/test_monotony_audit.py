from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))

from render_storyboard import sequence_quality_warnings


def sh(sid, size, move):
    return {
        'edit_shot_id': sid,
        'shot_type': {'shot_size': size},
        'camera_parameters': {'camera_move': move},
    }


def test_three_same_size_and_move_warns():
    payload = {'edit_shots': [sh('SH001','MS','slow push-in'), sh('SH002','MS','slow push-in'), sh('SH003','MS','slow push-in')]}
    warnings = sequence_quality_warnings(payload)
    assert any('MONOTONY_AUDIT' in w for w in warnings)


def test_same_size_but_different_move_does_not_warn():
    payload = {'edit_shots': [sh('SH001','MS','slow push-in'), sh('SH002','MS','locked'), sh('SH003','MS','slow push-in')]}
    assert sequence_quality_warnings(payload) == []


def test_same_move_but_different_size_does_not_warn():
    payload = {'edit_shots': [sh('SH001','MS','locked'), sh('SH002','CU','locked'), sh('SH003','MS','locked')]}
    assert sequence_quality_warnings(payload) == []


def test_missing_explicit_camera_or_size_does_not_infer_from_prose():
    payload = {'edit_shots': [
        {'edit_shot_id':'SH001','shot_type':'cinematic','camera_parameters':{'notes':'medium slow push-in'}},
        {'edit_shot_id':'SH002','shot_type':'cinematic','camera_parameters':{'notes':'medium slow push-in'}},
        {'edit_shot_id':'SH003','shot_type':'cinematic','camera_parameters':{'notes':'medium slow push-in'}},
    ]}
    assert sequence_quality_warnings(payload) == []


def test_four_identical_cuts_produce_one_run_warning_not_duplicate_spam():
    payload = {'edit_shots': [sh(f'SH00{i}','MS','locked') for i in range(1,5)]}
    warnings = sequence_quality_warnings(payload)
    assert len([w for w in warnings if 'MONOTONY_AUDIT' in w]) == 1


def test_monotony_is_documented_as_warning_not_blocker():
    qc = (ROOT / 'references/cineweaver/Final_QC_Engine_V1.3/module.md').read_text(encoding='utf-8').lower()
    coverage = (ROOT / 'references/cineweaver/Shot_Segment_Engine_V1.3/runtime/COVERAGE_DECISION.md').read_text(encoding='utf-8').lower()
    combined = qc + coverage
    assert 'monotony' in combined
    assert 'warning' in combined
    assert 'three consecutive' in combined or '连续 3' in combined or '连续3' in combined
    assert 'same shot size' in combined or '景别' in combined
    assert 'camera move' in combined or '摄影机运动' in combined

def test_current_afd_string_shot_type_and_camera_behavior_are_audited():
    payload = {'edit_shots': [
        {'edit_shot_id':'SH001','shot_type':'MS','camera_parameters':{'camera_behavior':'缓慢推近'}},
        {'edit_shot_id':'SH002','shot_type':'MS','camera_parameters':{'camera_behavior':'缓慢推近'}},
        {'edit_shot_id':'SH003','shot_type':'MS','camera_parameters':{'camera_behavior':'缓慢推近'}},
    ]}
    assert any('MONOTONY_AUDIT' in w for w in sequence_quality_warnings(payload))


def test_arbitrary_style_string_is_not_misread_as_shot_size():
    payload = {'edit_shots': [
        {'edit_shot_id':'SH001','shot_type':'cinematic','camera_parameters':{'camera_behavior':'缓慢推近'}},
        {'edit_shot_id':'SH002','shot_type':'cinematic','camera_parameters':{'camera_behavior':'缓慢推近'}},
        {'edit_shot_id':'SH003','shot_type':'cinematic','camera_parameters':{'camera_behavior':'缓慢推近'}},
    ]}
    assert sequence_quality_warnings(payload) == []
