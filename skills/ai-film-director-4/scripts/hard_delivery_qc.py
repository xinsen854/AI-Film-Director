#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from validate_unit_consistency import validate_project_consistency
from project_scope import validate_project_scope
from project_asset_baseline import validate_asset_baseline_lock

FILM_FORMATS = {'film', 'short_film'}
SERIES_FORMATS = {'series', 'short_series'}
PROMPT_KEYS = ('generation_goal', 'reference_roles', 'initial_state', 'sound', 'keep_consistent', 'local_constraints')
NEUTRAL_TEXTS = {'', '无', '无变化', '不变', 'none', 'no change', 'unchanged', 'neutral'}


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _pattern_key(value: Any) -> str:
    text = str(value or '').lower().strip()
    return re.sub(r'[\s\W_]+', '', text, flags=re.UNICODE)


def _has_real_progression(row: dict) -> bool:
    return sum(
        1 for key in ('relationship_change', 'information_change', 'power_change', 'stakes_change')
        if _has_content(row.get(key))
    ) >= 2


def detect_repeated_dramatic_patterns(rows: list[dict]) -> list[str]:
    """Reject repeated engines/hooks only when later uses lack real dramatic progression."""
    errors: list[str] = []
    for window in (rows[index:index + 3] for index in range(max(0, len(rows) - 2))):
        if len(window) < 3 or not all(isinstance(row, dict) for row in window):
            continue
        ids = '→'.join(str(row.get('unit_id') or '?') for row in window)
        engines = [_pattern_key(row.get('dramatic_engine')) for row in window]
        hooks = [_pattern_key(row.get('hook_structure')) for row in window]
        later_progresses = all(_has_real_progression(row) for row in window[1:])
        if engines[0] and len(set(engines)) == 1 and not later_progresses:
            errors.append(f'HARD_REPEATED_PLOT_ENGINE：{ids} 重复同一戏剧发动机，后续没有足够的关系/信息/权力/风险推进')
        if hooks[0] and len(set(hooks)) == 1 and not later_progresses:
            errors.append(f'HARD_MECHANICAL_HOOK：{ids} 重复同一悬念钩子公式，后续没有足够的剧情增量')
    return errors


def _unit_key(value: str) -> tuple[str, int, str]:
    text = str(value or '')
    match = re.fullmatch(r'([A-Za-z]+)(\d+)', text)
    if not match:
        return (text, 0, text)
    return (match.group(1).upper(), int(match.group(2)), text)


def _completed_units(ledger: dict) -> list[str]:
    if ledger.get('scope_type') == 'episodes':
        return [str(x) for x in ledger.get('completed_episodes', []) if isinstance(x, str)]
    return [str(x) for x in ledger.get('completed_units', []) if isinstance(x, str)]


def _validate_runtime_bounds(brief: dict, ledger: dict, errors: list[str]) -> None:
    work_format = brief.get('work_format')
    if work_format in SERIES_FORMATS:
        minimum = brief.get('minimum_episode_runtime_seconds')
        maximum = brief.get('maximum_episode_runtime_seconds')
        if minimum is None and maximum is None:
            return  # 不替用户发明容差范围。
        if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)) or minimum <= 0 or maximum < minimum:
            errors.append(f'HARD_RUNTIME_BOUNDS_INVALID：单集时长范围非法 {minimum}~{maximum}')
            return
        for episode in ledger.get('episodes', []) if isinstance(ledger.get('episodes'), list) else []:
            if not isinstance(episode, dict) or episode.get('status') != 'COMPLETE':
                continue
            runtime = episode.get('actual_runtime_seconds')
            if not isinstance(runtime, (int, float)) or runtime < minimum or runtime > maximum:
                errors.append(
                    f'HARD_EPISODE_RUNTIME_OUT_OF_RANGE：{episode.get("episode_id") or episode.get("unit_id")} '
                    f'实际={runtime}s，确认范围={minimum}~{maximum}s'
                )
    elif work_format in FILM_FORMATS:
        minimum = brief.get('minimum_total_runtime_seconds')
        maximum = brief.get('maximum_total_runtime_seconds')
        if minimum is None and maximum is None:
            return
        if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)) or minimum <= 0 or maximum < minimum:
            errors.append(f'HARD_RUNTIME_BOUNDS_INVALID：电影总时长范围非法 {minimum}~{maximum}')
            return
        coverage = ledger.get('coverage') if isinstance(ledger.get('coverage'), dict) else {}
        runtime = coverage.get('covered_seconds')
        if not isinstance(runtime, (int, float)) or runtime < minimum or runtime > maximum:
            errors.append(f'HARD_FILM_RUNTIME_OUT_OF_RANGE：实际={runtime}s，确认范围={minimum}~{maximum}s')


