#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REQUIRED_SHOT_FIELDS = [
    'edit_shot_id', 'scene_id', 'edit_shot_duration', 'generation_unit_id', 'source',
    'shot_function', 'shot_type', 'base_frame', 'camera_parameters', 'axis_and_gaze',
    'visual_asset_calls', 'spatial_blocking', 'continuous_visuals', 'first_last_frame_anchors',
    'key_micro_reactions', 'dialogue_execution', 'sound', 'edit_interface', 'continuity_locks',
    'next_shot_handoff',
]
REQUIRED_GU_FIELDS = [
    'generation_unit_id', 'target_video_model', 'packing_policy', 'mode', 'duration',
    'member_edit_shots', 'contains_explicit_cuts', 'active_media_references', 'voice_text_assets',
    'phases', 'prompt_sections',
]
REQUIRED_PROMPT_SECTIONS = [
    'generation_goal', 'reference_roles', 'initial_state', 'sound', 'keep_consistent', 'local_constraints'
]
BOILERPLATE_EXACT = {
    '保持克制',
    '按资产库与连续性锁执行',
    '当前动作中只锁定与功能直接相关的视线、停顿、手部状态或许可变化',
    '同上',
    '继承上一镜',
    'same as before',
    'as above',
}
MODEL_LIMITS = {'SEEDANCE_2_5': 30.0, 'SEEDANCE_2_0': 15.0}
EPSILON = 0.01


REFERENCE_ROLE_FIELDS = {
    'asset_id', 'media_ref', 'role', 'inherits', 'excludes', 'fidelity', 'fidelity_target',
}
REFERENCE_FIDELITY_VALUES = {
    'full-preserve', 'partial-preserve', 'attribute-transfer', 'loose-guide',
}
REFERENCE_MEDIA_RE = re.compile(r'^@(?:图片|图像|image|视频|video|音频|audio)\s*\d+$', re.I)


def _is_structured_reference_role(value: Any) -> bool:
    return isinstance(value, dict) and bool(set(value) & REFERENCE_ROLE_FIELDS)


def reference_role_items(value: Any) -> list[Any]:
    """Flatten legacy containers while preserving structured role objects."""
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        out: list[Any] = []
        for item in value:
            if _is_structured_reference_role(item):
                out.append(item)
            else:
                out.extend(reference_role_items(item))
        return out
    if isinstance(value, dict):
        if _is_structured_reference_role(value):
            return [value]
        out: list[Any] = []
        for item in value.values():
            out.extend(reference_role_items(item))
        return out
    return []


def render_reference_role(value: Any) -> str:
    if not isinstance(value, dict) or not _is_structured_reference_role(value):
        return str(value).strip()
    asset_id = str(value.get('asset_id') or '').strip()
    media_ref = str(value.get('media_ref') or '').strip()
    role = str(value.get('role') or '').strip()
    inherits = [str(item).strip() for item in value.get('inherits', []) if str(item).strip()] if isinstance(value.get('inherits'), list) else []
    excludes = [str(item).strip() for item in value.get('excludes', []) if str(item).strip()] if isinstance(value.get('excludes'), list) else []
    fidelity = str(value.get('fidelity') or '').strip()
    fidelity_target = str(value.get('fidelity_target') or '').strip()
    head = f'{media_ref} 对应 {asset_id}' if media_ref else asset_id
    parts = [head]
    if role:
        parts.append(f'职责：{role}')
    if inherits:
        parts.append(f'只继承：{"、".join(inherits)}')
    if excludes:
        parts.append(f'排除：{"、".join(excludes)}')
    if fidelity:
        fidelity_text = fidelity
        if fidelity_target:
            fidelity_text += f' → {fidelity_target}'
        parts.append(f'保真：{fidelity_text}')
    return '｜'.join(parts)


def _validate_reference_roles(value: Any, label: str, errors: list[str]) -> None:
    # Legacy-only payloads remain legal. Once a GU opts into structured media
    # roles, media-bearing legacy strings may not sit beside them, otherwise
    # the structured transfer/exclusion checks could be bypassed selectively.
    items = reference_role_items(value)
    has_structured = any(isinstance(item, dict) and _is_structured_reference_role(item) for item in items)
    has_legacy_media = any(
        isinstance(item, str)
        and re.search(r'@(?:图片|图像|image|视频|video|音频|audio)\s*\d+', item, re.I)
        for item in items
    )
    if has_structured and has_legacy_media:
        errors.append(
            f'{label}: REFERENCE_ROLE_MIXED_MODE structured media roles cannot be mixed with legacy @media role strings'
        )
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        item_label = f'{label}[{index}]'
        unknown = sorted(set(item) - REFERENCE_ROLE_FIELDS)
        if unknown:
            errors.append(f'{item_label}: REFERENCE_ROLE_UNKNOWN_FIELD {", ".join(unknown)}')
        for key in ('asset_id', 'role'):
            if not _has_content(item.get(key)):
                errors.append(f'{item_label}: REFERENCE_ROLE_STRUCTURE missing {key}')
        inherits = item.get('inherits')
        if not isinstance(inherits, list) or not inherits or not all(isinstance(x, str) and x.strip() for x in inherits):
            errors.append(f'{item_label}: REFERENCE_ROLE_STRUCTURE missing inherits')
        media_ref = str(item.get('media_ref') or '').strip()
        if media_ref and REFERENCE_MEDIA_RE.fullmatch(media_ref) is None:
            errors.append(f'{item_label}: REFERENCE_ROLE_MEDIA_REF invalid media_ref {media_ref!r}')
        excludes = item.get('excludes')
        if media_ref and (not isinstance(excludes, list) or not excludes or not all(isinstance(x, str) and x.strip() for x in excludes)):
            errors.append(f'{item_label}: REFERENCE_ROLE_STRUCTURE missing excludes')
        elif excludes is not None and (not isinstance(excludes, list) or not all(isinstance(x, str) and x.strip() for x in excludes)):
            errors.append(f'{item_label}: REFERENCE_ROLE_STRUCTURE excludes must be a string list')
        fidelity = str(item.get('fidelity') or '').strip()
        target = str(item.get('fidelity_target') or '').strip()
        if fidelity and fidelity not in REFERENCE_FIDELITY_VALUES:
            errors.append(f'{item_label}: REFERENCE_ROLE_FIDELITY invalid fidelity {fidelity!r}')
        if fidelity == 'attribute-transfer' and not target:
            errors.append(f'{item_label}: REFERENCE_ROLE_FIDELITY_TARGET attribute-transfer requires fidelity_target')
        if target and fidelity != 'attribute-transfer':
            errors.append(f'{item_label}: REFERENCE_ROLE_FIDELITY_TARGET fidelity_target is only legal for attribute-transfer')


