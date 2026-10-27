#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

SCENE_HANDOFF_KEYS = [
    'scene_id','story_atom_refs','information_refs','must_be_perceptible',
    'must_remain_implicit','must_not_be_revealed','key_reaction_requests',
    'key_listener_or_third_party_response','environmental_pressure_or_release',
    'important_object_or_space_evidence','emotion_capacity_note',
]
LOCKED_REQUIRED = [
    'unit_id','locked_screenplay_path','script_version','script_review_markdown',
    'story_authority','information_ledger','audience_emotion_compat_projection','scene_handoffs',
]
SAFE_ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$')
WINDOWS_RESERVED_IDS = {
    'CON', 'PRN', 'AUX', 'NUL',
    *(f'COM{i}' for i in range(1, 10)),
    *(f'LPT{i}' for i in range(1, 10)),
}
ATOM_TYPES = {'action', 'dialogue', 'reaction', 'event', 'result', 'transition'}
REVEAL_STAGES = {'OFFSCREEN', 'LATENT', 'PARTIAL', 'READABLE', 'EMPHASIZED', 'PAYOFF'}
INFO_STATUSES = {'HIDDEN', 'PARTIAL', 'REVEALED', 'REINTERPRETED'}


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f'invalid JSON: {path}: {exc}') from exc
    if not isinstance(value, dict):
        raise ValueError(f'JSON root must be object: {path}')
    return value


def _dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _safe_id(value: object, field: str) -> str:
    text = str(value or '').strip()
    if not SAFE_ID_RE.fullmatch(text) or text.upper() in WINDOWS_RESERVED_IDS:
        raise ValueError(f'{field} must be a safe ID (letters, numbers, dot, underscore, hyphen; max 128)')
    return text


def _project_file(root: Path, value: object, field: str) -> Path:
    raw = Path(str(value or '').strip())
    if not str(raw):
        raise ValueError(f'{field} is required')
    path = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f'{field} must stay inside project root') from exc
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f'{field} missing/empty: {path}')
    return path


def _nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} must be a non-empty string')
    return value.strip()


