#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from render_storyboard import render_storyboard, validate_storyboard_payload
from story_coverage import story_coverage_enabled, validate_story_coverage, write_story_coverage
from runtime_state import require_current_runtime_state
from validate_unit_consistency import validate_project_consistency

LEDGER_NAME = 'PRODUCTION_LEDGER.json'
FILM_FORMATS = {'film', 'short_film'}
SERIES_FORMATS = {'series', 'short_series'}
EPSILON = 0.01


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'expected object: {path}')
    return data


def _brief(root: Path) -> dict:
    path = root / 'state' / 'project_brief.json'
    if not path.is_file():
        raise FileNotFoundError(path)
    return _read_json(path)


def _write(root: Path, ledger: dict) -> dict:
    (root / LEDGER_NAME).write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return ledger


def _sync_pipeline_state(root: Path, ledger: dict) -> None:
    """Keep resumable runtime state aligned with the authoritative production ledger."""
    path = root / 'state' / 'pipeline_state.json'
    if not path.is_file():
        return
    try:
        state = _read_json(path)
    except Exception:
        return

    if ledger.get('scope_type') == 'episodes':
        completed = [str(x) for x in ledger.get('completed_episodes', []) if isinstance(x, str)]
        next_unit = ledger.get('next_resume', {}).get('episode_id')
    else:
        completed = [str(x) for x in ledger.get('completed_units', []) if isinstance(x, str)]
        next_unit = None

    state['completed_units'] = list(dict.fromkeys(completed))
    if ledger.get('status') == 'COMPLETED':
        state['status'] = 'PROJECT_COMPLETED'
        state['current_phase'] = 'quality-delivery'
        state['current_unit'] = None
    else:
        if state.get('status') == 'PROJECT_COMPLETED':
            state['status'] = 'PRODUCTION_IN_PROGRESS'
        if ledger.get('scope_type') == 'episodes':
            state['current_unit'] = next_unit
        elif state.get('current_unit') in set(completed):
            state['current_unit'] = None
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')



def _require_upstream_pipeline(project_root: Path, unit_id: str) -> None:
    errors = validate_project_consistency(project_root, unit_id)
    if errors:
        raise ValueError('PIPELINE_DEPENDENCY：当前单元上游生产链未完成：' + '; '.join(errors))

def _storyboard_json_path(project_root: Path, unit_id: str) -> Path:
    return project_root / 'storyboard' / f'{unit_id}_STORYBOARD.json'


def _storyboard_md_path(project_root: Path, unit_id: str) -> Path:
    return project_root / 'storyboard' / f'{unit_id}_STORYBOARD.md'


def _require_structured_storyboard(project_root: Path, unit_id: str) -> dict:
    json_path = _storyboard_json_path(project_root, unit_id)
    md_path = _storyboard_md_path(project_root, unit_id)
    if not json_path.is_file():
        raise ValueError(f'cannot checkpoint unit without structured SH/GU/PH storyboard: {unit_id}')
    try:
        payload = _read_json(json_path)
    except Exception as exc:
        raise ValueError(f'cannot checkpoint unit with unreadable storyboard JSON: {json_path.name}') from exc
    errors = validate_storyboard_payload(payload)
    if errors:
        raise ValueError(f'cannot checkpoint invalid storyboard {unit_id}: ' + '; '.join(errors))
    if not md_path.is_file():
        raise ValueError(f'cannot checkpoint unit without rendered storyboard Markdown: {unit_id}')
    expected = render_storyboard(payload)
    actual = md_path.read_text(encoding='utf-8')
    if actual != expected:
        raise ValueError(f'cannot checkpoint unit whose storyboard Markdown is not renderer output: {unit_id}')
    return payload


def _shot_runtime(project_root: Path, unit_id: str) -> float | None:
    try:
        payload = _require_structured_storyboard(project_root, unit_id)
    except ValueError:
        return None
    shots = payload.get('edit_shots', [])
    if not isinstance(shots, list) or not shots:
        return None
    durations: list[float] = []
    for shot in shots:
        if not isinstance(shot, dict):
            return None
        duration = shot.get('edit_shot_duration')
        if not isinstance(duration, (int, float)) or duration <= 0:
            return None
        durations.append(float(duration))
    return sum(durations)


def _episode_number(episode_id: str) -> int:
    match = re.fullmatch(r'EP(\d+)', episode_id.strip(), re.I)
    if not match:
        raise ValueError(f'episode_id must look like EP01: {episode_id}')
    return int(match.group(1))