DIALOGUE_REQUIRED_FIELDS = ('speaker', 'verbatim')
DIALOGUE_PERFORMANCE_FIELDS = (
    'voice_profile_id', 'performance_strategy', 'audible_emotion',
    'volume', 'distance', 'pace', 'emphasis', 'breath', 'pause',
)
DIALOGUE_PRESERVE_FIELDS = (
    'mode', 'lip_sync', 'performance_strategy', 'audible_emotion', 'volume', 'distance',
    'pace', 'emphasis', 'breath', 'pause',
)
DIALOGUE_PERFORMANCE_TRIGGER_FIELDS = tuple(key for key in DIALOGUE_PERFORMANCE_FIELDS if key != 'voice_profile_id')
SOUND_REQUIRED_FIELDS = ('environment', 'foley', 'sync_sound', 'spatial_acoustics', 'music_policy')
SOUND_STRUCTURE_TRIGGER_FIELDS = ('environment', 'foley', 'sync_sound', 'spatial_acoustics')
NO_MUSIC_MARKERS = ('无bgm', '无配乐', '禁止自动情绪音乐', 'no bgm', 'no music')


def _structured_dialogue_entries(value: Any) -> list[dict] | None:
    """Return structured dialogue entries; None means non-empty legacy/flattened data."""
    if value is None or value == '' or value == [] or value == {}:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        if all(isinstance(item, dict) for item in value):
            return value
        return None
    return None


def _validate_dialogue_entry(entry: dict, label: str, errors: list[str], *, strict: bool = False) -> None:
    for key in DIALOGUE_REQUIRED_FIELDS:
        if not _has_content(entry.get(key)):
            errors.append(f'{label}: GU_DIALOGUE_STRUCTURE missing {key}')
    if strict or any(key in entry for key in DIALOGUE_PERFORMANCE_TRIGGER_FIELDS):
        for key in DIALOGUE_PERFORMANCE_FIELDS:
            if not _has_content(entry.get(key)):
                errors.append(f'{label}: GU_DIALOGUE_PERFORMANCE missing {key}')
    if 'lip_sync' in entry and not isinstance(entry.get('lip_sync'), bool):
        errors.append(f'{label}: GU_DIALOGUE_STRUCTURE lip_sync must be boolean')
    voice_id = str(entry.get('voice_profile_id') or '').strip()
    if voice_id and (not voice_id.startswith('V') or not voice_id[1:].isdigit()):
        errors.append(f'{label}: GU_DIALOGUE_VOICE invalid voice_profile_id {voice_id}')


def _validate_sound(value: Any, label: str, errors: list[str], *, strict: bool = False) -> None:
    if not isinstance(value, dict):
        # Legacy 4.2 projects used a compiled string. New 4.3 payloads use the
        # structured keys below; migration owns upgrading old runtime state.
        if _has_content(value) and not strict:
            return
        errors.append(f'{label}: SOUND_STRUCTURE must be an object')
        return
    if not strict and not any(key in value for key in SOUND_STRUCTURE_TRIGGER_FIELDS):
        return
    for key in SOUND_REQUIRED_FIELDS:
        if not _has_content(value.get(key)):
            errors.append(f'{label}: SOUND_STRUCTURE missing {key}')
    music_policy = str(value.get('music_policy') or '').strip().lower()
    has_no_music = any(marker in music_policy for marker in NO_MUSIC_MARKERS)
    has_authorized_cue = _has_content(value.get('music_cue_source'))
    if not has_no_music and not has_authorized_cue:
        errors.append(f'{label}: BGM_FORBIDDEN music requires an explicit locked music_cue_source; default is no BGM')