def _validate_sh_gu_prompt(root: Path, ledger: dict, errors: list[str]) -> None:
    for unit_id in _completed_units(ledger):
        path = root / 'storyboard' / f'{unit_id}_STORYBOARD.json'
        data = _load(path)
        if not data:
            errors.append(f'HARD_SH_GU_PROMPT_MISSING：{unit_id}缺少结构化分镜JSON')
            continue
        shots = data.get('edit_shots')
        gus = data.get('generation_units')
        if not isinstance(shots, list) or not shots:
            errors.append(f'HARD_SH_GU_PROMPT_MISSING：{unit_id}没有正式SH')
            continue
        if not isinstance(gus, list) or not gus:
            errors.append(f'HARD_SH_GU_PROMPT_MISSING：{unit_id}有SH但没有GU/最终Prompt')
            continue

        gu_map: dict[str, dict] = {}
        membership: dict[str, set[str]] = {}
        for gu in gus:
            if not isinstance(gu, dict):
                continue
            gid = str(gu.get('generation_unit_id') or '').strip()
            if not gid:
                continue
            gu_map[gid] = gu
            members = gu.get('member_edit_shots') if isinstance(gu.get('member_edit_shots'), list) else []
            membership[gid] = {str(x) for x in members}
            phases = gu.get('phases')
            sections = gu.get('prompt_sections')
            if not isinstance(phases, list) or not phases:
                errors.append(f'HARD_SH_GU_PROMPT_MISSING：{unit_id}/{gid}缺少PH阶段推进')
            if not isinstance(sections, dict) or any(not _has_content(sections.get(key)) for key in PROMPT_KEYS):
                errors.append(f'HARD_SH_GU_PROMPT_MISSING：{unit_id}/{gid}最终视频Prompt结构不完整')

        for shot in shots:
            if not isinstance(shot, dict):
                continue
            sid = str(shot.get('edit_shot_id') or 'UNKNOWN_SHOT')
            gid = str(shot.get('generation_unit_id') or '').strip()
            if not gid or gid not in gu_map or sid not in membership.get(gid, set()):
                errors.append(f'HARD_SH_GU_PROMPT_MISSING：{unit_id}/{sid}没有被有效GU完整承接')


def _iter_assets(lib: dict):
    for group in ('character_assets', 'location_assets', 'prop_assets', 'g_assets'):
        for record in lib.get(group, []) if isinstance(lib.get(group), list) else []:
            if isinstance(record, dict):
                yield group, record
    for record in lib.get('persistent_states', []) if isinstance(lib.get('persistent_states'), list) else []:
        if isinstance(record, dict):
            yield 'persistent_states', record


def _asset_id(record: dict) -> str:
    return str(record.get('asset_id') or record.get('state_id') or 'UNKNOWN_ASSET')


def _is_required_asset(mode: str, group: str, record: dict) -> bool:
    if record.get('required_for_final_delivery') is True:
        return True
    if mode == 'all_required':
        return True
    if mode == 'core_assets':
        aid = _asset_id(record)
        if group == 'character_assets' and aid.startswith('A'):
            return True
        if group == 'persistent_states' and str(record.get('inherits_from') or '').startswith('A'):
            return True
    return False


def _validate_required_asset_status(root: Path, brief: dict, errors: list[str]) -> None:
    mode = str(brief.get('asset_production_mode') or '')
    if mode in {'', 'prompts_only'}:
        return
    data = _load(root / 'assets' / 'ASSET_LIBRARY.json')
    lib = data.get('ASSET_LIBRARY') if isinstance(data.get('ASSET_LIBRARY'), dict) else None
    if lib is None:
        errors.append('HARD_REQUIRED_ASSET_MISSING：需要生成视觉资产，但ASSET_LIBRARY.json不存在或无效')
        return
    for group, record in _iter_assets(lib):
        if not _is_required_asset(mode, group, record):
            continue
        status = str(record.get('image_status') or 'MISSING')
        if status != 'GENERATED':
            errors.append(f'HARD_REQUIRED_ASSET_MISSING：{_asset_id(record)}为必要资产，当前状态={status}')


