#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

NEUTRAL = {'', '无', 'none', 'n/a', 'na', '不适用', 'false', 'no'}


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in NEUTRAL
    if isinstance(value, dict):
        return bool(value) and any(_has_content(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return bool(value) and any(_has_content(v) for v in value)
    return True


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, dict):
        return ' '.join([str(k).lower() for k in value] + [_text(v) for v in value.values()])
    if isinstance(value, (list, tuple, set)):
        return ' '.join(_text(v) for v in value)
    return str(value).lower() if value is not None else ''


def _locked(handoff: dict, aliases: tuple[str, ...]) -> bool:
    haystack = _text(handoff.get('do_not_reset'))
    return any(alias.lower() in haystack for alias in aliases)


def _strict_value(value: Any) -> bool:
    # Hard continuity must use explicit structured facts; do not semantically police free prose.
    return isinstance(value, (dict, list, tuple, int, float, bool)) and not isinstance(value, str)


def _same_explicit(left: Any, right: Any) -> bool | None:
    if not (_strict_value(left) and _strict_value(right)):
        return None
    return left == right


def _completed_units(ledger: dict) -> list[str]:
    if ledger.get('scope_type') == 'film_timeline':
        units = [str(x) for x in ledger.get('completed_units', []) if str(x).strip()]
        if units:
            return units
        rows = [x for x in ledger.get('film_units', []) if isinstance(x, dict) and x.get('status') == 'COMPLETE']
        rows.sort(key=lambda x: float(x.get('start_seconds') or 0.0))
        return [str(x.get('unit_id')) for x in rows if x.get('unit_id')]
    units = [str(x) for x in ledger.get('completed_episodes', []) if str(x).strip()]
    if units:
        return units
    return [str(x.get('episode_id')) for x in ledger.get('episodes', []) if isinstance(x, dict) and x.get('status') == 'COMPLETE' and x.get('episode_id')]


def _ordered_shots(root: Path, ledger: dict) -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    for unit_id in _completed_units(ledger):
        data = _load(root / 'storyboard' / f'{unit_id}_STORYBOARD.json')
        for shot in data.get('edit_shots', []) if isinstance(data.get('edit_shots'), list) else []:
            if isinstance(shot, dict):
                out.append((unit_id, shot))
    return out


def _is_scene_transition(previous: dict, current: dict) -> bool:
    if str(previous.get('scene_id') or '') != str(current.get('scene_id') or ''):
        return True
    handoff = previous.get('next_shot_handoff') if isinstance(previous.get('next_shot_handoff'), dict) else {}
    kind = str(handoff.get('type') or '').strip().lower()
    return kind == 'st' or '场景转换' in kind or 'scene transition' in kind


def _axis_errors(previous: dict, current: dict, prefix: str, errors: list[str]) -> None:
    p = previous.get('axis_and_gaze') if isinstance(previous.get('axis_and_gaze'), dict) else {}
    c = current.get('axis_and_gaze') if isinstance(current.get('axis_and_gaze'), dict) else {}
    p_axis = p.get('axis_line') if _has_content(p.get('axis_line')) else p.get('axis')
    c_axis = c.get('axis_line') if _has_content(c.get('axis_line')) else c.get('axis')
    if not (_has_content(p_axis) and _has_content(c_axis)):
        return
    if str(p_axis) != str(c_axis):
        return  # new axis logic is allowed; do not force old geography onto a new axis.
    if not (_has_content(p.get('camera_side')) and _has_content(c.get('camera_side'))):
        return
    if str(p.get('camera_side')) == str(c.get('camera_side')):
        return
    allowed = p.get('cross_axis_allowed') is True or c.get('cross_axis_allowed') is True
    transition = p.get('cross_axis_transition') if _has_content(p.get('cross_axis_transition')) else c.get('cross_axis_transition')
    if not allowed:
        errors.append(f'CONTINUITY_AXIS_BREAK：{prefix} 同一轴线camera_side跳边且未明确允许越轴')
    elif not _has_content(transition):
        errors.append(f'CONTINUITY_AXIS_TRANSITION_MISSING：{prefix} 已允许越轴，但缺少真实越轴过渡/新空间逻辑')


def _explicit_field(source: Any, key: str) -> Any:
    return source.get(key) if isinstance(source, dict) else None


def _compare_locked_field(previous: dict, current: dict, prefix: str, key: str, aliases: tuple[str, ...], label: str, errors: list[str]) -> None:
    handoff = previous.get('next_shot_handoff') if isinstance(previous.get('next_shot_handoff'), dict) else {}
    if not _locked(handoff, aliases):
        return
    panchors = previous.get('first_last_frame_anchors') if isinstance(previous.get('first_last_frame_anchors'), dict) else {}
    canchors = current.get('first_last_frame_anchors') if isinstance(current.get('first_last_frame_anchors'), dict) else {}
    tail = panchors.get('last_frame')
    start = canchors.get('first_frame')
    pvalue = _explicit_field(tail, key)
    cvalue = _explicit_field(start, key)
    if pvalue is None or cvalue is None:
        # Position may already be structured in the dedicated spatial fields.
        if key == 'character_positions':
            pspace = previous.get('spatial_blocking') if isinstance(previous.get('spatial_blocking'), dict) else {}
            cspace = current.get('spatial_blocking') if isinstance(current.get('spatial_blocking'), dict) else {}
            pvalue = pspace.get('end_positions')
            cvalue = cspace.get('start_positions')
        elif key == 'gaze':
            paxis = previous.get('axis_and_gaze') if isinstance(previous.get('axis_and_gaze'), dict) else {}
            caxis = current.get('axis_and_gaze') if isinstance(current.get('axis_and_gaze'), dict) else {}
            pvalue = paxis.get('gaze')
            cvalue = caxis.get('gaze')
    same = _same_explicit(pvalue, cvalue)
    if same is False:
        errors.append(f'CONTINUITY_{key.upper()}_MISMATCH：{prefix} 锁定{label}发生明确冲突：上一镜={pvalue} 下一镜={cvalue}')


def _state_conflicts(root: Path, ordered: list[tuple[str, dict]], errors: list[str]) -> None:
    data = _load(root / 'assets' / 'ASSET_LIBRARY.json')
    lib = data.get('ASSET_LIBRARY') if isinstance(data.get('ASSET_LIBRARY'), dict) else {}
    conflicts: dict[str, set[str]] = {}
    for record in lib.get('persistent_states', []) if isinstance(lib.get('persistent_states'), list) else []:
        if not isinstance(record, dict):
            continue
        sid = str(record.get('state_id') or '').strip()
        if not sid:
            continue
        conflicts[sid] = {str(x) for x in record.get('conflicts_with', []) if isinstance(x, str) and x.strip()}
    if not conflicts:
        return
    seen: set[tuple[str, str, str]] = set()
    for unit_id, shot in ordered:
        active = [
            str(call.get('asset_id'))
            for call in shot.get('visual_asset_calls', []) if isinstance(shot.get('visual_asset_calls'), list)
            if isinstance(call, dict) and '-ST' in str(call.get('asset_id') or '')
        ]
        active_set = set(active)
        for left in active:
            for right in conflicts.get(left, set()):
                if right not in active_set:
                    continue
                pair = tuple(sorted((left, right)))
                key = (unit_id, str(shot.get('edit_shot_id') or 'UNKNOWN'), '|'.join(pair))
                if key in seen:
                    continue
                seen.add(key)
                errors.append(f'CONTINUITY_STATE_CONFLICT：{unit_id}/{shot.get("edit_shot_id","UNKNOWN")} 同时激活互斥持续状态 {pair[0]} / {pair[1]}')




def _character_asset_ids(root: Path) -> set[str]:
    data = _load(root / 'assets' / 'ASSET_LIBRARY.json')
    lib = data.get('ASSET_LIBRARY') if isinstance(data.get('ASSET_LIBRARY'), dict) else {}
    return {
        str(row.get('asset_id'))
        for row in lib.get('character_assets', []) if isinstance(lib.get('character_assets'), list)
        if isinstance(row, dict) and str(row.get('asset_id') or '').strip()
    }


def _visible_asset_ids(shot: dict) -> set[str]:
    ids = {
        str(row.get('asset_id'))
        for row in shot.get('visual_asset_calls', []) if isinstance(shot.get('visual_asset_calls'), list)
        if isinstance(row, dict) and str(row.get('asset_id') or '').strip()
    }
    spatial = shot.get('spatial_blocking') if isinstance(shot.get('spatial_blocking'), dict) else {}
    for key in ('start_positions', 'frame_positions', 'end_positions'):
        value = spatial.get(key)
        if isinstance(value, dict):
            ids.update(str(k) for k in value if str(k).strip())
    return ids


def _offscreen_carry_errors(root: Path, ordered: list[tuple[str, dict]], errors: list[str]) -> None:
    characters = _character_asset_ids(root)
    allowed = {'asset_id', 'exit_side', 'last_visible_state'}
    for index, (_, previous) in enumerate(ordered):
        handoff = previous.get('next_shot_handoff') if isinstance(previous.get('next_shot_handoff'), dict) else {}
        if 'offscreen_carry' not in handoff:
            continue
        carry = handoff.get('offscreen_carry')
        prefix = str(previous.get('edit_shot_id') or 'UNKNOWN')
        if not isinstance(carry, list):
            errors.append(f'OFFSCREEN_CARRY_STRUCTURE：{prefix} offscreen_carry must be a list')
            continue
        seen: set[str] = set()
        next_shot = ordered[index + 1][1] if index + 1 < len(ordered) else None
        for item in carry:
            if not isinstance(item, dict):
                errors.append(f'OFFSCREEN_CARRY_STRUCTURE：{prefix} entry must be an object')
                continue
            unknown = sorted(set(item) - allowed)
            if unknown:
                errors.append(f'OFFSCREEN_CARRY_STRUCTURE：{prefix} unknown fields {", ".join(unknown)}')
            aid = str(item.get('asset_id') or '').strip()
            if not aid or not str(item.get('exit_side') or '').strip() or not _has_content(item.get('last_visible_state')):
                errors.append(f'OFFSCREEN_CARRY_STRUCTURE：{prefix} each entry requires asset_id, exit_side, last_visible_state')
                continue
            if aid in seen:
                errors.append(f'OFFSCREEN_CARRY_DUPLICATE：{prefix} duplicate {aid}')
            seen.add(aid)
            if characters and aid not in characters:
                errors.append(f'OFFSCREEN_CARRY_ASSET：{prefix} {aid} is not a character asset')
            if next_shot is not None and str(previous.get('scene_id') or '') == str(next_shot.get('scene_id') or ''):
                if aid in _visible_asset_ids(next_shot):
                    errors.append(f'OFFSCREEN_CARRY_VISIBLE_CONFLICT：{prefix}→{next_shot.get("edit_shot_id","UNKNOWN")} {aid} is declared off-screen but visible')

def validate_continuity(project_root: str | Path) -> list[str]:
    root = Path(project_root).resolve()
    ledger = _load(root / 'PRODUCTION_LEDGER.json')
    if not ledger:
        return []  # base delivery gate owns missing-ledger errors.
    ordered = _ordered_shots(root, ledger)
    errors: list[str] = []
    _state_conflicts(root, ordered, errors)
    _offscreen_carry_errors(root, ordered, errors)
    for (_, previous), (_, current) in zip(ordered, ordered[1:]):
        if _is_scene_transition(previous, current):
            continue
        prefix = f'{previous.get("edit_shot_id","UNKNOWN")}→{current.get("edit_shot_id","UNKNOWN")}'
        _axis_errors(previous, current, prefix, errors)
        _compare_locked_field(previous, current, prefix, 'gaze', ('gaze', '视线', '目光'), '视线', errors)
        _compare_locked_field(previous, current, prefix, 'character_positions', ('character_positions', '人物位置', '物理位置', '站位'), '人物位置', errors)
        _compare_locked_field(previous, current, prefix, 'hand_props', ('hand_props', '手持道具', '左右手', '道具'), '手持道具', errors)
        _compare_locked_field(previous, current, prefix, 'persistent_states', ('persistent_states', '持续状态', '状态'), '持续状态', errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate only explicit hard continuity contradictions')
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()
    errors = validate_continuity(args.project_root)
    if errors:
        print('FAIL')
        for error in errors:
            print('-', error)
        return 1
    print('PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