def initialize_ledger(project_root: str | Path) -> dict:
    root = Path(project_root).resolve()
    brief = _brief(root)
    existing_path = root / LEDGER_NAME
    if existing_path.is_file():
        existing = _read_json(existing_path)
        work_format = brief.get('work_format')
        if work_format in FILM_FORMATS:
            target = brief.get('target_total_runtime_seconds')
            if existing.get('scope_type') != 'film_timeline' or not isinstance(target, (int, float)) or abs(float(existing.get('target_runtime_seconds', -1)) - float(target)) > EPSILON:
                raise ValueError('existing production ledger conflicts with confirmed film target; do not overwrite completed work automatically')
        elif work_format in SERIES_FORMATS:
            target_count = brief.get('episode_count')
            if existing.get('scope_type') != 'episodes' or existing.get('target_episode_count') != target_count:
                raise ValueError('existing production ledger conflicts with confirmed episode target; do not overwrite completed work automatically')
        return existing

    work_format = brief.get('work_format')
    project_id = str(brief.get('project_id', root.name))
    if work_format in FILM_FORMATS:
        target = brief.get('target_total_runtime_seconds')
        if not isinstance(target, (int, float)) or target <= 0:
            raise ValueError('film/short_film requires target_total_runtime_seconds > 0')
        ledger = {
            'schema_version': '1.0', 'project_id': project_id, 'scope_type': 'film_timeline',
            'status': 'IN_PROGRESS', 'target_runtime_seconds': float(target),
            'film_units': [], 'completed_units': [],
            'coverage': {'covered_seconds': 0.0, 'percentage': 0.0, 'gaps': []},
            'next_resume': {'start_seconds': 0.0},
        }
    elif work_format in SERIES_FORMATS:
        target_count = brief.get('episode_count')
        if not isinstance(target_count, int) or target_count <= 0:
            raise ValueError('series/short_series requires episode_count > 0')
        ledger = {
            'schema_version': '1.0', 'project_id': project_id, 'scope_type': 'episodes',
            'status': 'IN_PROGRESS', 'target_episode_count': target_count,
            'target_episode_runtime_seconds': brief.get('target_episode_runtime_seconds'),
            'episodes': [], 'completed_episodes': [],
            'coverage': {'completed_count': 0, 'percentage': 0.0},
            'next_resume': {'episode_id': 'EP01'},
        }
    else:
        raise ValueError(f'unsupported work_format for production ledger: {work_format}')
    return _write(root, ledger)


def load_or_initialize(project_root: str | Path) -> dict:
    root = Path(project_root).resolve()
    require_current_runtime_state(root)
    path = root / LEDGER_NAME
    return _read_json(path) if path.is_file() else initialize_ledger(root)


def checkpoint_film_unit(project_root: str | Path, unit_id: str, start_seconds: float, end_seconds: float) -> dict:
    root = Path(project_root).resolve()
    ledger = load_or_initialize(root)
    _require_upstream_pipeline(root, unit_id)
    if ledger.get('scope_type') != 'film_timeline':
        raise ValueError('film checkpoint used for non-film ledger')
    start, end = float(start_seconds), float(end_seconds)
    if end <= start:
        raise ValueError('end_seconds must be greater than start_seconds')
    target = float(ledger['target_runtime_seconds'])
    if end > target + EPSILON:
        raise ValueError(f'film checkpoint exceeds confirmed target runtime: {end} > {target}')

    payload = _require_structured_storyboard(root, unit_id)
    if story_coverage_enabled(root):
        write_story_coverage(root)
        coverage_errors = validate_story_coverage(root, unit_id=unit_id)
        if coverage_errors:
            raise ValueError('cannot checkpoint unit with incomplete Story Coverage: ' + '; '.join(coverage_errors))
    actual_runtime = sum(float(shot['edit_shot_duration']) for shot in payload['edit_shots'])
    claimed_runtime = end - start
    if abs(actual_runtime - claimed_runtime) > EPSILON:
        raise ValueError(f'film unit coverage does not match actual SH runtime: claimed={claimed_runtime}s actual={actual_runtime}s')

    units = list(ledger.get('film_units', []))
    existing = next((u for u in units if u.get('unit_id') == unit_id), None)
    if existing:
        if abs(float(existing.get('start_seconds', -1)) - start) > EPSILON or abs(float(existing.get('end_seconds', -1)) - end) > EPSILON:
            raise ValueError(f'cannot rewrite completed unit with different range: {unit_id}')
        if story_coverage_enabled(root):
            write_story_coverage(root, confirm_unit=unit_id)
        _sync_pipeline_state(root, ledger)
        return ledger

    expected_start = float(ledger.get('next_resume', {}).get('start_seconds', 0.0))
    if abs(start - expected_start) > EPSILON:
        raise ValueError(f'film unit must continue from next uncovered second {expected_start}, got {start}')

    units.append({'unit_id': unit_id, 'start_seconds': start, 'end_seconds': end, 'status': 'COMPLETE'})
    covered = end
    completed = [u['unit_id'] for u in units if u.get('status') == 'COMPLETE']
    ledger.update({
        'film_units': units, 'completed_units': completed,
        'coverage': {'covered_seconds': covered, 'percentage': round(min(100.0, covered / target * 100.0), 4), 'gaps': []},
        'next_resume': {'start_seconds': covered if covered < target - EPSILON else target},
        'status': 'COMPLETED' if abs(covered - target) <= EPSILON else 'IN_PROGRESS',
    })
    _write(root, ledger)
    if story_coverage_enabled(root):
        write_story_coverage(root, confirm_unit=unit_id)
    _sync_pipeline_state(root, ledger)
    return ledger