def _validate_clear_axis_breaks(root: Path, ledger: dict, errors: list[str]) -> None:
    """Only catch explicit same-axis side flips. Full continuity validation belongs to item 6."""
    for unit_id in _completed_units(ledger):
        data = _load(root / 'storyboard' / f'{unit_id}_STORYBOARD.json')
        shots = data.get('edit_shots') if isinstance(data.get('edit_shots'), list) else []
        previous: dict | None = None
        for shot in shots:
            if not isinstance(shot, dict):
                continue
            if previous is not None and str(previous.get('scene_id') or '') == str(shot.get('scene_id') or ''):
                p = previous.get('axis_and_gaze') if isinstance(previous.get('axis_and_gaze'), dict) else {}
                c = shot.get('axis_and_gaze') if isinstance(shot.get('axis_and_gaze'), dict) else {}
                same_axis = _has_content(p.get('axis')) and str(p.get('axis')) == str(c.get('axis'))
                side_flip = _has_content(p.get('camera_side')) and _has_content(c.get('camera_side')) and str(p.get('camera_side')) != str(c.get('camera_side'))
                explicit_permission = p.get('cross_axis_allowed') is True or c.get('cross_axis_allowed') is True
                if same_axis and side_flip and not explicit_permission:
                    errors.append(
                        f'HARD_CONTINUITY_BREAK：{unit_id}/{previous.get("edit_shot_id")}→{shot.get("edit_shot_id")} '
                        f'同一轴线{p.get("axis")}从{p.get("camera_side")}侧跳到{c.get("camera_side")}侧，未声明允许越轴'
                    )
            previous = shot


def _scene_result(path: Path) -> dict:
    data = _load(path)
    result = data.get('SCENE_INTELLIGENCE_RESULT') if isinstance(data.get('SCENE_INTELLIGENCE_RESULT'), dict) else {}
    return result


def _unit_scene_results(root: Path, unit_id: str) -> list[dict]:
    base = root / 'state' / 'scene_intelligence'
    results: list[dict] = []
    if base.is_dir():
        for path in sorted(base.glob(f'{unit_id}_SC*_scene_intelligence.json')):
            result = _scene_result(path)
            if result:
                results.append(result)
    if results:
        return results
    legacy = _scene_result(base / f'{unit_id}_scene_intelligence.json')
    return [legacy] if legacy else []


def _neutral(value: Any) -> bool:
    return str(value or '').strip().lower() in NEUTRAL_TEXTS