def _validate_space_diagram(spatial: Any, label: str, errors: list[str]) -> None:
    if not isinstance(spatial, dict):
        errors.append(f'{label}: spatial_blocking must be an object')
        return
    required = spatial.get('needs_space_diagram') is True
    diagram = spatial.get('space_diagram')
    if not required:
        if _has_content(diagram):
            errors.append(f'{label}: SPACE_DIAGRAM_OVERUSE simple scene must not emit a space diagram')
        return
    if not isinstance(diagram, dict):
        errors.append(f'{label}: SPACE_DIAGRAM_REQUIRED complex scene is missing space_diagram')
        return
    for key in ('north', 'axis_line', 'camera_side', 'ascii_map', 'characters', 'camera', 'props', 'entrances_exits', 'visibility_hearing'):
        if not _has_content(diagram.get(key)):
            errors.append(f'{label}.space_diagram: SPACE_DIAGRAM_REQUIRED missing {key}')
    ascii_lines = diagram.get('ascii_map')
    if not isinstance(ascii_lines, list) or len(ascii_lines) < 4 or not all(isinstance(item, str) and item.strip() for item in ascii_lines):
        errors.append(f'{label}.space_diagram.ascii_map: SPACE_DIAGRAM_REQUIRED must be a non-empty boxed text map')
        return
    map_text = '\n'.join(ascii_lines)
    if '┌' not in map_text or '└' not in map_text or 'CAM' not in map_text.upper():
        errors.append(f'{label}.space_diagram.ascii_map: SPACE_DIAGRAM_CONTENT must contain a box and CAM marker')
    axis_id = str(diagram.get('axis_line') or '').split('：', 1)[0].split(':', 1)[0].strip()
    if axis_id and axis_id not in map_text:
        errors.append(f'{label}.space_diagram.ascii_map: SPACE_DIAGRAM_CONTENT missing axis marker {axis_id}')
    for character in diagram.get('characters', []) if isinstance(diagram.get('characters'), list) else []:
        asset_id = str(character.get('asset_id') or '') if isinstance(character, dict) else ''
        if asset_id and asset_id not in map_text:
            errors.append(f'{label}.space_diagram.ascii_map: SPACE_DIAGRAM_CONTENT missing character {asset_id}')