def checkpoint_episode(project_root: str | Path, episode_id: str, actual_runtime_seconds: float | None = None) -> dict:
    root = Path(project_root).resolve()
    ledger = load_or_initialize(root)
    normalized_for_gate = f'EP{_episode_number(episode_id):02d}'
    _require_upstream_pipeline(root, normalized_for_gate)
    if ledger.get('scope_type') != 'episodes':
        raise ValueError('episode checkpoint used for non-series ledger')
    number = _episode_number(episode_id)
    target_count = int(ledger['target_episode_count'])
    if number > target_count:
        raise ValueError(f'episode exceeds confirmed target count: {episode_id} > EP{target_count:02d}')

    episodes = list(ledger.get('episodes', []))
    existing = next((e for e in episodes if str(e.get('episode_id', '')).upper() == episode_id.upper()), None)

    normalized_id = f'EP{number:02d}'
    payload = _require_structured_storyboard(root, normalized_id)
    if story_coverage_enabled(root):
        write_story_coverage(root)
        coverage_errors = validate_story_coverage(root, unit_id=normalized_id)
        if coverage_errors:
            raise ValueError('cannot checkpoint unit with incomplete Story Coverage: ' + '; '.join(coverage_errors))
    shot_runtime = sum(float(shot['edit_shot_duration']) for shot in payload['edit_shots'])
    runtime = shot_runtime if actual_runtime_seconds is None else float(actual_runtime_seconds)
    if runtime <= 0:
        raise ValueError('actual_runtime_seconds must be > 0')
    if abs(runtime - shot_runtime) > EPSILON:
        raise ValueError(f'episode runtime does not match actual SH runtime: declared={runtime}s actual={shot_runtime}s')

    if existing:
        if story_coverage_enabled(root):
            write_story_coverage(root, confirm_unit=normalized_id)
        _sync_pipeline_state(root, ledger)
        return ledger

    expected = len([e for e in episodes if e.get('status') == 'COMPLETE']) + 1
    if number != expected:
        raise ValueError(f'episodes must checkpoint sequentially; expected EP{expected:02d}, got {episode_id}')

    episodes.append({'episode_id': normalized_id, 'status': 'COMPLETE', 'unit_id': normalized_id, 'actual_runtime_seconds': runtime})
    completed = [e['episode_id'] for e in episodes if e.get('status') == 'COMPLETE']
    count = len(completed)
    ledger.update({
        'episodes': episodes, 'completed_episodes': completed,
        'coverage': {'completed_count': count, 'percentage': round(min(100.0, count / target_count * 100.0), 4)},
        'next_resume': {'episode_id': None if count >= target_count else f'EP{count + 1:02d}'},
        'status': 'COMPLETED' if count == target_count else 'IN_PROGRESS',
    })
    _write(root, ledger)
    if story_coverage_enabled(root):
        write_story_coverage(root, confirm_unit=normalized_id)
    _sync_pipeline_state(root, ledger)
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser(description='Initialize or checkpoint resumable production coverage using authoritative SH/GU/PH storyboard files')
    parser.add_argument('action', choices=['init', 'checkpoint-film', 'checkpoint-episode', 'status'])
    parser.add_argument('--project-root', required=True)
    parser.add_argument('--unit-id')
    parser.add_argument('--start', type=float)
    parser.add_argument('--end', type=float)
    parser.add_argument('--episode-id')
    parser.add_argument('--actual-runtime', type=float)
    args = parser.parse_args()

    require_current_runtime_state(args.project_root)

    if args.action == 'init':
        data = initialize_ledger(args.project_root)
    elif args.action == 'checkpoint-film':
        if not args.unit_id or args.start is None or args.end is None:
            parser.error('checkpoint-film requires --unit-id --start --end')
        data = checkpoint_film_unit(args.project_root, args.unit_id, args.start, args.end)
    elif args.action == 'checkpoint-episode':
        if not args.episode_id:
            parser.error('checkpoint-episode requires --episode-id')
        data = checkpoint_episode(args.project_root, args.episode_id, args.actual_runtime)
    else:
        data = load_or_initialize(args.project_root)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
