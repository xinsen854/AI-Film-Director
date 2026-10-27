#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

STAGES = [
    'PROJECT_INTAKE','FORGE_DESIGN','DESIGN_HANDOFF','CREATIVE_BIBLE',
    'SCREENWRITER','FORGE_GATE_QC_DEAI','SCRIPT_LOCK','FORGE_AUDIT',
    'LOCKED_AUDIT_HANDOFF','FORGE_EMOTION_RENDER','SCENE_INTELLIGENCE',
    'CAPABILITY_ROUTER','DIRECTOR_CRAFT','SCENE_DIRECTION','ASSET_ENGINE',
    'SPATIAL','SHOT_SEGMENT','FINAL_HARD_QC','PRODUCTION_LEDGER','EXPORTS',
]
LOCK_POLICIES = {'REVIEW_BEFORE_LOCK', 'AUTO_ACCEPT_AFTER_QC'}
STATE_REL = Path('state/master_orchestrator.json')
STAGE_REQUIREMENTS = {
    stage: 'lock_candidate_file' if stage == 'FORGE_GATE_QC_DEAI' else 'artifact'
    for stage in STAGES
    if stage != 'SCRIPT_LOCK'
}
STAGE_REQUIREMENTS['PROJECT_SCOPE_PLAN'] = 'artifact'
STAGE_REQUIREMENTS['PROJECT_ASSET_BASELINE'] = 'artifact'
STAGE_REQUIREMENTS['PROJECT_FINAL_HARD_QC'] = 'artifact'


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_path(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / STATE_REL


def _write(project_root: str | Path, state: dict) -> dict:
    path = _state_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return state


def init_state(project_root: str | Path, lock_policy: str = 'REVIEW_BEFORE_LOCK') -> dict:
    if lock_policy not in LOCK_POLICIES:
        raise ValueError(f'unsupported script_lock_policy: {lock_policy}')
    state = {
        'orchestrator_contract': 'AFD_MASTER_ORCHESTRATOR_V1',
        'current_stage': STAGES[0],
        'stage_status': 'PENDING',
        'next_stage': STAGES[1],
        'script_lock_policy': lock_policy,
        'lock_status': 'DRAFT',
        'spatial_required': None,
        'history': [],
        'rerun': None,
        'updated_at': _now(),
    }
    return _write(project_root, state)


def load_state(project_root: str | Path) -> dict:
    path = _state_path(project_root)
    if not path.is_file():
        raise FileNotFoundError(f'master orchestrator state missing: {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def _stage_index(stage: str) -> int:
    try:
        return STAGES.index(stage)
    except ValueError as exc:
        raise ValueError(f'unknown stage: {stage}') from exc


def _next_after(stage: str, state: dict) -> str | None:
    idx = _stage_index(stage)
    if stage == 'ASSET_ENGINE' and state.get('spatial_required') is False:
        return 'SHOT_SEGMENT'
    if idx + 1 >= len(STAGES):
        return None
    return STAGES[idx + 1]




def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _stage_artifact(project_root: str | Path, artifact: str | None) -> tuple[str, str | None, Path]:
    if not artifact:
        raise ValueError('STAGE_ARTIFACT_REQUIRED: PASS requires an artifact path')
    root = Path(project_root).resolve()
    raw = Path(artifact)
    path = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        rel = path.relative_to(root)
    except ValueError as exc:
        raise ValueError('STAGE_ARTIFACT_OUTSIDE_PROJECT: artifact must stay inside project root') from exc
    if not path.exists():
        raise ValueError(f'STAGE_ARTIFACT_MISSING: {path}')
    if path.is_file():
        if path.stat().st_size == 0:
            raise ValueError(f'STAGE_ARTIFACT_EMPTY: {path}')
        return rel.as_posix(), _sha256(path), path
    if path.is_dir():
        try:
            next(path.iterdir())
        except StopIteration as exc:
            raise ValueError(f'STAGE_ARTIFACT_EMPTY: {path}') from exc
        return rel.as_posix(), None, path
    raise ValueError(f'STAGE_ARTIFACT_UNSUPPORTED: {path}')


def _lock_candidate(project_root: str | Path, artifact: str | None) -> tuple[str, str]:
    try:
        rel, digest, path = _stage_artifact(project_root, artifact)
    except ValueError as exc:
        raise ValueError(f'LOCK_CANDIDATE_REQUIRED: {exc}') from exc
    if not path.is_file() or not path.read_text(encoding='utf-8').strip():
        raise ValueError(f'LOCK_CANDIDATE_REQUIRED: candidate missing/empty: {path}')
    assert digest is not None
    return rel, digest

def _read_json_object(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        raise ValueError(f'MASTER_JSON_INVALID: {path}') from exc
    if not isinstance(payload, dict):
        raise ValueError(f'MASTER_JSON_OBJECT_REQUIRED: {path}')
    return payload


def _unit_semantic_errors(project_root: str | Path, unit_id: str) -> list[str]:
    """Reuse the existing unit-consistency authority before Master advances a PU."""
    from validate_unit_consistency import validate_project_consistency
    return list(validate_project_consistency(Path(project_root).resolve(), unit_id))


def _project_ledger_shape_errors(ledger: dict, planned_units: list[str]) -> list[str]:
    """Validate only the formal film checkpoint shape already produced by Production Ledger."""
    errors: list[str] = []
    if ledger.get('scope_type') != 'film_timeline':
        return ['MASTER_LEDGER_SCOPE_INVALID: project PU loop requires film_timeline ledger']

    completed = ledger.get('completed_units')
    rows = ledger.get('film_units')
    if not isinstance(completed, list) or not all(isinstance(x, str) and x for x in completed):
        return ['MASTER_LEDGER_COMPLETED_UNITS_INVALID']
    if not isinstance(rows, list):
        return ['MASTER_LEDGER_FILM_UNITS_INVALID']
    if completed != planned_units[:len(completed)]:
        errors.append('MASTER_LEDGER_UNIT_ORDER_INVALID: completed_units must be a prefix of planned_units')

    if len(rows) != len(completed):
        errors.append('MASTER_LEDGER_UNIT_SHAPE_INVALID: film_units must correspond one-to-one with completed_units')
        return errors

    previous_end = 0.0
    for idx, (unit_id, row) in enumerate(zip(completed, rows)):
        if not isinstance(row, dict):
            errors.append(f'MASTER_LEDGER_UNIT_SHAPE_INVALID: film_units[{idx}] must be an object')
            continue
        if row.get('unit_id') != unit_id:
            errors.append(f'MASTER_LEDGER_UNIT_SHAPE_INVALID: film_units[{idx}].unit_id must equal {unit_id}')
        if row.get('status') != 'COMPLETE':
            errors.append(f'MASTER_LEDGER_UNIT_SHAPE_INVALID: {unit_id} status must be COMPLETE')
        start = row.get('start_seconds')
        end = row.get('end_seconds')
        if not isinstance(start, (int, float)) or isinstance(start, bool) or not isinstance(end, (int, float)) or isinstance(end, bool):
            errors.append(f'MASTER_LEDGER_UNIT_SHAPE_INVALID: {unit_id} requires numeric start_seconds/end_seconds')
            continue
        start_f, end_f = float(start), float(end)
        if abs(start_f - previous_end) > 0.01:
            errors.append(f'MASTER_LEDGER_TIMELINE_GAP: {unit_id} must start at {previous_end}, got {start_f}')
        if end_f <= start_f:
            errors.append(f'MASTER_LEDGER_UNIT_SHAPE_INVALID: {unit_id} end_seconds must be greater than start_seconds')
        previous_end = end_f

    coverage = ledger.get('coverage')
    covered = coverage.get('covered_seconds') if isinstance(coverage, dict) else None
    if not isinstance(covered, (int, float)) or isinstance(covered, bool) or abs(float(covered) - previous_end) > 0.01:
        errors.append('MASTER_LEDGER_COVERAGE_MISMATCH: coverage.covered_seconds must equal the last completed end_seconds')
    next_resume = ledger.get('next_resume')
    resume = next_resume.get('start_seconds') if isinstance(next_resume, dict) else None
    if not isinstance(resume, (int, float)) or isinstance(resume, bool) or abs(float(resume) - previous_end) > 0.01:
        errors.append('MASTER_LEDGER_RESUME_MISMATCH: next_resume.start_seconds must equal the last completed end_seconds')
    return errors


def _film_project_scope_required(project_root: str | Path) -> bool:
    path = Path(project_root).resolve() / 'state' / 'project_brief.json'
    if not path.is_file():
        return False
    try:
        brief = _read_json_object(path)
    except ValueError:
        return False
    production_scope = str(brief.get('production_scope') or 'PROJECT').upper()
    if production_scope not in {'PROJECT', 'UNIT', 'PILOT'}:
        raise ValueError(f'unsupported production_scope: {production_scope}')
    return brief.get('work_format') == 'film' and production_scope == 'PROJECT'


def _project_asset_baseline_errors(project_root: str | Path) -> list[str]:
    from project_asset_baseline import validate_asset_baseline_lock
    return list(validate_asset_baseline_lock(Path(project_root).resolve()))


def _project_scope_binding_errors(project_root: str | Path, state: dict) -> list[str]:
    root = Path(project_root).resolve()
    scope_path = root / 'state' / 'PROJECT_SCOPE.json'
    if not scope_path.is_file():
        return ['MASTER_PROJECT_SCOPE_MISSING']
    from project_scope import validate_project_scope
    errors = validate_project_scope(root)
    if errors:
        return ['MASTER_PROJECT_SCOPE_INVALID: ' + '; '.join(errors)]
    scope = _read_json_object(scope_path)
    if scope.get('scope_manifest_sha256') != state.get('scope_manifest_sha256'):
        return ['MASTER_SCOPE_BINDING_STALE: PROJECT_SCOPE hash changed after Master binding']
    units = scope.get('production_units')
    planned = [str(u.get('unit_id')) for u in units if isinstance(u, dict)] if isinstance(units, list) else []
    if planned != state.get('planned_units'):
        return ['MASTER_SCOPE_BINDING_STALE: planned_units no longer match PROJECT_SCOPE']
    return []


def _bind_project_scope(project_root: str | Path, state: dict, artifact_path: Path) -> None:
    root = Path(project_root).resolve()
    expected = root / 'state' / 'PROJECT_SCOPE.json'
    if artifact_path.resolve() != expected.resolve():
        raise ValueError('MASTER_PROJECT_SCOPE_ARTIFACT_REQUIRED: PROJECT_SCOPE_PLAN must bind state/PROJECT_SCOPE.json')
    from project_scope import validate_project_scope
    errors = validate_project_scope(root)
    if errors:
        raise ValueError('MASTER_PROJECT_SCOPE_INVALID: ' + '; '.join(errors))
    scope = _read_json_object(expected)
    units = scope.get('production_units')
    planned = [str(u.get('unit_id')) for u in units if isinstance(u, dict)] if isinstance(units, list) else []
    if not planned:
        raise ValueError('MASTER_PROJECT_SCOPE_UNITS_REQUIRED')
    state['project_scope_active'] = True
    state['project_stage'] = 'PROJECT_PREPRODUCTION'
    state['scope_manifest_sha256'] = scope.get('scope_manifest_sha256')
    state['planned_units'] = planned
    state['completed_units'] = []
    state['current_unit_id'] = planned[0]
    state['unit_stage'] = None


def _record(state: dict, stage: str, status: str, **extra: object) -> None:
    row = {'stage': stage, 'status': status, 'at': _now()}
    row.update({k: v for k, v in extra.items() if v is not None})
    state.setdefault('history', []).append(row)


def pass_stage(
    project_root: str | Path,
    stage: str,
    *,
    artifact: str | None = None,
    spatial_required: bool | None = None,
) -> dict:
    state = load_state(project_root)
    if state.get('current_stage') != stage:
        raise ValueError(f'OUT_OF_ORDER: expected {state.get("current_stage")}, got {stage}')
    if stage == 'SCRIPT_LOCK':
        raise ValueError('SCRIPT_LOCK must be resolved by resolve_script_lock()')
    if stage == 'FORGE_AUDIT' and state.get('lock_status') != 'LOCKED':
        raise ValueError('LOCK_GATE: Forge AUDIT requires LOCKED screenplay')
    if stage not in STAGE_REQUIREMENTS:
        raise ValueError(f'no artifact requirement declared for stage: {stage}')

    if spatial_required is not None:
        if stage not in {'CAPABILITY_ROUTER', 'ASSET_ENGINE'}:
            raise ValueError('spatial_required may only be set by routing/asset boundary')
        state['spatial_required'] = bool(spatial_required)

    artifact_sha256: str | None = None
    artifact_path: Path | None = None
    if stage == 'FORGE_GATE_QC_DEAI':
        candidate_rel, candidate_sha = _lock_candidate(project_root, artifact)
        state['lock_candidate_path'] = candidate_rel
        state['lock_candidate_sha256'] = candidate_sha
        artifact = candidate_rel
        artifact_sha256 = candidate_sha
    else:
        artifact, artifact_sha256, artifact_path = _stage_artifact(project_root, artifact)

    if stage == 'PROJECT_ASSET_BASELINE':
        assert artifact_path is not None
        root = Path(project_root).resolve()
        expected = root / 'state' / 'project_asset_baseline.json'
        if artifact_path.resolve() != expected.resolve():
            raise ValueError('MASTER_PROJECT_ASSET_BASELINE_ARTIFACT_REQUIRED: stage must bind state/project_asset_baseline.json')
        baseline_errors = _project_asset_baseline_errors(root)
        if baseline_errors:
            raise ValueError('MASTER_PROJECT_ASSET_BASELINE_INVALID: ' + '; '.join(baseline_errors))
        receipt = _read_json_object(expected)
        req_hash = receipt.get('requirements_manifest_sha256')
        lock_hash = receipt.get('baseline_lock_sha256')
        if not isinstance(req_hash, str) or not req_hash or not isinstance(lock_hash, str) or not lock_hash:
            raise ValueError('MASTER_PROJECT_ASSET_BASELINE_BINDING_MISSING')
        old_req = state.get('project_asset_requirements_sha256')
        old_lock = state.get('project_asset_baseline_lock_sha256')
        if old_req not in (None, '', req_hash) or old_lock not in (None, '', lock_hash):
            raise ValueError('MASTER_PROJECT_ASSET_BASELINE_BINDING_STALE')
        state['project_asset_requirements_sha256'] = req_hash
        state['project_asset_baseline_lock_sha256'] = lock_hash
        _record(state, stage, 'PASS', artifact=artifact, artifact_sha256=artifact_sha256)
        state['rerun'] = None
        state['current_stage'] = 'SCENE_INTELLIGENCE'
        state['stage_status'] = 'PENDING'
        state['next_stage'] = 'CAPABILITY_ROUTER'
        state['unit_stage'] = 'SCENE_INTELLIGENCE'
        state['project_stage'] = 'UNIT_PRODUCTION'
        state['updated_at'] = _now()
        return _write(project_root, state)

    if stage == 'PROJECT_FINAL_HARD_QC':
        assert artifact_path is not None
        root = Path(project_root).resolve()
        expected = root / 'FINAL_QC.md'
        if artifact_path.resolve() != expected.resolve():
            raise ValueError('MASTER_PROJECT_QC_ARTIFACT_REQUIRED: PROJECT_FINAL_HARD_QC must bind FINAL_QC.md')
        scope_errors = _project_scope_binding_errors(root, state)
        if scope_errors:
            raise ValueError('; '.join(scope_errors))
        from hard_delivery_qc import validate_hard_delivery
        hard_errors = validate_hard_delivery(root, scope='project')
        if hard_errors:
            raise ValueError('MASTER_PROJECT_QC_FAILED: ' + '; '.join(hard_errors))
        text = expected.read_text(encoding='utf-8', errors='replace')
        if not re.search(r'^##\s+Project Result\s*$\s*^PASS\s*$', text, flags=re.MULTILINE | re.IGNORECASE):
            raise ValueError('MASTER_PROJECT_QC_RESULT_NOT_PASS: FINAL_QC.md must contain Project Result PASS')
        _record(state, stage, 'PASS', artifact=artifact, artifact_sha256=artifact_sha256)
        state['rerun'] = None
        state['current_stage'] = 'EXPORTS'
        state['stage_status'] = 'PENDING'
        state['next_stage'] = None
        state['project_stage'] = 'EXPORTS'
        state['updated_at'] = _now()
        return _write(project_root, state)

    if stage == 'PROJECT_SCOPE_PLAN':
        assert artifact_path is not None
        _bind_project_scope(project_root, state, artifact_path)
        _record(state, stage, 'PASS', artifact=artifact, artifact_sha256=artifact_sha256)
        state['rerun'] = None
        state['current_stage'] = 'FORGE_AUDIT'
        state['stage_status'] = 'PENDING'
        state['next_stage'] = 'LOCKED_AUDIT_HANDOFF'
        state['updated_at'] = _now()
        return _write(project_root, state)

    # Project-scoped film production is a PU loop, not a one-pass global stage chain.
    # Consume only a formally checkpointed and semantically valid current PU.
    project_loop_result: dict | None = None
    if stage == 'PRODUCTION_LEDGER' and state.get('project_scope_active') is True:
        root = Path(project_root).resolve()
        ledger_path = root / 'PRODUCTION_LEDGER.json'
        if Path(artifact).as_posix() != 'PRODUCTION_LEDGER.json':
            raise ValueError('MASTER_PRODUCTION_LEDGER_ARTIFACT_REQUIRED: project PU loop must bind PRODUCTION_LEDGER.json')
        scope_errors = _project_scope_binding_errors(root, state)
        if scope_errors:
            raise ValueError('; '.join(scope_errors))
        ledger = _read_json_object(ledger_path)
        planned = state.get('planned_units')
        current_unit = state.get('current_unit_id')
        if not isinstance(planned, list) or not planned or not all(isinstance(x, str) and x for x in planned):
            raise ValueError('MASTER_PLANNED_UNITS_REQUIRED')
        if not isinstance(current_unit, str) or current_unit not in planned:
            raise ValueError('MASTER_CURRENT_UNIT_INVALID')
        completed = ledger.get('completed_units')
        if not isinstance(completed, list) or current_unit not in completed:
            raise ValueError(f'MASTER_CURRENT_UNIT_NOT_CHECKPOINTED: {current_unit}')
        semantic_errors = _unit_semantic_errors(root, current_unit)
        if semantic_errors:
            raise ValueError('MASTER_CURRENT_UNIT_SEMANTIC_QC_FAILED: ' + '; '.join(semantic_errors))
        ledger_errors = _project_ledger_shape_errors(ledger, planned)
        if ledger_errors:
            raise ValueError('; '.join(ledger_errors))
        project_loop_result = {'planned': planned, 'completed': list(completed)}

    _record(state, stage, 'PASS', artifact=artifact, artifact_sha256=artifact_sha256)
    state['rerun'] = None

    if project_loop_result is not None:
        planned = project_loop_result['planned']
        completed = project_loop_result['completed']
        state['completed_units'] = completed
        if len(completed) < len(planned):
            state['current_unit_id'] = planned[len(completed)]
            state['current_stage'] = 'SCENE_INTELLIGENCE'
            state['stage_status'] = 'PENDING'
            state['next_stage'] = 'CAPABILITY_ROUTER'
            state['unit_stage'] = 'SCENE_INTELLIGENCE'
            state['project_stage'] = 'UNIT_PRODUCTION'
            state['spatial_required'] = None
        else:
            state['current_unit_id'] = None
            state['current_stage'] = 'PROJECT_FINAL_HARD_QC'
            state['stage_status'] = 'PENDING'
            state['next_stage'] = 'EXPORTS'
            state['unit_stage'] = None
            state['project_stage'] = 'PROJECT_FINAL_HARD_QC'
        state['updated_at'] = _now()
        return _write(project_root, state)

    if stage == 'FORGE_EMOTION_RENDER' and state.get('project_scope_active') is True:
        state['current_stage'] = 'PROJECT_ASSET_BASELINE'
        state['stage_status'] = 'PENDING'
        state['next_stage'] = 'SCENE_INTELLIGENCE'
        state['project_stage'] = 'PROJECT_ASSET_BASELINE'
        state['updated_at'] = _now()
        return _write(project_root, state)

    if stage == 'FORGE_GATE_QC_DEAI':
        state['current_stage'] = 'SCRIPT_LOCK'
        if state['script_lock_policy'] == 'REVIEW_BEFORE_LOCK':
            state['stage_status'] = 'WAITING_FOR_SCRIPT_APPROVAL'
            state['next_stage'] = None
        else:
            state['stage_status'] = 'AUTO_ACCEPTING'
            state['next_stage'] = 'FORGE_AUDIT'
            _record(
                state,
                'SCRIPT_LOCK',
                'PASS',
                policy='AUTO_ACCEPT_AFTER_QC',
                artifact=state.get('lock_candidate_path'),
                artifact_sha256=state.get('lock_candidate_sha256'),
            )
            state['lock_status'] = 'LOCKED'
            state['locked_screenplay_path'] = state.get('lock_candidate_path')
            state['locked_screenplay_sha256'] = state.get('lock_candidate_sha256')
            if _film_project_scope_required(project_root):
                state['current_stage'] = 'PROJECT_SCOPE_PLAN'
                state['stage_status'] = 'PENDING'
                state['next_stage'] = 'FORGE_AUDIT'
            else:
                state['current_stage'] = 'FORGE_AUDIT'
                state['stage_status'] = 'PENDING'
                state['next_stage'] = 'LOCKED_AUDIT_HANDOFF'
        state['updated_at'] = _now()
        return _write(project_root, state)

    nxt = _next_after(stage, state)
    if stage == 'ASSET_ENGINE' and state.get('spatial_required') is False:
        _record(state, 'SPATIAL', 'SKIPPED', reason='Capability Router did not require spatial narrative')
    state['current_stage'] = nxt or 'COMPLETED'
    state['stage_status'] = 'PENDING' if nxt else 'COMPLETED'
    state['next_stage'] = _next_after(nxt, state) if nxt else None
    state['updated_at'] = _now()
    return _write(project_root, state)


def resolve_script_lock(project_root: str | Path, *, approved: bool | None = None) -> dict:
    state = load_state(project_root)
    if state.get('current_stage') != 'SCRIPT_LOCK':
        raise ValueError(f'LOCK_STAGE_REQUIRED: current={state.get("current_stage")}')
    policy = state.get('script_lock_policy')
    if policy == 'AUTO_ACCEPT_AFTER_QC':
        decision = True
    else:
        if approved is not True:
            raise ValueError('LOCK_APPROVAL_REQUIRED: REVIEW_BEFORE_LOCK requires explicit approved=True')
        decision = True
    if decision:
        candidate_rel = state.get('lock_candidate_path')
        expected_sha = state.get('lock_candidate_sha256')
        current_rel, current_sha = _lock_candidate(project_root, candidate_rel)
        if not expected_sha or current_sha != expected_sha:
            raise ValueError('LOCK_CANDIDATE_CHANGED: candidate bytes changed after Forge QC; rerun Gate/QC before locking')
        _record(state, 'SCRIPT_LOCK', 'PASS', policy=policy, artifact=current_rel, artifact_sha256=current_sha)
        state['lock_status'] = 'LOCKED'
        state['locked_screenplay_path'] = current_rel
        state['locked_screenplay_sha256'] = current_sha
        if _film_project_scope_required(project_root):
            state['current_stage'] = 'PROJECT_SCOPE_PLAN'
            state['stage_status'] = 'PENDING'
            state['next_stage'] = 'FORGE_AUDIT'
        else:
            state['current_stage'] = 'FORGE_AUDIT'
            state['stage_status'] = 'PENDING'
            state['next_stage'] = 'LOCKED_AUDIT_HANDOFF'
        state['updated_at'] = _now()
    return _write(project_root, state)


def fail_stage(
    project_root: str | Path,
    stage: str,
    *,
    owner_stage: str,
    affected_ids: list[str] | None = None,
    reason: str | None = None,
) -> dict:
    state = load_state(project_root)
    if state.get('current_stage') != stage:
        raise ValueError(f'OUT_OF_ORDER_FAIL: expected {state.get("current_stage")}, got {stage}')
    if owner_stage not in STAGES:
        raise ValueError(f'unknown owner_stage: {owner_stage}')
    if _stage_index(owner_stage) > _stage_index(stage):
        raise ValueError('owner_stage cannot be downstream of failed stage')
    _record(state, stage, 'FAIL', reason=reason)
    # Any rerun that can rewrite screenplay bytes invalidates the previous lock.
    # This prevents a downstream failure from silently keeping a LOCKED marker on
    # pages that are about to be regenerated or De-AI repaired.
    if state.get('lock_status') == 'LOCKED' and _stage_index(owner_stage) <= _stage_index('FORGE_GATE_QC_DEAI'):
        state['lock_status'] = 'DRAFT'
        for key in ('locked_screenplay_path', 'locked_screenplay_sha256', 'lock_candidate_path', 'lock_candidate_sha256'):
            state.pop(key, None)
    affected = list(affected_ids or [])
    state['rerun'] = {
        'failed_stage': stage,
        'owner_stage': owner_stage,
        'affected_ids': affected,
        'do_not_rerun_before_owner': True,
        'reason': reason,
    }
    if state.get('project_scope_active') is True and affected and _stage_index(owner_stage) <= _stage_index('PRODUCTION_LEDGER'):
        planned = state.get('planned_units')
        if isinstance(planned, list):
            rerun_units = [unit_id for unit_id in planned if unit_id in affected]
            if rerun_units:
                state['current_unit_id'] = rerun_units[0]
    state['current_stage'] = owner_stage
    state['stage_status'] = 'RERUN_REQUIRED'
    state['next_stage'] = _next_after(owner_stage, state)
    state['updated_at'] = _now()
    return _write(project_root, state)


def main() -> int:
    parser = argparse.ArgumentParser(description='AFD Master Orchestrator deterministic stage/lock controller')
    parser.add_argument('--project-root', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    p_init = sub.add_parser('init')
    p_init.add_argument('--lock-policy', choices=sorted(LOCK_POLICIES), default='REVIEW_BEFORE_LOCK')
    p_pass = sub.add_parser('pass')
    p_pass.add_argument('--stage', required=True, choices=STAGES + ['PROJECT_SCOPE_PLAN', 'PROJECT_ASSET_BASELINE', 'PROJECT_FINAL_HARD_QC'])
    p_pass.add_argument('--artifact')
    p_pass.add_argument('--spatial-required', choices=['true', 'false'])
    p_lock = sub.add_parser('lock')
    p_lock.add_argument('--approve', action='store_true')
    p_fail = sub.add_parser('fail')
    p_fail.add_argument('--stage', required=True, choices=STAGES)
    p_fail.add_argument('--owner-stage', required=True, choices=STAGES)
    p_fail.add_argument('--affected-id', action='append', default=[])
    p_fail.add_argument('--reason')
    sub.add_parser('show')
    args = parser.parse_args()

    root = args.project_root
    if args.command == 'init':
        state = init_state(root, args.lock_policy)
    elif args.command == 'pass':
        spatial = None if args.spatial_required is None else args.spatial_required == 'true'
        state = pass_stage(root, args.stage, artifact=args.artifact, spatial_required=spatial)
    elif args.command == 'lock':
        state = resolve_script_lock(root, approved=args.approve)
    elif args.command == 'fail':
        state = fail_stage(root, args.stage, owner_stage=args.owner_stage, affected_ids=args.affected_id, reason=args.reason)
    else:
        state = load_state(root)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