def _dialogue_signature(entry: dict) -> tuple[str, str]:
    return (str(entry.get('speaker') or '').strip(), str(entry.get('verbatim') or '').strip())


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return bool(value) and any(_has_content(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return bool(value) and any(_has_content(v) for v in value)
    return True


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value.strip()
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)


def _contains_boilerplate(value: Any) -> str | None:
    for text in _walk_strings(value):
        if text.lower() in {x.lower() for x in BOILERPLATE_EXACT}:
            return text
    return None


def validate_storyboard_payload(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ['payload must be an object']
    strict_v43 = str(data.get('storyboard_contract_version') or '') == '4.3'
    shots = data.get('edit_shots')
    units = data.get('generation_units')
    if not isinstance(shots, list) or not shots:
        errors.append('edit_shots must be a non-empty list')
        shots = []
    if not isinstance(units, list) or not units:
        errors.append('generation_units must be a non-empty list')
        units = []

    shot_ids: set[str] = set()
    shot_durations: dict[str, float] = {}
    for i, shot in enumerate(shots):
        prefix = f'edit_shots[{i}]'
        if not isinstance(shot, dict):
            errors.append(f'{prefix} must be an object')
            continue
        for key in REQUIRED_SHOT_FIELDS:
            if key not in shot:
                errors.append(f'{prefix} missing {key}')
            elif key not in {'visual_asset_calls', 'dialogue_execution'} and not _has_content(shot[key]):
                errors.append(f'{prefix}.{key} is empty')
        shot_id = str(shot.get('edit_shot_id') or '')
        if shot_id:
            if shot_id in shot_ids:
                errors.append(f'duplicate edit_shot_id {shot_id}')
            shot_ids.add(shot_id)
            if not shot_id.startswith('SH') or not shot_id[2:].isdigit():
                errors.append(f'{prefix}.edit_shot_id invalid: {shot_id}')
        source = shot.get('source') if isinstance(shot.get('source'), dict) else {}
        source_scene = str(source.get('scene_id') or '').strip()
        shot_scene = str(shot.get('scene_id') or '').strip()
        if source_scene and shot_scene and source_scene != shot_scene:
            errors.append(f'{prefix}.source.scene_id {source_scene} does not match shot scene_id {shot_scene}')

        duration = shot.get('edit_shot_duration')
        if not isinstance(duration, (int, float)) or duration <= 0:
            errors.append(f'{prefix}.edit_shot_duration must be > 0')
        elif shot_id:
            shot_durations[shot_id] = float(duration)
        continuous = shot.get('continuous_visuals')
        if not isinstance(continuous, list):
            errors.append(f'{prefix}.continuous_visuals must be a list')
        assets = shot.get('visual_asset_calls', [])
        if not isinstance(assets, list):
            errors.append(f'{prefix}.visual_asset_calls must be a list')
        else:
            for j, asset in enumerate(assets):
                if not isinstance(asset, dict):
                    errors.append(f'{prefix}.visual_asset_calls[{j}] must be an object')
                    continue
                asset_id = str(asset.get('asset_id') or '')
                if asset_id.startswith('V'):
                    errors.append(f'{prefix}: VOICE_MEDIA_LEAK {asset_id} cannot be visual media')
                for key in ('asset_id', 'name', 'file', 'role', 'shot_use'):
                    if not _has_content(asset.get(key)):
                        errors.append(f'{prefix}.visual_asset_calls[{j}] missing {key}')
        shot_dialogue = _structured_dialogue_entries(shot.get('dialogue_execution'))
        if shot_dialogue is None:
            errors.append(f'{prefix}.dialogue_execution: GU_DIALOGUE_STRUCTURE must preserve speaker/verbatim as structured entries')
        else:
            for j, entry in enumerate(shot_dialogue):
                _validate_dialogue_entry(entry, f'{prefix}.dialogue_execution[{j}]', errors, strict=strict_v43)
        _validate_space_diagram(shot.get('spatial_blocking'), f'{prefix}.spatial_blocking', errors)
        _validate_sound(shot.get('sound'), f'{prefix}.sound', errors, strict=strict_v43)

        bad = _contains_boilerplate({
            'shot_function': shot.get('shot_function'),
            'base_frame': shot.get('base_frame'),
            'camera_parameters': shot.get('camera_parameters'),
            'axis_and_gaze': shot.get('axis_and_gaze'),
            'spatial_blocking': shot.get('spatial_blocking'),
            'key_micro_reactions': shot.get('key_micro_reactions'),
            'sound': shot.get('sound'),
            'continuity_locks': shot.get('continuity_locks'),
        })
        if bad:
            errors.append(f'{prefix}: FIELD_BOILERPLATE: {bad}')

    unit_ids: set[str] = set()
    membership: dict[str, str] = {}
    for i, unit in enumerate(units):
        prefix = f'generation_units[{i}]'
        if not isinstance(unit, dict):
            errors.append(f'{prefix} must be an object')
            continue
        for key in REQUIRED_GU_FIELDS:
            if key not in unit:
                errors.append(f'{prefix} missing {key}')
            elif key not in {'active_media_references', 'voice_text_assets'} and not _has_content(unit[key]):
                errors.append(f'{prefix}.{key} is empty')
        unit_id = str(unit.get('generation_unit_id') or '')
        if unit_id:
            if unit_id in unit_ids:
                errors.append(f'duplicate generation_unit_id {unit_id}')
            unit_ids.add(unit_id)
            if not unit_id.startswith('GU') or not unit_id[2:].isdigit():
                errors.append(f'{prefix}.generation_unit_id invalid: {unit_id}')
        duration = unit.get('duration')
        model = unit.get('target_video_model')
        if not isinstance(duration, (int, float)) or duration <= 0:
            errors.append(f'{prefix}.duration must be > 0')
        elif model in MODEL_LIMITS and float(duration) > MODEL_LIMITS[model]:
            errors.append(f'{prefix}: MODEL_WINDOW {model} duration {duration}s > {MODEL_LIMITS[model]:g}s')
        elif model == 'OTHER':
            max_seconds = unit.get('model_call_max_seconds')
            if not isinstance(max_seconds, (int, float)) or max_seconds <= 0:
                errors.append(f'{prefix}: MODEL_WINDOW OTHER requires model_call_max_seconds')
            elif isinstance(duration, (int, float)) and duration > max_seconds:
                errors.append(f'{prefix}: MODEL_WINDOW OTHER duration {duration}s > {max_seconds}s')
        members = unit.get('member_edit_shots', [])
        if not isinstance(members, list) or not members:
            errors.append(f'{prefix}.member_edit_shots must be non-empty')
        else:
            for member in members:
                if member not in shot_ids:
                    errors.append(f'{prefix}: member edit shot not found: {member}')
                if member in membership:
                    errors.append(f'{member} belongs to multiple GUs: {membership[member]}, {unit_id}')
                membership[member] = unit_id
        if isinstance(members, list) and members and isinstance(duration, (int, float)) and duration > 0:
            member_durations = [shot_durations.get(str(member)) for member in members]
            if all(item is not None for item in member_durations):
                member_runtime = sum(float(item) for item in member_durations)
                if abs(float(duration) - member_runtime) > EPSILON:
                    errors.append(f'{prefix}.duration {duration}s does not match member SH runtime {member_runtime:g}s')
        if unit.get('mode') == 'MULTI_SHOT':
            if unit.get('model_supports_multi_shot') is not True:
                errors.append(f'{prefix}: MULTI_SHOT_MODEL_SUPPORT_NOT_CONFIRMED')
            if not unit.get('contains_explicit_cuts'):
                errors.append(f'{prefix}: MULTI_SHOT requires contains_explicit_cuts=true')
        if strict_v43 or 'starting_state' in unit or 'ending_state' in unit:
            if not isinstance(unit.get('starting_state'), dict) or not _has_content(unit.get('starting_state')):
                errors.append(f'{prefix}.starting_state must be a non-empty structured object')
            if not isinstance(unit.get('ending_state'), dict) or not _has_content(unit.get('ending_state')):
                errors.append(f'{prefix}.ending_state must be a non-empty structured object')
        phases = unit.get('phases', [])
        if not isinstance(phases, list) or not phases:
            errors.append(f'{prefix}.phases must be non-empty')
        else:
            for j, phase in enumerate(phases):
                if not isinstance(phase, dict):
                    errors.append(f'{prefix}.phases[{j}] must be an object')
                    continue
                for key in ('phase_id', 'stage_goal', 'image_and_camera', 'action_and_physics', 'performance_and_microreaction', 'dialogue_execution', 'end_state'):
                    if key not in phase:
                        errors.append(f'{prefix}.phases[{j}] missing {key}')
                    elif key != 'dialogue_execution' and not _has_content(phase.get(key)):
                        errors.append(f'{prefix}.phases[{j}] missing {key}')
                phase_id = str(phase.get('phase_id') or '')
                if phase_id and (not phase_id.startswith('PH') or not phase_id[2:].isdigit()):
                    errors.append(f'{prefix}.phases[{j}].phase_id invalid: {phase_id}')
        # Final GU dialogue is a direct-execution contract. It must preserve the
        # current Member SH dialogue as structured speaker/verbatim records rather
        # than flattening multiple speakers into an anonymous string.
        expected_dialogue: list[dict] = []
        for member_id in members if isinstance(members, list) else []:
            member_shot = next((shot for shot in shots if isinstance(shot, dict) and str(shot.get('edit_shot_id') or '') == str(member_id)), None)
            if not isinstance(member_shot, dict):
                continue
            entries = _structured_dialogue_entries(member_shot.get('dialogue_execution'))
            if entries:
                expected_dialogue.extend(entries)

        gu_dialogue: list[dict] = []
        gu_dialogue_structured = True
        for j, phase in enumerate(phases if isinstance(phases, list) else []):
            if not isinstance(phase, dict):
                continue
            raw_dialogue = phase.get('dialogue_execution')
            entries = _structured_dialogue_entries(raw_dialogue)
            if entries is None:
                if _has_content(raw_dialogue):
                    errors.append(
                        f'{prefix}.phases[{j}].dialogue_execution: GU_DIALOGUE_STRUCTURE '
                        'locked dialogue must be structured; flattened strings are forbidden'
                    )
                    gu_dialogue_structured = False
                continue
            for k, entry in enumerate(entries):
                _validate_dialogue_entry(entry, f'{prefix}.phases[{j}].dialogue_execution[{k}]', errors, strict=strict_v43)
                voice_id = str(entry.get('voice_profile_id') or '').strip()
                if voice_id and voice_id not in {str(x) for x in unit.get('voice_text_assets', []) if str(x)}:
                    errors.append(
                        f'{prefix}.phases[{j}].dialogue_execution[{k}]: GU_DIALOGUE_VOICE '
                        f'{voice_id} is not declared in current GU voice_text_assets'
                    )
                gu_dialogue.append(entry)

        if gu_dialogue_structured:
            if len(expected_dialogue) != len(gu_dialogue):
                if expected_dialogue or gu_dialogue:
                    errors.append(
                        f'{prefix}: GU_DIALOGUE_MISMATCH Member SH has {len(expected_dialogue)} locked lines '
                        f'but GU phases have {len(gu_dialogue)} structured lines'
                    )
            else:
                for j, (expected, actual) in enumerate(zip(expected_dialogue, gu_dialogue)):
                    if _dialogue_signature(expected) != _dialogue_signature(actual):
                        errors.append(
                            f'{prefix}: GU_DIALOGUE_MISMATCH line {j + 1} speaker/verbatim/order changed '
                            f'from {_dialogue_signature(expected)} to {_dialogue_signature(actual)}'
                        )
                        continue
                    for key in DIALOGUE_PRESERVE_FIELDS:
                        if key in expected and expected.get(key) != actual.get(key):
                            errors.append(
                                f'{prefix}: GU_DIALOGUE_MISMATCH line {j + 1} {key} changed '
                                f'from {expected.get(key)!r} to {actual.get(key)!r}'
                            )

        sections = unit.get('prompt_sections', {})
        if not isinstance(sections, dict):
            errors.append(f'{prefix}.prompt_sections must be an object')
        else:
            for key in REQUIRED_PROMPT_SECTIONS:
                if not _has_content(sections.get(key)):
                    errors.append(f'{prefix}.prompt_sections missing {key}')
            _validate_reference_roles(
                sections.get('reference_roles'), f'{prefix}.prompt_sections.reference_roles', errors
            )
            _validate_sound(sections.get('sound'), f'{prefix}.prompt_sections.sound', errors, strict=strict_v43)
            bad = _contains_boilerplate(sections)
            if bad:
                errors.append(f'{prefix}: FIELD_BOILERPLATE: {bad}')
            for text in _walk_strings(sections):
                if text.lower() in {'同上', '继承上一镜', 'same as before', 'as above'}:
                    errors.append(f'{prefix}: stale shorthand forbidden: {text}')

        if isinstance(members, list) and members:
            member_shots = [
                next((shot for shot in shots if isinstance(shot, dict) and shot.get('edit_shot_id') == member), None)
                for member in members
            ]
            member_shots = [shot for shot in member_shots if isinstance(shot, dict)]
            if member_shots:
                first_anchors = member_shots[0].get('first_last_frame_anchors') if isinstance(member_shots[0].get('first_last_frame_anchors'), dict) else {}
                last_anchors = member_shots[-1].get('first_last_frame_anchors') if isinstance(member_shots[-1].get('first_last_frame_anchors'), dict) else {}
                if (strict_v43 or 'starting_state' in unit) and unit.get('starting_state') != first_anchors.get('first_frame'):
                    errors.append(f'{prefix}: GU_START_STATE_MISMATCH starting_state must equal first Member SH first_frame')
                if (strict_v43 or 'ending_state' in unit) and unit.get('ending_state') != last_anchors.get('last_frame'):
                    errors.append(f'{prefix}: GU_END_STATE_MISMATCH ending_state must equal last Member SH last_frame')

    for previous, current in zip(units, units[1:]):
        if not isinstance(previous, dict) or not isinstance(current, dict):
            continue
        if (strict_v43 or 'ending_state' in previous or 'starting_state' in current) and previous.get('ending_state') != current.get('starting_state'):
            errors.append(
                f'{previous.get("generation_unit_id", "UNKNOWN")}→{current.get("generation_unit_id", "UNKNOWN")}: '
                'GU_CONTINUITY_MISMATCH previous ending_state must equal next starting_state'
            )

    # A model window is a ceiling, never an editorial duration template. Two
    # or more SHs that all land exactly on the same 15/30 second ceiling are a
    # strong mechanical-quantization signal. Deliberate equal long takes remain
    # legal when every affected SH records its own dramatic duration basis.
    if len(shots) >= 2:
        quantized: list[dict] = []
        units_by_id = {
            str(unit.get('generation_unit_id') or ''): unit
            for unit in units if isinstance(unit, dict)
        }
        for shot in shots:
            if not isinstance(shot, dict):
                continue
            duration = shot.get('edit_shot_duration')
            unit = units_by_id.get(str(shot.get('generation_unit_id') or ''))
            if not isinstance(duration, (int, float)) or not isinstance(unit, dict):
                continue
            model = str(unit.get('target_video_model') or '')
            limit = MODEL_LIMITS.get(model)
            if limit is not None and abs(float(duration) - float(limit)) <= EPSILON:
                quantized.append(shot)
        if len(quantized) == len(shots):
            durations = {float(shot['edit_shot_duration']) for shot in quantized}
            missing_basis = [
                str(shot.get('edit_shot_id') or 'UNKNOWN')
                for shot in quantized
                if not _has_content(shot.get('duration_basis'))
            ]
            if len(durations) == 1 and missing_basis:
                errors.append(
                    'MECHANICAL_DURATION_QUANTIZATION: model_call_max_seconds is a ceiling, '
                    'not a fixed SH duration; missing story-driven duration_basis for '
                    + ', '.join(missing_basis)
                )

    for shot in shots:
        if not isinstance(shot, dict):
            continue
        sid = str(shot.get('edit_shot_id') or '')
        declared = str(shot.get('generation_unit_id') or '')
        actual = membership.get(sid)
        if sid and not actual:
            errors.append(f'{sid} is not assigned to any GU')
        elif sid and declared and actual and declared != actual:
            errors.append(f'{sid}.generation_unit_id={declared} but GU membership={actual}')
    return errors




def _normalized_qc_token(value: Any) -> str:
    if not isinstance(value, str):
        return ''
    return re.sub(r'\s+', ' ', value.strip().lower())


SHOT_SIZE_TOKENS = {
    'ews', 'ws', 'ls', 'mls', 'fs', 'mfs', 'ms', 'mcu', 'cu', 'ecu',
    '远景', '大远景', '全景', '大全景', '中全景', '中景', '中近景', '近景', '特写', '大特写',
}


def _explicit_shot_size(shot: dict) -> str:
    value = shot.get('shot_type')
    if isinstance(value, str):
        token = _normalized_qc_token(value)
        return token if token in SHOT_SIZE_TOKENS else ''
    if not isinstance(value, dict):
        return ''
    for key in ('shot_size', 'framing', 'size'):
        token = _normalized_qc_token(value.get(key))
        if token:
            return token
    return ''


def _explicit_camera_move(shot: dict) -> str:
    value = shot.get('camera_parameters')
    if not isinstance(value, dict):
        return ''
    for key in ('camera_move', 'camera_movement', 'movement', 'camera_behavior'):
        token = _normalized_qc_token(value.get(key))
        if token:
            return token
    return ''


def sequence_quality_warnings(payload: dict) -> list[str]:
    """Return non-blocking whole-sequence warnings based only on explicit structured evidence."""
    shots = payload.get('edit_shots') if isinstance(payload.get('edit_shots'), list) else []
    warnings: list[str] = []
    run_pair: tuple[str, str] | None = None
    run_ids: list[str] = []

    def flush() -> None:
        nonlocal run_pair, run_ids
        if run_pair is not None and len(run_ids) >= 3:
            warnings.append(
                'MONOTONY_AUDIT: consecutive SHs repeat the same explicit shot size and camera move: '
                + '→'.join(run_ids)
                + f' [{run_pair[0]} / {run_pair[1]}]. Review intent; this is a WARNING, not a blocker.'
            )
        run_pair = None
        run_ids = []

    for shot in shots:
        if not isinstance(shot, dict):
            flush()
            continue
        size = _explicit_shot_size(shot)
        move = _explicit_camera_move(shot)
        if not size or not move:
            flush()
            continue
        pair = (size, move)
        sid = str(shot.get('edit_shot_id') or 'UNKNOWN')
        if pair == run_pair:
            run_ids.append(sid)
        else:
            flush()
            run_pair = pair
            run_ids = [sid]
    flush()
    return warnings

def _labelize(key: str) -> str:
    labels = {
        'scene_id': 'SCENE_ID', 'story_range': '对应剧情范围', 'director_beat': '对应导演节拍',
        'dramatic_task': '场景戏剧任务', 'allowed_information': '允许观众看到的信息',
        'forbidden_information': '禁止提前露出的信息', 'world_rules': '必须继承的世界规则限制',
        'primary': '主要任务', 'change_after_shot': '本镜结束后改变了什么',
        'location_time': '地点与时间', 'functional_zone': '当前功能区', 'framing_and_position': '景别与机位',
        'camera_behavior': '摄影机行为', 'perspective': '透视倾向或焦段', 'height': '摄影机高度',
        'angle': '拍摄角度', 'depth_focus': '景深与焦点', 'composition': '构图重心', 'layers': '前中后景关系',
        'look_motion_room': '视线留白与运动留白', 'axis': '当前对话轴线或动作轴线', 'axis_line': '轴线ID与定义', 'camera_side': '摄影机侧',
        'gaze': '人物视线方向', 'screen_direction': '屏幕方向', 'cross_axis_allowed': '是否允许越轴',
        'cross_axis_transition': '越轴过渡', 'location_asset': '继承的S场景', 'dramatic_purpose': '站位的剧情目的',
        'visibility_hearing': '人物之间的可见／可听关系', 'start_positions': '人物起始物理位置', 'frame_positions': '人物画面位置',
        'movement_path': '移动路径', 'end_positions': '人物结束物理位置', 'needs_space_diagram': '是否需要空间占位图',
        'first_frame': '首帧准确画面', 'last_frame': '尾帧准确画面', 'locked_between': '首尾之间必须保持不变的连续状态',
        'stimulus': '接收刺激', 'first_reaction': '第一反应', 'control': '掩饰或重新控制', 'final_action': '最终动作或回答',
        'verbatim': '逐字对白', 'speaker': '说话人', 'voice_profile_id': 'Voice Profile', 'mode': '画内 / 画外 / 旁白', 'lip_sync': '是否需要口型同步',
        'performance_strategy': '人物策略', 'audible_emotion': '可听情绪', 'volume': '音量', 'distance': '声源距离',
        'pace': '语速', 'emphasis': '重音', 'breath': '呼吸', 'pause': '停顿',
        'camera_subject': '镜头主要拍摄对象', 'delivery': '停顿、重音、呼吸与被打断位置', 'onscreen': '画面内声音',
        'ambience': '环境声远近与空间感', 'environment': '环境声', 'foley': 'Foley', 'sync_sound': '同期声',
        'spatial_acoustics': '空间声学', 'special': '特殊声音', 'bridge': '声音桥 / J-cut / L-cut', 'music_policy': '音乐策略',
        'cut_in': '切入依据', 'cut_out': '切出触发动作或声音', 'action_match': '是否动作匹配', 'gaze_match': '是否视线匹配',
        'sound_lead': '是否由声音提前带入下一镜', 'wardrobe': '服装', 'injury_wet_dirt': '伤势、湿度与污损',
        'hair_face': '发型与面部状态', 'hand_props': '手持道具及左右手', 'orientation_screen': '人物朝向与屏幕方向',
        'physical_position': '人物物理位置', 'light_time_weather': '光线、时间与天气状态', 'other_state': '形态或其他持续状态',
        'known_information': '本镜人物可依据的已知信息', 'forbidden_future': '不得出现的未来信息或未揭露证据',
        'world_ability_limits': '特殊能力/技术当前可用范围与代价', 'type': '类型', 'start_state': '下一镜从什么状态开始',
        'do_not_reset': '不得重置', 'duration_basis': '剧情驱动时长依据',
    }
    return labels.get(key, key)


def _render_value(value: Any, indent: int = 0) -> list[str]:
    if isinstance(value, dict):
        lines: list[str] = []
        for key, val in value.items():
            if isinstance(val, (dict, list)):
                lines.append(f"- {_labelize(key)}：")
                nested = _render_value(val, indent + 1)
                lines.extend(('  ' + line) if line else '' for line in nested)
            else:
                lines.append(f"- {_labelize(key)}：{val}")
        return lines
    if isinstance(value, list):
        return [f'- {item}' for item in value]
    return [str(value)]


def _section(title: str, value: Any) -> list[str]:
    return [title, *_render_value(value), '']


def _render_assets(assets: list[dict]) -> list[str]:
    lines = ['【资产调用】']
    for idx, asset in enumerate(assets, start=1):
        lines.append(
            f"图{idx}【{asset['asset_id']}】是【{asset['name']}】（{asset['file']}），"
            f"负责{asset['role']}，有{asset['shot_use']}"
        )
    lines.extend(['--------资产调用完毕-------', ''])
    return lines


def _render_space_diagram(diagram: dict) -> list[str]:
    lines = ['【空间占位图】', '', f"固定北向：{diagram['north']}", '', '```text']
    lines.extend(str(item) for item in diagram['ascii_map'])
    lines.extend(['```', '', f"- axis_line：{diagram['axis_line']}", f"- camera_side：{diagram['camera_side']}"])
    lines.extend(_render_value({'characters': diagram['characters']}))
    lines.append(f"- 摄影机位置与方向：{diagram['camera']}")
    lines.extend(_render_value({'props': diagram['props'], 'entrances_exits': diagram['entrances_exits']}))
    lines.append(f"- 人物之间的可见／可听关系：{diagram['visibility_hearing']}")
    lines.append('')
    return lines



def _render_phase_dialogue(value: Any) -> list[str]:
    entries = _structured_dialogue_entries(value)
    if not entries:
        return []
    lines: list[str] = []
    for entry in entries:
        speaker = str(entry.get('speaker') or '').strip()
        verbatim = str(entry.get('verbatim') or '').strip()
        voice_id = str(entry.get('voice_profile_id') or '').strip()
        identity = f'{speaker}【{voice_id}】' if voice_id else speaker
        lines.append(f'- 对白执行：{identity}：“{verbatim}”')
        details: list[str] = []
        mode = str(entry.get('mode') or '').strip()
        if mode:
            details.append(f'模式：{mode}')
        if isinstance(entry.get('lip_sync'), bool):
            details.append(f"口型同步：{'是' if entry['lip_sync'] else '否'}")
        detail_labels = (
            ('performance_strategy', '人物策略'), ('audible_emotion', '可听情绪'), ('volume', '音量'),
            ('distance', '距离'), ('pace', '语速'), ('emphasis', '重音'), ('breath', '呼吸'), ('pause', '停顿'),
        )
        details.extend(f'{label}：{entry[key]}' for key, label in detail_labels if _has_content(entry.get(key)))
        delivery = str(entry.get('delivery') or '').strip()
        if delivery:
            details.append(f'表演：{delivery}')
        if details:
            lines.append('  - ' + '｜'.join(details))
    return lines


def _render_gu(unit: dict, shots_by_id: dict[str, dict]) -> list[str]:
    lines = [
        f"## {unit['generation_unit_id']}｜视频模型最终 Prompt",
        '',
        f"- 模型：{unit['target_video_model']}｜时长：{unit['duration']}秒｜模式：{unit['mode']}",
        f"- Member SH：{', '.join(unit['member_edit_shots'])}",
        f"- Packing：{unit['packing_policy']}",
        f"- Explicit Cuts：{'是' if unit['contains_explicit_cuts'] else '否'}",
        '',
        '【生成目标】',
        str(unit['prompt_sections']['generation_goal']),
        '',
        '【参考素材职责】',
    ]
    refs = reference_role_items(unit['prompt_sections']['reference_roles'])
    if refs:
        lines.extend(f'- {render_reference_role(item)}' for item in refs)
    else:
        lines.append(str(unit['prompt_sections']['reference_roles']))
    for member_id in unit['member_edit_shots']:
        shot = shots_by_id.get(str(member_id), {})
        spatial = shot.get('spatial_blocking') if isinstance(shot.get('spatial_blocking'), dict) else {}
        if spatial.get('needs_space_diagram') is True and isinstance(spatial.get('space_diagram'), dict):
            lines.extend([''])
            lines.extend(_render_space_diagram(spatial['space_diagram']))
    lines.extend(['', '【初始状态】', str(unit['prompt_sections']['initial_state']), '', '【阶段推进】'])
    for phase in unit['phases']:
        phase_lines = [
            f"### {phase['phase_id']}｜{phase['stage_goal']}",
            f"- 画面与摄影机：{phase['image_and_camera']}",
            f"- 动作与物理：{phase['action_and_physics']}",
            f"- 表演与微反应：{phase['performance_and_microreaction']}",
        ]
        if _has_content(phase.get('dialogue_execution')):
            phase_lines.extend(_render_phase_dialogue(phase.get('dialogue_execution')))
        phase_lines.extend([f"- 阶段尾态：{phase['end_state']}", ''])
        lines.extend(phase_lines)
    anchors = unit.get('critical_time_anchors') or []
    if anchors:
        lines.extend(['【关键时间锚点｜可选】'])
        lines.extend(f'- {item}' for item in anchors)
        lines.append('')
    lines.extend(['【声音】'])
    lines.extend(_render_value(unit['prompt_sections']['sound']))
    lines.extend([
        '', '【保持一致】', str(unit['prompt_sections']['keep_consistent']), '',
        '【局部限制】', str(unit['prompt_sections']['local_constraints']), '',
        '----此生成单元结束----', '',
    ])
    return lines


def render_storyboard(data: dict) -> str:
    errors = validate_storyboard_payload(data)
    if errors:
        raise ValueError('Storyboard validation failed:\n- ' + '\n- '.join(errors))
    lines = ['# 正式分镜与视频生成Prompt', '']
    for shot in data['edit_shots']:
        title = shot.get('title') or shot['edit_shot_id']
        lines.extend([
            f"# {shot['scene_id']}｜{shot['edit_shot_id']}｜{title}",
            '',
            f"- EDIT_SHOT_DURATION：{shot['edit_shot_duration']}秒",
            f"- DURATION_BASIS：{shot.get('duration_basis', '由当前剧情动作、表演和剪辑需要决定')}",
            f"- GENERATION_UNIT_ID：{shot['generation_unit_id']}",
            '',
        ])
        lines += _section('【来源】', shot['source'])
        lines += _section('【镜头功能】', shot['shot_function'])
        lines += _section('【镜头类型】', shot['shot_type'])
        lines += _section('【基础画面】', shot['base_frame'])
        lines += _section('【摄影参数】', shot['camera_parameters'])
        lines += _section('【轴线与视线】', shot['axis_and_gaze'])
        lines += _render_assets(shot['visual_asset_calls'])
        spatial = shot['spatial_blocking']
        lines += _section('【空间与站位】', {key: value for key, value in spatial.items() if key != 'space_diagram'})
        if spatial.get('needs_space_diagram') is True:
            lines += _render_space_diagram(spatial['space_diagram'])
        lines += _section('【连续画面】', shot['continuous_visuals'])
        lines += _section('【首尾帧锚点】', shot['first_last_frame_anchors'])
        lines += _section('【关键微反应】', shot['key_micro_reactions'])
        if _has_content(shot.get('dialogue_execution')):
            lines += _section('【对白执行】', shot['dialogue_execution'])
        lines += _section('【声音】', shot['sound'])
        lines += _section('【剪辑接口】', shot['edit_interface'])
        lines += _section('【连续性锁】', shot['continuity_locks'])
        lines += _section('【下一镜衔接】', shot['next_shot_handoff'])
        lines.extend(['----此分镜结束----', ''])
    lines.extend(['# Generation Units｜视频模型执行单元', ''])
    shots_by_id = {str(shot['edit_shot_id']): shot for shot in data['edit_shots']}
    for unit in data['generation_units']:
        lines += _render_gu(unit, shots_by_id)
    return '\n'.join(lines).rstrip() + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate and render CineWeaver structured storyboard JSON to fixed Markdown')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding='utf-8'))
    errors = validate_storyboard_payload(data)
    if errors:
        for error in errors:
            print(f'ERROR: {error}')
        return 1
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_storyboard(data), encoding='utf-8')
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