def _scene_signature(result: dict) -> str:
    dramatic = result.get('dramatic_function') if isinstance(result.get('dramatic_function'), dict) else {}
    emotional = result.get('emotional_mechanism') if isinstance(result.get('emotional_mechanism'), dict) else {}
    relationship = result.get('relationship_dynamic') if isinstance(result.get('relationship_dynamic'), dict) else {}
    power = result.get('power_dynamic') if isinstance(result.get('power_dynamic'), dict) else {}
    subtext = result.get('subtext') if isinstance(result.get('subtext'), dict) else {}
    beats = result.get('beat_map') if isinstance(result.get('beat_map'), list) else []
    signature = {
        'dramatic_function': dramatic.get('primary'),
        'interaction_form': result.get('interaction_form'),
        'emotional_mechanism': emotional.get('primary'),
        'relationship_start': relationship.get('start'),
        'relationship_end': relationship.get('end'),
        'power_direction': power.get('direction'),
        'subtext_hidden': subtext.get('hidden_layer'),
        'beat_pattern': [b.get('change_basis') for b in beats if isinstance(b, dict)],
    }
    if not any(_has_content(value) for value in signature.values()):
        return ''
    return json.dumps(signature, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _scene_has_progression(result: dict) -> bool:
    relationship = result.get('relationship_dynamic') if isinstance(result.get('relationship_dynamic'), dict) else {}
    if not _neutral(relationship.get('delta')):
        return True
    power = result.get('power_dynamic') if isinstance(result.get('power_dynamic'), dict) else {}
    if isinstance(power.get('shift_points'), list) and power.get('shift_points'):
        return True
    if not _neutral(power.get('direction')):
        return True
    info = result.get('information_state') if isinstance(result.get('information_state'), dict) else {}
    if isinstance(info.get('reveal_in_scene'), list) and info.get('reveal_in_scene'):
        return True
    beats = result.get('beat_map') if isinstance(result.get('beat_map'), list) else []
    for beat in beats:
        if isinstance(beat, dict) and not _neutral(beat.get('change_basis')):
            return True
    return False


def _validate_repeated_template(root: Path, brief: dict, ledger: dict, errors: list[str]) -> None:
    if brief.get('work_format') not in SERIES_FORMATS:
        return  # 不把电影中的蒙太奇/平行结构误当“流量模板”。
    records: list[tuple[str, str, bool, bool]] = []
    pattern_rows: list[dict] = []
    for unit_id in sorted(_completed_units(ledger), key=_unit_key):
        results = _unit_scene_results(root, unit_id)
        if not results:
            continue  # 没有结构证据，不凭空判重复。
        scene_signatures = [_scene_signature(result) for result in results]
        scene_signatures = [item for item in scene_signatures if item]
        if not scene_signatures:
            continue
        signature = json.dumps(scene_signatures, ensure_ascii=False, separators=(',', ':'))
        intentional = any(bool(str(result.get('intentional_repetition_reason') or '').strip()) for result in results)
        progressed = any(_scene_has_progression(result) for result in results)
        records.append((unit_id, signature, progressed, intentional))
        engines = [str(result.get('dramatic_engine') or '').strip() for result in results if str(result.get('dramatic_engine') or '').strip()]
        hooks = []
        for result in results:
            hook = result.get('hook') if isinstance(result.get('hook'), dict) else {}
            value = str(result.get('hook_structure') or hook.get('structure') or '').strip()
            if value:
                hooks.append(value)
        relationship = [
            str((result.get('relationship_dynamic') or {}).get('delta') or '').strip()
            for result in results if isinstance(result.get('relationship_dynamic'), dict)
        ]
        information = [
            str((result.get('information_state') or {}).get('reveal_in_scene') or '').strip()
            for result in results if isinstance(result.get('information_state'), dict)
        ]
        power = [
            str((result.get('power_dynamic') or {}).get('direction') or '').strip()
            for result in results if isinstance(result.get('power_dynamic'), dict)
        ]
        pattern_rows.append({
            'unit_id': unit_id,
            'dramatic_engine': ' + '.join(engines),
            'hook_structure': ' + '.join(hooks),
            'relationship_change': '；'.join(item for item in relationship if not _neutral(item)),
            'information_change': '；'.join(item for item in information if not _neutral(item)),
            'power_change': '；'.join(item for item in power if not _neutral(item)),
            'stakes_change': 'intentional progression' if progressed and intentional else '',
        })
    for i in range(len(records) - 2):
        window = records[i:i + 3]
        if len({item[1] for item in window}) != 1:
            continue
        if not window[1][2] and not window[2][2] and not any(item[3] for item in window):
            errors.append(
                'HARD_REPEATED_PLOT_TEMPLATE：连续三个生产单元机械复用同一结构，且后两单元没有新的关系/权力/信息/节拍推进：'
                + ','.join(item[0] for item in window)
            )
    errors.extend(detect_repeated_dramatic_patterns(pattern_rows))


def _project_ledger_errors(ledger: dict, planned_units: list[str]) -> list[str]:
    errors: list[str] = []
    if ledger.get('scope_type') != 'film_timeline':
        return ['HARD_PROJECT_LEDGER_SCOPE_INVALID：Project QC requires film_timeline ledger']
    completed = ledger.get('completed_units')
    rows = ledger.get('film_units')
    if not isinstance(completed, list) or not all(isinstance(x, str) and x for x in completed):
        return ['HARD_PROJECT_LEDGER_UNIT_SHAPE_INVALID：completed_units invalid']
    if completed != planned_units[:len(completed)]:
        errors.append('HARD_PROJECT_LEDGER_UNIT_ORDER_INVALID：completed_units must be a planned_units prefix')
    if not isinstance(rows, list) or len(rows) != len(completed):
        errors.append('HARD_PROJECT_LEDGER_UNIT_SHAPE_INVALID：film_units must correspond one-to-one with completed_units')
        return errors
    previous_end = 0.0
    for idx, (uid, row) in enumerate(zip(completed, rows)):
        if not isinstance(row, dict) or row.get('unit_id') != uid or row.get('status') != 'COMPLETE':
            errors.append(f'HARD_PROJECT_LEDGER_UNIT_SHAPE_INVALID：film_units[{idx}] does not formally checkpoint {uid}')
            continue
        start, end = row.get('start_seconds'), row.get('end_seconds')
        if not isinstance(start, (int, float)) or isinstance(start, bool) or not isinstance(end, (int, float)) or isinstance(end, bool):
            errors.append(f'HARD_PROJECT_LEDGER_UNIT_SHAPE_INVALID：{uid} start/end must be numeric')
            continue
        start_f, end_f = float(start), float(end)
        if abs(start_f - previous_end) > 0.01:
            errors.append(f'HARD_PROJECT_LEDGER_TIMELINE_GAP：{uid} starts at {start_f}, expected {previous_end}')
        if end_f <= start_f:
            errors.append(f'HARD_PROJECT_LEDGER_UNIT_SHAPE_INVALID：{uid} end_seconds must exceed start_seconds')
        previous_end = end_f
    coverage = ledger.get('coverage') if isinstance(ledger.get('coverage'), dict) else {}
    covered = coverage.get('covered_seconds')
    if not isinstance(covered, (int, float)) or isinstance(covered, bool) or abs(float(covered) - previous_end) > 0.01:
        errors.append('HARD_PROJECT_LEDGER_COVERAGE_MISMATCH：covered_seconds must equal the last completed end_seconds')
    resume = ledger.get('next_resume', {}).get('start_seconds') if isinstance(ledger.get('next_resume'), dict) else None
    if not isinstance(resume, (int, float)) or isinstance(resume, bool) or abs(float(resume) - previous_end) > 0.01:
        errors.append('HARD_PROJECT_LEDGER_RESUME_MISMATCH：next_resume.start_seconds must equal the last completed end_seconds')
    return errors


def _project_scope_qc(root: Path, brief: dict, ledger: dict, errors: list[str]) -> None:
    scope_path = root / 'state' / 'PROJECT_SCOPE.json'
    scope = _load(scope_path)
    if not scope:
        errors.append('HARD_PROJECT_SCOPE_MISSING：state/PROJECT_SCOPE.json is required')
        return
    scope_errors = validate_project_scope(root)
    errors.extend(f'HARD_PROJECT_SCOPE_INVALID：{item}' for item in scope_errors)
    units = scope.get('production_units') if isinstance(scope.get('production_units'), list) else []
    planned = [str(u.get('unit_id')) for u in units if isinstance(u, dict) and str(u.get('unit_id') or '').strip()]
    expected_scenes = {str(x) for x in scope.get('scene_ids', []) if isinstance(x, str)}
    completed = [str(x) for x in ledger.get('completed_units', []) if isinstance(x, str)]
    if not completed:
        errors.append('HARD_PROJECT_NO_COMPLETED_UNITS：Project QC cannot PASS an empty completion set')
    if completed != planned:
        missing = [u for u in planned if u not in set(completed)]
        extra = [u for u in completed if u not in set(planned)]
        errors.append(f'HARD_PROJECT_UNIT_COVERAGE_INCOMPLETE：missing={missing} extra={extra}')
    errors.extend(_project_ledger_errors(ledger, planned))
    if ledger.get('status') != 'COMPLETED':
        errors.append(f'HARD_PROJECT_LEDGER_NOT_COMPLETED：status={ledger.get("status")}')
    target = scope.get('target_runtime_seconds')
    ledger_target = ledger.get('target_runtime_seconds')
    coverage = ledger.get('coverage') if isinstance(ledger.get('coverage'), dict) else {}
    covered = coverage.get('covered_seconds')
    if not isinstance(target, (int, float)) or not isinstance(ledger_target, (int, float)) or not isinstance(covered, (int, float)):
        errors.append('HARD_PROJECT_RUNTIME_INCOMPLETE：target/covered runtime must be numeric')
    elif abs(float(target) - float(ledger_target)) > 0.01 or abs(float(target) - float(covered)) > 0.01:
        errors.append(f'HARD_PROJECT_RUNTIME_INCOMPLETE：target={target}s ledger_target={ledger_target}s covered={covered}s')
    gaps = coverage.get('gaps')
    if not isinstance(gaps, list) or gaps:
        errors.append(f'HARD_PROJECT_RUNTIME_GAPS：gaps={gaps}')

    actual_scenes: set[str] = set()
    actual_atoms: set[str] = set()
    for uid in planned:
        unit_errors = validate_project_consistency(root, uid)
        if unit_errors:
            errors.append(f'HARD_PROJECT_UNIT_INVALID：{uid}: ' + '; '.join(unit_errors))
        data = _load(root / 'storyboard' / f'{uid}_STORYBOARD.json')
        shots = data.get('edit_shots') if isinstance(data.get('edit_shots'), list) else []
        for shot in shots:
            if not isinstance(shot, dict):
                continue
            sid = str(shot.get('scene_id') or '').strip()
            if sid:
                actual_scenes.add(sid)
            coverage_row = shot.get('coverage') if isinstance(shot.get('coverage'), dict) else {}
            for atom in coverage_row.get('story_atom_ids', []) if isinstance(coverage_row.get('story_atom_ids'), list) else []:
                if isinstance(atom, str) and atom.strip():
                    actual_atoms.add(atom.strip())
    if actual_scenes != expected_scenes:
        errors.append(f'HARD_PROJECT_SCENE_COVERAGE_INCOMPLETE：missing={sorted(expected_scenes-actual_scenes)} extra={sorted(actual_scenes-expected_scenes)}')

    authority = _load(root / 'state' / 'story_authority.json')
    atoms = authority.get('atoms') if isinstance(authority.get('atoms'), list) else []
    expected_atoms = {
        str(atom.get('atom_id')).strip() for atom in atoms
        if isinstance(atom, dict) and str(atom.get('scene_id') or '').strip() in expected_scenes and str(atom.get('atom_id') or '').strip()
    }
    if actual_atoms != expected_atoms:
        errors.append(f'HARD_PROJECT_STORY_ATOM_COVERAGE_INCOMPLETE：missing={sorted(expected_atoms-actual_atoms)} extra={sorted(actual_atoms-expected_atoms)}')


def validate_hard_delivery(project_root: str | Path, *, scope: str = 'legacy', unit_id: str | None = None) -> list[str]:
    root = Path(project_root).resolve()
    if not root.is_dir():
        return [f'HARD_PROJECT_MISSING：项目目录不存在 {root}']
    brief = _load(root / 'state' / 'project_brief.json')
    ledger = _load(root / 'PRODUCTION_LEDGER.json')
    errors: list[str] = []
    if scope not in {'legacy', 'unit', 'project'}:
        return [f'HARD_SCOPE_INVALID：{scope}']

    if scope == 'project':
        if not brief:
            return ['HARD_PROJECT_BRIEF_MISSING：state/project_brief.json required']
        if not ledger:
            return ['HARD_PROJECT_LEDGER_MISSING：PRODUCTION_LEDGER.json required']
        _project_scope_qc(root, brief, ledger, errors)
        baseline_errors = validate_asset_baseline_lock(root)
        errors.extend(f'HARD_PROJECT_ASSET_BASELINE_INVALID：{item}' for item in baseline_errors)
        _validate_required_asset_status(root, brief, errors)
        _validate_sh_gu_prompt(root, ledger, errors)
        _validate_clear_axis_breaks(root, ledger, errors)
        return errors

    if scope == 'unit':
        if not unit_id:
            return ['HARD_UNIT_ID_REQUIRED：--scope unit requires --unit-id']
        errors.extend(validate_project_consistency(root, unit_id))
        if ledger:
            subset = dict(ledger)
            if ledger.get('scope_type') == 'episodes':
                subset['completed_episodes'] = [unit_id]
            else:
                subset['completed_units'] = [unit_id]
            _validate_sh_gu_prompt(root, subset, errors)
            _validate_clear_axis_breaks(root, subset, errors)
        return errors

    # Legacy behavior remains unchanged for non-Project-Scope projects.
    if not brief or not ledger:
        return errors
    _validate_runtime_bounds(brief, ledger, errors)
    _validate_sh_gu_prompt(root, ledger, errors)
    _validate_required_asset_status(root, brief, errors)
    _validate_clear_axis_breaks(root, ledger, errors)
    _validate_repeated_template(root, brief, ledger, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description='Final Hard QC for only delivery-blocking production errors')
    parser.add_argument('--project-root', required=True)
    parser.add_argument('--scope', choices=['legacy','unit','project'], default='legacy')
    parser.add_argument('--unit-id')
    args = parser.parse_args()
    errors = validate_hard_delivery(args.project_root, scope=args.scope, unit_id=args.unit_id)
    if errors:
        print('FAIL')
        for item in errors:
            print('-', item)
        return 1
    print('PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
