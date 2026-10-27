from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from master_orchestrator import (
    STAGES,
    init_state,
    load_state,
    pass_stage,
    resolve_script_lock,
    fail_stage,
)

EXPECTED = [
    'PROJECT_INTAKE','FORGE_DESIGN','DESIGN_HANDOFF','CREATIVE_BIBLE',
    'SCREENWRITER','FORGE_GATE_QC_DEAI','SCRIPT_LOCK','FORGE_AUDIT',
    'LOCKED_AUDIT_HANDOFF','FORGE_EMOTION_RENDER','SCENE_INTELLIGENCE',
    'CAPABILITY_ROUTER','DIRECTOR_CRAFT','SCENE_DIRECTION','ASSET_ENGINE',
    'SPATIAL','SHOT_SEGMENT','FINAL_HARD_QC','PRODUCTION_LEDGER','EXPORTS',
]


def pass_with_artifact(root: Path, stage: str, **kwargs):
    path = root / 'stage-artifacts' / f'{stage}.txt'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stage, encoding='utf-8')
    return pass_stage(root, stage, artifact=path.relative_to(root).as_posix(), **kwargs)


def test_master_stage_order_is_exact():
    assert STAGES == EXPECTED


def test_review_lock_stops_until_explicit_approval(tmp_path):
    candidate = tmp_path / 'lock_candidates' / 'EP01.md'
    candidate.parent.mkdir(parents=True)
    candidate.write_text('locked candidate', encoding='utf-8')
    init_state(tmp_path, 'REVIEW_BEFORE_LOCK')
    for stage in EXPECTED[:5]:
        pass_with_artifact(tmp_path, stage)
    pass_stage(tmp_path, 'FORGE_GATE_QC_DEAI', artifact='lock_candidates/EP01.md')
    state = load_state(tmp_path)
    assert state['current_stage'] == 'SCRIPT_LOCK'
    assert state['stage_status'] == 'WAITING_FOR_SCRIPT_APPROVAL'
    assert state['lock_status'] == 'DRAFT'
    resolve_script_lock(tmp_path, approved=True)
    state = load_state(tmp_path)
    assert state['current_stage'] == 'FORGE_AUDIT'
    assert state['lock_status'] == 'LOCKED'


def test_auto_accept_lock_continues_without_human_gate(tmp_path):
    candidate = tmp_path / 'lock_candidates' / 'EP01.md'
    candidate.parent.mkdir(parents=True)
    candidate.write_text('locked candidate', encoding='utf-8')
    init_state(tmp_path, 'AUTO_ACCEPT_AFTER_QC')
    for stage in EXPECTED[:5]:
        pass_with_artifact(tmp_path, stage)
    pass_stage(tmp_path, 'FORGE_GATE_QC_DEAI', artifact='lock_candidates/EP01.md')
    state = load_state(tmp_path)
    assert state['current_stage'] == 'FORGE_AUDIT'
    assert state['lock_status'] == 'LOCKED'
    assert state['next_stage'] == 'LOCKED_AUDIT_HANDOFF'
    assert any(x['stage'] == 'SCRIPT_LOCK' and x['status'] == 'PASS' for x in state['history'])


def test_out_of_order_stage_is_rejected(tmp_path):
    init_state(tmp_path, 'REVIEW_BEFORE_LOCK')
    try:
        pass_stage(tmp_path, 'FORGE_DESIGN')
    except ValueError as exc:
        assert 'OUT_OF_ORDER' in str(exc)
    else:
        raise AssertionError('out-of-order stage should fail')


def test_owner_rerun_routes_to_smallest_owner_without_restart(tmp_path):
    init_state(tmp_path, 'AUTO_ACCEPT_AFTER_QC')
    pass_with_artifact(tmp_path, 'PROJECT_INTAKE')
    pass_with_artifact(tmp_path, 'FORGE_DESIGN')
    pass_with_artifact(tmp_path, 'DESIGN_HANDOFF')
    pass_with_artifact(tmp_path, 'CREATIVE_BIBLE')
    pass_with_artifact(tmp_path, 'SCREENWRITER')
    fail_stage(tmp_path, 'FORGE_GATE_QC_DEAI', owner_stage='SCREENWRITER', affected_ids=['SC03'])
    state = load_state(tmp_path)
    assert state['current_stage'] == 'SCREENWRITER'
    assert state['rerun']['owner_stage'] == 'SCREENWRITER'
    assert state['rerun']['affected_ids'] == ['SC03']
    assert state['history'][0]['stage'] == 'PROJECT_INTAKE'


def test_forge_gate_pass_requires_real_lock_candidate_artifact(tmp_path):
    init_state(tmp_path, 'REVIEW_BEFORE_LOCK')
    for stage in EXPECTED[:5]:
        pass_with_artifact(tmp_path, stage)
    try:
        pass_stage(tmp_path, 'FORGE_GATE_QC_DEAI')
    except ValueError as exc:
        assert 'LOCK_CANDIDATE_REQUIRED' in str(exc)
    else:
        raise AssertionError('QC PASS must bind a real lock candidate before SCRIPT_LOCK')


def test_review_lock_rejects_candidate_changed_after_qc(tmp_path):
    candidate = tmp_path / 'lock_candidates' / 'EP01.md'
    candidate.parent.mkdir(parents=True)
    candidate.write_text('v1', encoding='utf-8')
    init_state(tmp_path, 'REVIEW_BEFORE_LOCK')
    for stage in EXPECTED[:5]:
        pass_with_artifact(tmp_path, stage)
    pass_stage(tmp_path, 'FORGE_GATE_QC_DEAI', artifact='lock_candidates/EP01.md')
    candidate.write_text('v2 changed after QC', encoding='utf-8')
    try:
        resolve_script_lock(tmp_path, approved=True)
    except ValueError as exc:
        assert 'LOCK_CANDIDATE_CHANGED' in str(exc)
    else:
        raise AssertionError('changed candidate must not be locked')


def test_rerun_back_to_screenwriter_invalidates_existing_script_lock(tmp_path):
    candidate = tmp_path / 'lock_candidates' / 'EP01.md'
    candidate.parent.mkdir(parents=True)
    candidate.write_text('candidate v1', encoding='utf-8')
    init_state(tmp_path, 'AUTO_ACCEPT_AFTER_QC')
    for stage in EXPECTED[:5]:
        pass_with_artifact(tmp_path, stage)
    pass_stage(tmp_path, 'FORGE_GATE_QC_DEAI', artifact='lock_candidates/EP01.md')
    state = load_state(tmp_path)
    assert state['current_stage'] == 'FORGE_AUDIT'
    assert state['lock_status'] == 'LOCKED'
    fail_stage(tmp_path, 'FORGE_AUDIT', owner_stage='SCREENWRITER', affected_ids=['SC01'], reason='script repair required')
    state = load_state(tmp_path)
    assert state['current_stage'] == 'SCREENWRITER'
    assert state['lock_status'] == 'DRAFT'
    assert 'locked_screenplay_sha256' not in state
    assert 'locked_screenplay_path' not in state
