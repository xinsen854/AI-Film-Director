#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        text = value.strip()
        if text:
            yield text
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)


def _normalize(text: str) -> str:
    return re.sub(r'[\s\u3000，。！？；：、“”‘’（）()【】\[\]—…·,.!?;:\-]+', '', str(text)).lower()


def _contains_literal(corpus: str, literal: str, *, min_chars: int) -> bool:
    needle = _normalize(literal)
    return len(needle) >= min_chars and needle in corpus


def _dialogue_texts(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, str):
        if value.strip():
            out.append(value.strip())
    elif isinstance(value, dict):
        preferred = False
        for key in ('verbatim', 'text', 'dialogue', 'line'):
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
                preferred = True
        if not preferred:
            for item in value.values():
                out.extend(_dialogue_texts(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            out.extend(_dialogue_texts(item))
    return list(dict.fromkeys(out))


def _sound_texts(shot: dict) -> list[str]:
    values = list(_walk_strings(shot.get('sound')))
    return list(dict.fromkeys(values))


def _state_assets(shot: dict) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    calls = shot.get('visual_asset_calls') if isinstance(shot.get('visual_asset_calls'), list) else []
    for call in calls:
        if not isinstance(call, dict):
            continue
        asset_id = str(call.get('asset_id') or '').strip()
        if '-ST' not in asset_id.upper():
            continue
        literals = {asset_id}
        name = str(call.get('name') or '').strip()
        if name:
            literals.add(name)
        result[asset_id] = literals
    return result


def _member_shots(payload: dict, gu: dict) -> tuple[list[dict], list[dict]]:
    shots = [shot for shot in payload.get('edit_shots', []) if isinstance(shot, dict)]
    members = {str(x) for x in gu.get('member_edit_shots', []) if str(x)}
    member_indices = [i for i, shot in enumerate(shots) if str(shot.get('edit_shot_id') or '') in members]
    current = [shots[i] for i in member_indices]
    if not member_indices:
        return current, []
    last = max(member_indices)
    return current, shots[last + 1:]


def _gu_corpus(gu: dict) -> str:
    # Only data that the fixed Renderer can place into the current GU prompt.
    prompt_data = {
        'active_media_references': gu.get('active_media_references'),
        'voice_text_assets': gu.get('voice_text_assets'),
        'phases': gu.get('phases'),
        'prompt_sections': gu.get('prompt_sections'),
        'critical_time_anchors': gu.get('critical_time_anchors'),
    }
    return _normalize(' '.join(_walk_strings(prompt_data)))


def _current_revealed_info_ids(shots: list[dict]) -> set[str]:
    out: set[str] = set()
    for shot in shots:
        coverage = shot.get('coverage') if isinstance(shot.get('coverage'), dict) else {}
        for info_id in coverage.get('revealed_info_ids', []) if isinstance(coverage.get('revealed_info_ids'), list) else []:
            if str(info_id).strip():
                out.add(str(info_id).strip())
    return out


def _unit_number(value: str) -> tuple[str, int] | None:
    match = re.search(r'\b(EP|PU)(\d+)\b', str(value), flags=re.I)
    return (match.group(1).upper(), int(match.group(2))) if match else None


def _shot_number(value: str) -> int | None:
    match = re.search(r'\bSH(\d+)\b', str(value), flags=re.I)
    return int(match.group(1)) if match else None


def _marker_is_future(marker: Any, unit_id: str, member_shot_ids: list[str]) -> bool | None:
    if not isinstance(marker, str) or not marker.strip():
        return None
    current_unit = _unit_number(unit_id)
    marker_unit = _unit_number(marker)
    if current_unit and marker_unit and current_unit[0] == marker_unit[0]:
        if marker_unit[1] != current_unit[1]:
            return marker_unit[1] > current_unit[1]
    marker_shot = _shot_number(marker)
    current_numbers = [n for n in (_shot_number(x) for x in member_shot_ids) if n is not None]
    if marker_shot is not None and current_numbers:
        return marker_shot > max(current_numbers)
    return None


def _scene_number(value: str) -> int | None:
    match = re.search(r'\bSC(\d+)\b', str(value), flags=re.I)
    return int(match.group(1)) if match else None


def _marker_is_future_for_shots(marker: Any, unit_id: str, shots: list[dict]) -> bool | None:
    members = [str(shot.get('edit_shot_id') or '') for shot in shots]
    direct = _marker_is_future(marker, unit_id, members)
    if direct is not None:
        return direct
    marker_scene = _scene_number(str(marker or ''))
    current_scenes = [n for n in (_scene_number(str(shot.get('scene_id') or '')) for shot in shots) if n is not None]
    if marker_scene is not None and current_scenes:
        return marker_scene > max(current_scenes)
    return None


def _asset_library_records(root: Path) -> tuple[dict[str, dict], list[dict]]:
    payload = _load_json(root / 'assets' / 'ASSET_LIBRARY.json')
    lib = payload.get('ASSET_LIBRARY') if isinstance(payload.get('ASSET_LIBRARY'), dict) else {}
    records: dict[str, dict] = {}
    for group in ('character_assets', 'location_assets', 'prop_assets', 'g_assets'):
        items = lib.get(group) if isinstance(lib.get(group), list) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            asset_id = str(item.get('asset_id') or '').strip()
            if asset_id:
                records[asset_id] = item
    states = [item for item in (lib.get('persistent_states') if isinstance(lib.get('persistent_states'), list) else []) if isinstance(item, dict)]
    for state in states:
        state_id = str(state.get('state_id') or '').strip()
        if state_id:
            records[state_id] = state
    return records, states


def _called_asset_ids(shots: list[dict]) -> list[str]:
    out: list[str] = []
    for shot in shots:
        calls = shot.get('visual_asset_calls') if isinstance(shot.get('visual_asset_calls'), list) else []
        for call in calls:
            if not isinstance(call, dict):
                continue
            asset_id = str(call.get('asset_id') or '').strip()
            if asset_id and asset_id not in out:
                out.append(asset_id)
    return out


def _asset_reference_prompt(record: dict) -> str:
    return str(record.get('image_prompt') or '').strip()


def _asset_reference_isolation_errors(root: Path, unit_id: str, gu: dict, current_shots: list[dict]) -> list[str]:
    records, states = _asset_library_records(root)
    if not records:
        return []
    called_ids = _called_asset_ids(current_shots)
    if not called_ids:
        return []

    errors: list[str] = []
    ledger = _load_json(root / 'state' / 'information_ledger.json')
    items = ledger.get('items') if isinstance(ledger.get('items'), list) else []
    current_revealed = _current_revealed_info_ids(current_shots)

    for asset_id in called_ids:
        record = records.get(asset_id)
        if not isinstance(record, dict):
            continue
        prompt = _asset_reference_prompt(record)
        prompt_corpus = _normalize(prompt)
        if prompt_corpus:
            for item in items:
                if not isinstance(item, dict):
                    continue
                info_id = str(item.get('info_id') or '').strip()
                if info_id and info_id in current_revealed:
                    continue
                status = str(item.get('status') or '').upper()
                marker_future = _marker_is_future_for_shots(
                    item.get('actual_reveal') or item.get('planned_reveal') or item.get('earliest_fair_reveal'),
                    unit_id, current_shots,
                )
                protected_now = status in {'HIDDEN', 'PARTIAL'} or marker_future is True
                if not protected_now:
                    continue
                literals = item.get('protected_literals') if isinstance(item.get('protected_literals'), list) else []
                for literal in literals:
                    if isinstance(literal, str) and _contains_literal(prompt_corpus, literal, min_chars=4):
                        errors.append(
                            f'CURRENT_GU_ONLY_ASSET_REVEAL：{unit_id}/{gu.get("generation_unit_id")} '
                            f'当前资产 {asset_id} 的参考图Prompt提前包含未揭露信息 {info_id or "UNKNOWN"}：{literal}'
                        )
                        break

        if '-ST' in asset_id.upper():
            parent_id = str(record.get('inherits_from') or '').strip()
            if _marker_is_future_for_shots(record.get('state_start'), unit_id, current_shots) is True:
                errors.append(
                    f'CURRENT_GU_ONLY_ASSET_STATE_TOO_EARLY：{unit_id}/{gu.get("generation_unit_id")} '
                    f'当前调用状态 {asset_id} 尚未到 state_start={record.get("state_start")}'
                )
        else:
            parent_id = asset_id

        if not parent_id or not prompt_corpus:
            continue
        for future_state in states:
            future_id = str(future_state.get('state_id') or '').strip()
            if not future_id or future_id == asset_id:
                continue
            if str(future_state.get('inherits_from') or '').strip() != parent_id:
                continue
            if _marker_is_future_for_shots(future_state.get('state_start'), unit_id, current_shots) is not True:
                continue
            visible_change = str(future_state.get('visible_change') or '').strip()
            if _contains_literal(prompt_corpus, visible_change, min_chars=4):
                errors.append(
                    f'CURRENT_GU_ONLY_ASSET_FUTURE_STATE_CONTENT：{unit_id}/{gu.get("generation_unit_id")} '
                    f'当前资产 {asset_id} 的参考图Prompt提前混入未来状态 {future_id}：{visible_change}'
                )
                break

    return errors


def _protected_reveal_errors(root: Path, unit_id: str, gu: dict, current_shots: list[dict], corpus: str) -> list[str]:
    ledger = _load_json(root / 'state' / 'information_ledger.json')
    items = ledger.get('items') if isinstance(ledger.get('items'), list) else []
    if not items:
        return []
    current_revealed = _current_revealed_info_ids(current_shots)
    members = [str(x) for x in gu.get('member_edit_shots', []) if str(x)]
    errors: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        info_id = str(item.get('info_id') or '').strip()
        if info_id and info_id in current_revealed:
            continue
        status = str(item.get('status') or '').upper()
        marker_future = _marker_is_future(item.get('actual_reveal') or item.get('planned_reveal') or item.get('earliest_fair_reveal'), unit_id, members)
        protected_now = status in {'HIDDEN', 'PARTIAL'} or marker_future is True
        if not protected_now:
            continue
        literals = item.get('protected_literals') if isinstance(item.get('protected_literals'), list) else []
        for literal in literals:
            if isinstance(literal, str) and _contains_literal(corpus, literal, min_chars=4):
                errors.append(f'CURRENT_GU_ONLY_REVEAL：{unit_id}/{gu.get("generation_unit_id")} 提前包含未揭露信息 {info_id or "UNKNOWN"}：{literal}')
                break
    return errors


def validate_current_gu_only(project_root: str | Path) -> list[str]:
    root = Path(project_root).resolve()
    errors: list[str] = []
    storyboard_dir = root / 'storyboard'
    if not storyboard_dir.is_dir():
        return errors

    for path in sorted(storyboard_dir.glob('*_STORYBOARD.json')):
        payload = _load_json(path)
        if not payload:
            continue
        unit_id = path.name[:-len('_STORYBOARD.json')]
        units = payload.get('generation_units') if isinstance(payload.get('generation_units'), list) else []
        for gu in units:
            if not isinstance(gu, dict):
                continue
            gid = str(gu.get('generation_unit_id') or 'UNKNOWN')
            current_shots, future_shots = _member_shots(payload, gu)
            corpus = _gu_corpus(gu)
            if not current_shots:
                continue

            current_story = {_normalize(str(shot.get('source', {}).get('story_range') or '')) for shot in current_shots if isinstance(shot.get('source'), dict)}
            for shot in future_shots:
                source = shot.get('source') if isinstance(shot.get('source'), dict) else {}
                story = str(source.get('story_range') or '').strip()
                if _normalize(story) not in current_story and _contains_literal(corpus, story, min_chars=6):
                    errors.append(f'CURRENT_GU_ONLY_STORY：{unit_id}/{gid} 提前包含未来剧情：{story}')
                    break

            current_dialogue = {_normalize(x) for shot in current_shots for x in _dialogue_texts(shot.get('dialogue_execution'))}
            future_dialogue = [x for shot in future_shots for x in _dialogue_texts(shot.get('dialogue_execution'))]
            for text in future_dialogue:
                if _normalize(text) not in current_dialogue and _contains_literal(corpus, text, min_chars=2):
                    errors.append(f'CURRENT_GU_ONLY_DIALOGUE：{unit_id}/{gid} 提前包含未来对白：{text}')
                    break

            current_sounds = {_normalize(x) for shot in current_shots for x in _sound_texts(shot)}
            future_sounds = [x for shot in future_shots for x in _sound_texts(shot)]
            for text in future_sounds:
                if _normalize(text) not in current_sounds and _contains_literal(corpus, text, min_chars=4):
                    errors.append(f'CURRENT_GU_ONLY_SOUND：{unit_id}/{gid} 提前包含未来声音：{text}')
                    break

            current_states: set[str] = set()
            for shot in current_shots:
                current_states.update(_state_assets(shot))
            future_states: dict[str, set[str]] = {}
            for shot in future_shots:
                future_states.update(_state_assets(shot))
            for state_id, literals in future_states.items():
                if state_id in current_states:
                    continue
                if any(_contains_literal(corpus, literal, min_chars=4) for literal in literals):
                    errors.append(f'CURRENT_GU_ONLY_STATE：{unit_id}/{gid} 提前激活未来资产状态：{state_id}')
                    break

            errors.extend(_protected_reveal_errors(root, unit_id, gu, current_shots, corpus))
            errors.extend(_asset_reference_isolation_errors(root, unit_id, gu, current_shots))

    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate CURRENT_GU_ONLY isolation for structured CineWeaver GU prompts')
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()
    errors = validate_current_gu_only(args.project_root)
    if errors:
        print('FAIL')
        for error in errors:
            print('-', error)
        return 1
    print('PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