def _number(value: object, field: str, *, minimum: float | None = None, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{field} must be a number')
    number = float(value)
    if minimum is not None and number < minimum:
        raise ValueError(f'{field} must be >= {minimum}')
    if maximum is not None and number > maximum:
        raise ValueError(f'{field} must be <= {maximum}')
    return number


def _validate_story_authority(value: object, unit_id: str) -> tuple[dict, dict[str, str]]:
    if not isinstance(value, dict) or not isinstance(value.get('atoms'), list) or not value['atoms']:
        raise ValueError('integration.afd.story_authority.atoms must be a non-empty array')
    atom_scenes: dict[str, str] = {}
    for index, atom in enumerate(value['atoms']):
        where = f'integration.afd.story_authority.atoms[{index}]'
        if not isinstance(atom, dict):
            raise ValueError(f'{where} must be an object')
        for key in ('atom_id', 'unit_id', 'scene_id', 'type', 'content', 'locked'):
            if key not in atom:
                raise ValueError(f'{where}.{key} is required')
        atom_id = _safe_id(atom['atom_id'], f'{where}.atom_id')
        if atom_id in atom_scenes:
            raise ValueError(f'{where}.atom_id is duplicated: {atom_id}')
        if str(atom['unit_id']).strip() != unit_id:
            raise ValueError(f'{where}.unit_id must equal integration.afd.unit_id')
        scene_id = _safe_id(atom['scene_id'], f'{where}.scene_id')
        if atom['type'] not in ATOM_TYPES:
            raise ValueError(f'{where}.type is unsupported: {atom["type"]}')
        _nonempty_string(atom['content'], f'{where}.content')
        if not isinstance(atom['locked'], bool):
            raise ValueError(f'{where}.locked must be boolean')
        if 'visual_coverage_required' in atom and not isinstance(atom['visual_coverage_required'], bool):
            raise ValueError(f'{where}.visual_coverage_required must be boolean')
        atom_scenes[atom_id] = scene_id
    return value, atom_scenes


def _validate_information_ledger(value: object) -> tuple[dict, set[str]]:
    if not isinstance(value, dict) or not isinstance(value.get('items'), list):
        raise ValueError('integration.afd.information_ledger.items must be an array')
    info_ids: set[str] = set()
    for index, item in enumerate(value['items']):
        where = f'integration.afd.information_ledger.items[{index}]'
        if not isinstance(item, dict):
            raise ValueError(f'{where} must be an object')
        for key in ('info_id', 'truth', 'character_knowledge', 'audience_state', 'reveal_stage', 'status'):
            if key not in item:
                raise ValueError(f'{where}.{key} is required')
        info_id = _safe_id(item['info_id'], f'{where}.info_id')
        if info_id in info_ids:
            raise ValueError(f'{where}.info_id is duplicated: {info_id}')
        _nonempty_string(item['truth'], f'{where}.truth')
        if not isinstance(item['character_knowledge'], dict) or not isinstance(item['audience_state'], dict):
            raise ValueError(f'{where}.character_knowledge and audience_state must be objects')
        if item['reveal_stage'] not in REVEAL_STAGES:
            raise ValueError(f'{where}.reveal_stage is unsupported')
        if item['status'] not in INFO_STATUSES:
            raise ValueError(f'{where}.status is unsupported')
        protected = item.get('protected_literals', [])
        if not isinstance(protected, list) or any(not isinstance(x, str) or not x.strip() for x in protected):
            raise ValueError(f'{where}.protected_literals must be an array of non-empty strings')
        info_ids.add(info_id)
    return value, info_ids


def _validate_emotion_projection(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError('integration.afd.audience_emotion_compat_projection must be an object')
    _nonempty_string(value.get('project_title'), 'emotion_projection.project_title')
    if value.get('project_type') not in {'film', 'series'}:
        raise ValueError('emotion_projection.project_type must be film or series')
    axis = value.get('axis')
    if not isinstance(axis, dict) or axis.get('type') not in {'minute', 'episode'}:
        raise ValueError('emotion_projection.axis must define type=minute|episode')
    _number(axis.get('max'), 'emotion_projection.axis.max', minimum=0.000001)
    _nonempty_string(axis.get('unit_label'), 'emotion_projection.axis.unit_label')
    if not isinstance(value.get('summary'), dict):
        raise ValueError('emotion_projection.summary must be an object')
    for field in ('phases', 'nodes', 'fatigue_zones', 'paragraphs', 'actor_emotion_tracks'):
        if not isinstance(value.get(field), list):
            raise ValueError(f'emotion_projection.{field} must be an array')
    if not value['phases'] or not value['actor_emotion_tracks']:
        raise ValueError('emotion_projection.phases and actor_emotion_tracks must be non-empty')
    for index, phase in enumerate(value['phases']):
        where = f'emotion_projection.phases[{index}]'
        if not isinstance(phase, dict):
            raise ValueError(f'{where} must be an object')
        for key in ('phase_id', 'range_label', 'name', 'primary_emotion'):
            _nonempty_string(phase.get(key), f'{where}.{key}')
        for key in ('start', 'end'):
            _number(phase.get(key), f'{where}.{key}', minimum=0)
        for key in ('entry_intensity', 'peak_intensity', 'exit_intensity'):
            _number(phase.get(key), f'{where}.{key}', minimum=0, maximum=10)
    for index, track in enumerate(value['actor_emotion_tracks']):
        where = f'emotion_projection.actor_emotion_tracks[{index}]'
        if not isinstance(track, dict) or not isinstance(track.get('points'), list) or not track['points']:
            raise ValueError(f'{where} must contain a non-empty points array')
        _nonempty_string(track.get('character_id'), f'{where}.character_id')
        _nonempty_string(track.get('character_name'), f'{where}.character_name')
        for point_index, point in enumerate(track['points']):
            point_where = f'{where}.points[{point_index}]'
            if not isinstance(point, dict):
                raise ValueError(f'{point_where} must be an object')
            _number(point.get('position'), f'{point_where}.position', minimum=0)
            _number(point.get('intensity'), f'{point_where}.intensity', minimum=0, maximum=10)
            for key in ('internal_emotion', 'performed_emotion', 'strategy', 'event_basis'):
                _nonempty_string(point.get(key), f'{point_where}.{key}')
    return value




def _require_master_stage(root: Path, expected_stage: str, *, require_locked: bool = False) -> dict:
    path = root / 'state' / 'master_orchestrator.json'
    if not path.is_file():
        raise ValueError(f'MASTER_STAGE_REQUIRED: missing {path}')
    state = _load(path)
    current = state.get('current_stage')
    if current != expected_stage:
        raise ValueError(f'MASTER_STAGE_REQUIRED: expected {expected_stage}, got {current}')
    if require_locked and state.get('lock_status') != 'LOCKED':
        raise ValueError('MASTER_LOCK_REQUIRED: locked-audit handoff requires master lock_status=LOCKED')
    return state

def _afd_namespace(payload: dict) -> dict:
    integration = payload.get('integration')
    afd = integration.get('afd') if isinstance(integration, dict) else None
    if not isinstance(afd, dict):
        raise ValueError('integration.afd object is required; compiler will not infer missing semantics')
    return afd


def _require(afd: dict, keys: list[str]) -> None:
    missing = [key for key in keys if key not in afd]
    if missing:
        raise ValueError('integration.afd missing required fields: ' + ', '.join(missing))


def _validate_forge_audit(payload: dict) -> None:
    from render_emotion_map import validate_emotion_payload

    errors = list(validate_emotion_payload(payload))
    if errors:
        raise ValueError('Forge locked-audit validation failed: ' + '; '.join(errors))


def _validate_scene_handoffs(
    value: object,
    atom_scenes: dict[str, str],
    info_ids: set[str],
) -> list[dict]:
    if not isinstance(value, list) or not value:
        raise ValueError('integration.afd.scene_handoffs must be a non-empty array')
    scene_ids: set[str] = set()
    for index, row in enumerate(value):
        where = f'integration.afd.scene_handoffs[{index}]'
        if not isinstance(row, dict):
            raise ValueError(f'{where} must be an object')
        missing = [key for key in SCENE_HANDOFF_KEYS if key not in row]
        if missing:
            raise ValueError(f'{where} missing fields: {", ".join(missing)}')
        scene_id = _safe_id(row['scene_id'], f'{where}.scene_id')
        if scene_id in scene_ids:
            raise ValueError(f'{where}.scene_id is duplicated: {scene_id}')
        scene_ids.add(scene_id)
        for key in SCENE_HANDOFF_KEYS[1:-1]:
            items = row[key]
            if not isinstance(items, list) or any(not isinstance(item, str) or not item.strip() for item in items):
                raise ValueError(f'{where}.{key} must be an array of non-empty strings')
        if not isinstance(row['emotion_capacity_note'], str):
            raise ValueError(f'{where}.emotion_capacity_note must be a string')
        for atom_id in row['story_atom_refs']:
            if atom_id not in atom_scenes:
                raise ValueError(f'{where}.story_atom_refs contains unknown atom: {atom_id}')
            if atom_scenes[atom_id] != scene_id:
                raise ValueError(f'{where}.story_atom_refs contains atom from another scene: {atom_id}')
        for info_id in row['information_refs']:
            if info_id not in info_ids:
                raise ValueError(f'{where}.information_refs contains unknown item: {info_id}')
    return value




def _validate_project_scope_against_forge(scope: dict, story_authority: dict, handoffs: list[dict]) -> list[str]:
    expected = list(scope.get('scene_ids') or [])
    expected_set = set(expected)
    story_set = {str(a.get('scene_id') or '') for a in (story_authority.get('atoms') or []) if isinstance(a, dict)}
    handoff_set = {str(h.get('scene_id') or '') for h in handoffs if isinstance(h, dict)}
    errors: list[str] = []
    if story_set != expected_set:
        errors.append(f'FORGE_PROJECT_SCOPE_INCOMPLETE: Story Authority scene set mismatch; missing={sorted(expected_set-story_set)} extra={sorted(story_set-expected_set)}')
    if handoff_set != expected_set:
        errors.append(f'FORGE_PROJECT_SCOPE_INCOMPLETE: scene_handoffs scene set mismatch; missing={sorted(expected_set-handoff_set)} extra={sorted(handoff_set-expected_set)}')
    return errors

def _commit_staged(staged_root: Path, project_root: Path, relatives: list[Path]) -> None:
    for relative in relatives:
        source = staged_root / relative
        target = project_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source, target)


def compile_design(project_root: str | Path, forge_json: str | Path, afd_visual_source: str | Path) -> dict:
    root = Path(project_root).resolve()
    _require_master_stage(root, 'DESIGN_HANDOFF')
    source = Path(forge_json).resolve()
    visual_path = Path(afd_visual_source).resolve()
    payload = _load(source)
    if (payload.get('meta') or {}).get('workflow_stage') != 'design':
        raise ValueError('DESIGN_HANDOFF requires meta.workflow_stage=design')
    afd = _afd_namespace(payload)
    story = afd.get('creative_bible_story_markdown')
    if not isinstance(story, str) or not story.strip():
        raise ValueError('integration.afd.creative_bible_story_markdown is required')
    if not visual_path.is_file() or not visual_path.read_text(encoding='utf-8').strip():
        raise ValueError(f'AFD visual production source missing/empty: {visual_path}')

    state_dir = root / 'state'
    state_dir.mkdir(parents=True, exist_ok=True)
    design_target = state_dir / 'forge_design.json'
    if source != design_target.resolve():
        shutil.copy2(source, design_target)
    visual = visual_path.read_text(encoding='utf-8').strip()
    bible = (
        '# PROJECT_CREATIVE_BIBLE\n\n'
        '<!-- authority: Forge story design + AFD visual/production specification -->\n\n'
        '## Forge 故事设计权威部分\n\n'
        + story.strip() + '\n\n'
        '## AFD 视觉与生产规范部分\n\n'
        + visual + '\n'
    )
    (root / 'PROJECT_CREATIVE_BIBLE.md').write_text(bible, encoding='utf-8')

    alignment_path = state_dir / 'forge_alignment.json'
    alignment = _load(alignment_path) if alignment_path.is_file() else {}
    alignment.update({
        'alignment_contract': 'FORGE_AFD_ALIGNMENT_V1',
        'blueprint_version': (payload.get('meta') or {}).get('blueprint_version'),
        'design_sha256': _sha(design_target),
    })
    _dump(alignment_path, alignment)
    return {'design_sha256': alignment['design_sha256'], 'creative_bible': str(root / 'PROJECT_CREATIVE_BIBLE.md')}


def compile_locked_audit(project_root: str | Path, forge_json: str | Path) -> dict:
    root = Path(project_root).resolve()
    master_state = _require_master_stage(root, 'LOCKED_AUDIT_HANDOFF', require_locked=True)
    source = Path(forge_json).resolve()
    payload = _load(source)
    if (payload.get('meta') or {}).get('workflow_stage') != 'locked_audit':
        raise ValueError('LOCKED_AUDIT_HANDOFF requires meta.workflow_stage=locked_audit')
    script_audit = payload.get('script_audit')
    if not isinstance(script_audit, dict) or script_audit.get('lock_status') != 'LOCKED':
        raise ValueError('LOCKED_AUDIT_HANDOFF requires script_audit.lock_status=LOCKED')
    _validate_forge_audit(payload)
    afd = _afd_namespace(payload)
    _require(afd, LOCKED_REQUIRED)

    unit_id = _safe_id(afd['unit_id'], 'integration.afd.unit_id')
    script_version = _nonempty_string(afd['script_version'], 'integration.afd.script_version')
    review = _nonempty_string(afd['script_review_markdown'], 'integration.afd.script_review_markdown')
    screenplay_source = _project_file(root, afd['locked_screenplay_path'], 'integration.afd.locked_screenplay_path')
    screenplay_rel = screenplay_source.relative_to(root).as_posix()
    master_rel = str(master_state.get('locked_screenplay_path') or '')
    master_sha = str(master_state.get('locked_screenplay_sha256') or '')
    current_sha = _sha(screenplay_source)
    if screenplay_rel != master_rel or not master_sha or current_sha != master_sha:
        raise ValueError(
            'MASTER_LOCK_MISMATCH: Forge AUDIT handoff screenplay path/hash does not match the screenplay locked by Master'
        )

    story_authority, atom_scenes = _validate_story_authority(afd['story_authority'], unit_id)
    information_ledger, info_ids = _validate_information_ledger(afd['information_ledger'])
    emotion_projection = _validate_emotion_projection(afd['audience_emotion_compat_projection'])
    handoffs = _validate_scene_handoffs(afd['scene_handoffs'], atom_scenes, info_ids)
    scope_path = root / 'state' / 'PROJECT_SCOPE.json'
    scope_manifest_sha256 = None
    if scope_path.is_file():
        from project_scope import validate_project_scope
        scope = _load(scope_path)
        scope_errors = validate_project_scope(root, scope)
        if scope_errors:
            raise ValueError('FORGE_PROJECT_SCOPE_INVALID: ' + '; '.join(scope_errors))
        scope_errors = _validate_project_scope_against_forge(scope, story_authority, handoffs)
        if scope_errors:
            raise ValueError('; '.join(scope_errors))
        scope_manifest_sha256 = scope.get('scope_manifest_sha256')

    audit_rel = Path('state/forge_locked_audit.json')
    screenplay_relpath = Path('screenplay') / f'{unit_id}_LOCKED_SCREENPLAY.md'
    review_rel = Path('SCRIPT_REVIEW.md')
    story_rel = Path('state/story_authority.json')
    info_rel = Path('state/information_ledger.json')
    emotion_rel = Path('state/audience_emotion_architecture.json')
    alignment_rel = Path('state/forge_alignment.json')
    causal_rels = [Path('state/audience_causal') / f'{unit_id}_{row["scene_id"]}.json' for row in handoffs]
    artifact_rels = [audit_rel, screenplay_relpath, review_rel, story_rel, info_rel, emotion_rel, *causal_rels]

    with tempfile.TemporaryDirectory(prefix='.forge-handoff-', dir=root) as tmp:
        staged = Path(tmp)
        for relative in artifact_rels:
            (staged / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, staged / audit_rel)
        shutil.copy2(screenplay_source, staged / screenplay_relpath)
        (staged / review_rel).write_text(review + '\n', encoding='utf-8')
        _dump(staged / story_rel, story_authority)
        _dump(staged / info_rel, information_ledger)
        _dump(staged / emotion_rel, emotion_projection)
        for row, relative in zip(handoffs, causal_rels):
            _dump(staged / relative, row)

        artifact_sha256 = {relative.as_posix(): _sha(staged / relative) for relative in artifact_rels}
        alignment_path = root / alignment_rel
        alignment = _load(alignment_path) if alignment_path.is_file() else {}
        record = {
            'unit_id': unit_id,
            'script_version': script_version,
            'screenplay_sha256': artifact_sha256[screenplay_relpath.as_posix()],
            'forge_audit_sha256': artifact_sha256[audit_rel.as_posix()],
            'artifact_sha256': artifact_sha256,
            'lock_status': 'LOCKED',
            'blueprint_version': (payload.get('meta') or {}).get('blueprint_version'),
            'scope_manifest_sha256': scope_manifest_sha256,
        }
        units = alignment.get('units')
        if not isinstance(units, dict):
            units = {}
        units[unit_id] = dict(record)
        alignment.update({
            'alignment_contract': 'FORGE_AFD_ALIGNMENT_V1',
            'units': units,
            'latest_unit_id': unit_id,
            **record,
        })
        _dump(staged / alignment_rel, alignment)
        _commit_staged(staged, root, [*artifact_rels, alignment_rel])
    return {'unit_id': unit_id, **alignment}


def validate_alignment(project_root: str | Path, unit_id: str | None = None) -> list[str]:
    root = Path(project_root).resolve()
    alignment_path = root / 'state' / 'forge_alignment.json'
    if not alignment_path.is_file():
        return ['missing state/forge_alignment.json']
    try:
        alignment = _load(alignment_path)
    except ValueError as exc:
        return [str(exc)]
    selected = unit_id or str(alignment.get('latest_unit_id') or alignment.get('unit_id') or '').strip()
    units = alignment.get('units')
    record = units.get(selected) if isinstance(units, dict) and selected in units else alignment
    if not isinstance(record, dict):
        return [f'missing Forge alignment record for unit: {selected or "<unknown>"}']
    errors: list[str] = []
    if record.get('lock_status') != 'LOCKED':
        errors.append('forge_alignment.lock_status must be LOCKED')
    artifacts = record.get('artifact_sha256')
    if not isinstance(artifacts, dict) or not artifacts:
        errors.append('forge_alignment.artifact_sha256 must be a non-empty object')
        return errors
    for relative, expected in artifacts.items():
        if not isinstance(relative, str) or not isinstance(expected, str) or not expected:
            errors.append(f'invalid Forge alignment artifact entry: {relative!r}')
            continue
        target = (root / relative).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            errors.append(f'Forge alignment artifact escapes project root: {relative}')
            continue
        if not target.is_file():
            errors.append(f'Forge alignment artifact missing: {relative}')
        elif _sha(target) != expected:
            errors.append(f'Forge alignment artifact hash mismatch: {relative}')
    scope_path = root / 'state' / 'PROJECT_SCOPE.json'
    if scope_path.is_file():
        try:
            scope = _load(scope_path)
            current_scope_hash = scope.get('scope_manifest_sha256')
            if current_scope_hash and record.get('scope_manifest_sha256') != current_scope_hash:
                errors.append('Forge alignment scope_manifest_sha256 does not match current PROJECT_SCOPE')
        except ValueError as exc:
            errors.append(str(exc))
    master_path = root / 'state' / 'master_orchestrator.json'
    if master_path.is_file():
        try:
            master = _load(master_path)
            locked_hash = str(master.get('locked_screenplay_sha256') or '')
            if locked_hash and record.get('screenplay_sha256') != locked_hash:
                errors.append('Forge alignment screenplay hash does not match Master lock')
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description='Deterministic Forge -> AFD handoff compiler; no semantic inference')
    parser.add_argument('--project-root', required=True)
    parser.add_argument('--stage', required=True, choices=['design','locked-audit','validate-alignment'])
    parser.add_argument('--forge-json')
    parser.add_argument('--afd-visual-source')
    args = parser.parse_args()
    try:
        if args.stage == 'validate-alignment':
            errors = validate_alignment(args.project_root)
            if errors:
                raise ValueError('; '.join(errors))
            result = {'status': 'PASS'}
        elif args.stage == 'design':
            if not args.forge_json:
                raise ValueError('--forge-json is required for design stage')
            if not args.afd_visual_source:
                raise ValueError('--afd-visual-source is required for design stage')
            result = compile_design(args.project_root, args.forge_json, args.afd_visual_source)
        else:
            if not args.forge_json:
                raise ValueError('--forge-json is required for locked-audit stage')
            result = compile_locked_audit(args.project_root, args.forge_json)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f'FAIL: {exc}')
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
