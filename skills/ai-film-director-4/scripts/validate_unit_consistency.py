#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from render_asset_library import render_asset_library, validate_asset_library_payload
from render_storyboard import render_storyboard, validate_storyboard_payload, reference_role_items, render_reference_role
from render_emotion_map import render_emotion_html, validate_emotion_payload
from compile_forge_handoff import validate_alignment
from scene_geo_lock import validate_scene_geo_contract

FILM_FORMATS = {'film', 'short_film'}
SERIES_FORMATS = {'series', 'short_series'}
EPSILON = 0.01


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_object(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _existing_media_path(root: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = Path(value)
    candidates = [raw] if raw.is_absolute() else [root / raw, root / 'assets' / raw, root / 'assets' / 'generated' / raw.name]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _asset_records(payload: dict) -> tuple[dict[str, dict], set[str]]:
    lib = payload.get('ASSET_LIBRARY', {}) if isinstance(payload, dict) else {}
    records: dict[str, dict] = {}
    voice_ids: set[str] = set()
    for group in ('character_assets', 'location_assets', 'prop_assets', 'g_assets'):
        for record in lib.get(group, []) or []:
            if isinstance(record, dict) and isinstance(record.get('asset_id'), str):
                records[record['asset_id']] = record
    for state in lib.get('persistent_states', []) or []:
        if isinstance(state, dict) and isinstance(state.get('state_id'), str):
            copy = dict(state)
            copy['asset_id'] = state['state_id']
            records[state['state_id']] = copy
    for voice in lib.get('voice_assets', []) or []:
        if isinstance(voice, dict) and isinstance(voice.get('asset_id'), str):
            records[voice['asset_id']] = voice
            voice_ids.add(voice['asset_id'])
    return records, voice_ids


def _validate_asset_authority(root: Path, errors: list[str], *, require_project_baseline: bool = False) -> tuple[dict[str, dict], set[str]]:
    json_path = root / 'assets' / 'ASSET_LIBRARY.json'
    md_path = root / 'assets' / 'ASSET_LIBRARY.md'
    payload = _load_object(json_path)
    if payload is None:
        errors.append('缺少或无法解析唯一资产权威：assets/ASSET_LIBRARY.json')
        return {}, set()
    asset_errors = validate_asset_library_payload(payload)
    errors.extend(f'ASSET_LIBRARY：{item}' for item in asset_errors)
    if not asset_errors:
        expected = render_asset_library(payload)
        if not md_path.is_file():
            errors.append('缺少Renderer生成的资产文件：assets/ASSET_LIBRARY.md')
        elif md_path.read_text(encoding='utf-8') != expected:
            errors.append('assets/ASSET_LIBRARY.md 不是当前ASSET_LIBRARY.json的Renderer固定输出')

    if require_project_baseline:
        try:
            from project_asset_baseline import validate_asset_baseline_lock
            baseline_errors = validate_asset_baseline_lock(root)
            errors.extend(f'PROJECT_ASSET_BASELINE：{item}' for item in baseline_errors)
        except Exception as exc:
            errors.append(f'PROJECT_ASSET_BASELINE：validator failure: {exc}')

    records, voice_ids = _asset_records(payload)
    for asset_id, record in records.items():
        if asset_id in voice_ids:
            continue
        if str(record.get('image_status', '')) == 'GENERATED' and _existing_media_path(root, record.get('image_file')) is None:
            errors.append(f'{asset_id} 标记GENERATED但真实图片文件不存在：{record.get("image_file")}')
    return records, voice_ids



def _validate_emotion_authority(root: Path, errors: list[str]) -> None:
    audit_path = root / 'state' / 'forge_locked_audit.json'
    compat_path = root / 'state' / 'audience_emotion_architecture.json'
    alignment_path = root / 'state' / 'forge_alignment.json'
    html_path = root / 'AUDIENCE_EMOTION_MAP.html'

    payload = _load_object(audit_path)
    if payload is None:
        errors.append('缺少或无法解析Forge锁稿审计：state/forge_locked_audit.json')
        return
    emotion_errors = validate_emotion_payload(payload)
    errors.extend(f'Forge锁稿审计：{item}' for item in emotion_errors)
    if emotion_errors:
        return
    meta = payload.get('meta') if isinstance(payload.get('meta'), dict) else {}
    script_audit = payload.get('script_audit') if isinstance(payload.get('script_audit'), dict) else {}
    if meta.get('workflow_stage') != 'locked_audit' or script_audit.get('lock_status') != 'LOCKED':
        errors.append('正式情绪HTML要求 Forge locked_audit + LOCKED')
        return

    compat = _load_object(compat_path)
    if compat is None:
        errors.append('缺少AFD兼容情绪投影：state/audience_emotion_architecture.json')

    expected = render_emotion_html(payload)
    if not html_path.is_file():
        errors.append('缺少Forge Renderer生成的观众情绪HTML：AUDIENCE_EMOTION_MAP.html')
    elif html_path.read_text(encoding='utf-8') != expected:
        errors.append('AUDIENCE_EMOTION_MAP.html 不是当前 state/forge_locked_audit.json 的Forge Renderer固定输出')

    if (root / 'state' / 'master_orchestrator.json').is_file():
        errors.extend(f'Forge对齐失败：{item}' for item in validate_alignment(root))
        return

    # Legacy low-level fixtures/APIs remain readable without claiming entry into
    # the Master+Forge production chain. FULL run_pipeline validates the new
    # artifact hash set unconditionally before rendering or export.
    alignment = _load_object(alignment_path)
    if alignment is None:
        errors.append('缺少Forge/AFD对齐状态：state/forge_alignment.json')
        return
    if alignment.get('forge_audit_sha256') != _sha256(audit_path):
        errors.append('Forge对齐失败：forge_audit_sha256 与当前锁稿审计不一致')
    if alignment.get('lock_status') != 'LOCKED':
        errors.append('Forge对齐失败：lock_status 必须为 LOCKED')
    unit_id = str(alignment.get('unit_id') or '').strip()
    screenplay_hash = str(alignment.get('screenplay_sha256') or '').strip()
    if unit_id and screenplay_hash:
        screenplay_path = root / 'screenplay' / f'{unit_id}_LOCKED_SCREENPLAY.md'
        if screenplay_path.is_file() and _sha256(screenplay_path) != screenplay_hash:
            errors.append(f'Forge对齐失败：{unit_id} 锁稿 hash 与 forge_alignment 不一致')

def _dialogue_entries(value: Any) -> list[dict]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _speaker_voice_map(records: dict[str, dict], voice_ids: set[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    ambiguous: set[str] = set()
    for asset_id, record in records.items():
        if asset_id in voice_ids or not isinstance(record, dict):
            continue
        name = str(record.get('name') or '').strip()
        voice_id = str(record.get('voice_asset_id') or '').strip()
        if not name or voice_id not in voice_ids:
            continue
        if name in result and result[name] != voice_id:
            ambiguous.add(name)
        else:
            result[name] = voice_id
    for name in ambiguous:
        result.pop(name, None)
    return result


def _validate_gu_voice_binding(payload: dict, records: dict[str, dict], voice_ids: set[str], errors: list[str]) -> None:
    speaker_voice = _speaker_voice_map(records, voice_ids)
    if not speaker_voice:
        return
    for gu in payload.get('generation_units', []) if isinstance(payload.get('generation_units'), list) else []:
        if not isinstance(gu, dict):
            continue
        gu_id = str(gu.get('generation_unit_id') or 'UNKNOWN')
        declared = {str(x) for x in gu.get('voice_text_assets', []) if str(x)} if isinstance(gu.get('voice_text_assets'), list) else set()
        for phase in gu.get('phases', []) if isinstance(gu.get('phases'), list) else []:
            if not isinstance(phase, dict):
                continue
            for entry in _dialogue_entries(phase.get('dialogue_execution')):
                speaker = str(entry.get('speaker') or '').strip()
                expected_voice = speaker_voice.get(speaker)
                if not expected_voice:
                    continue
                actual_voice = str(entry.get('voice_profile_id') or '').strip()
                if actual_voice != expected_voice or expected_voice not in declared:
                    errors.append(
                        f'{gu_id}: GU_DIALOGUE_VOICE speaker {speaker} has locked {expected_voice}; '
                        f'final GU must preserve voice_profile_id={expected_voice} and declare it in voice_text_assets'
                    )



_MEDIA_REFERENCE_RE = re.compile(r'@(?:图片|图像|image)\s*\d+', flags=re.I)
_GENERIC_ANCHOR_WORDS = {
    'identity', '保持一致', '身份一致', '资产', '参考', '文字身份锚', '当前镜头', '只负责', '对应',
}


def _reference_role_strings(value: Any) -> list[str]:
    return [render_reference_role(item) for item in reference_role_items(value) if render_reference_role(item)]


def _structured_reference_role_matches(value: Any, asset_id: str) -> list[dict]:
    return [
        item for item in reference_role_items(value)
        if isinstance(item, dict) and str(item.get('asset_id') or '').strip() == asset_id
    ]


def _structured_anchor_is_specific(entry: dict, record: dict) -> bool:
    # Structure proves source identity via asset_id, but the inherited facts
    # still need enough concrete visual content to be useful. One tiny generic
    # fragment must not satisfy the anchor contract.
    text = '｜'.join(str(item) for item in entry.get('inherits', []) if str(item).strip())
    normalized = _normalized_anchor_text(text)
    matches = {
        _normalized_anchor_text(literal)
        for literal in _flatten_asset_anchor_literals(record)
        if len(_normalized_anchor_text(literal)) >= 2 and _normalized_anchor_text(literal) in normalized
    }
    if len(matches) >= 2:
        return True
    return len(matches) == 1 and len(normalized) >= 8


def _flatten_asset_anchor_literals(record: dict) -> list[str]:
    preferred = (
        'execution_anchor_summary', 'visual_identity', 'story_identity', 'architecture_type',
        'materials_and_color', 'stable_geography', 'visible_change', 'unchanged_facts', 'image_prompt',
    )
    literals: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, str):
            for part in re.split(r'[，。；：、,;|/\\\n]+', value):
                part = part.strip()
                if len(re.sub(r'\s+', '', part)) >= 2:
                    literals.append(part)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)

    for key in preferred:
        if key in record:
            walk(record.get(key))
    # Longer, specific literals first; duplicates removed without reordering.
    unique = list(dict.fromkeys(literals))
    unique.sort(key=lambda item: len(re.sub(r'\s+', '', item)), reverse=True)
    return unique


def _normalized_anchor_text(text: str) -> str:
    return re.sub(r'[\s\u3000，。！？；：、“”‘’（）()【】\[\]—…·,.!?;:\-|/@]+', '', str(text)).lower()


def _entry_has_specific_anchor(entry: str, asset_id: str, record: dict) -> bool:
    normalized = _normalized_anchor_text(entry)
    asset_norm = _normalized_anchor_text(asset_id)
    name = str(record.get('name') or record.get('state_category') or '').strip()
    name_norm = _normalized_anchor_text(name)
    if asset_norm not in normalized:
        return False
    if name_norm and name_norm not in normalized:
        return False

    for literal in _flatten_asset_anchor_literals(record):
        literal_norm = _normalized_anchor_text(literal)
        if len(literal_norm) >= 2 and literal_norm in normalized:
            return True

    # Backward-compatible fallback for sparse asset records: after removing ID,
    # name and generic binding words, a meaningful local visual description is
    # still accepted instead of forcing the asset schema to become more verbose.
    residual = normalized.replace(asset_norm, '')
    if name_norm:
        residual = residual.replace(name_norm, '')
    for word in _GENERIC_ANCHOR_WORDS:
        residual = residual.replace(_normalized_anchor_text(word), '')
    return len(residual) >= 8


def _member_visual_asset_ids(payload: dict, gu: dict) -> list[str]:
    member_ids = {str(item) for item in gu.get('member_edit_shots', []) if str(item)} if isinstance(gu.get('member_edit_shots'), list) else set()
    result: list[str] = []
    for shot in payload.get('edit_shots', []) if isinstance(payload.get('edit_shots'), list) else []:
        if not isinstance(shot, dict) or str(shot.get('edit_shot_id') or '') not in member_ids:
            continue
        for call in shot.get('visual_asset_calls', []) if isinstance(shot.get('visual_asset_calls'), list) else []:
            if not isinstance(call, dict):
                continue
            asset_id = str(call.get('asset_id') or '').strip()
            if asset_id and asset_id not in result:
                result.append(asset_id)
    return result


def _validate_gu_asset_identity_anchors(payload: dict, records: dict[str, dict], voice_ids: set[str], errors: list[str]) -> None:
    for gu in payload.get('generation_units', []) if isinstance(payload.get('generation_units'), list) else []:
        if not isinstance(gu, dict):
            continue
        gu_id = str(gu.get('generation_unit_id') or 'UNKNOWN')
        active_media = {str(item) for item in gu.get('active_media_references', []) if str(item)} if isinstance(gu.get('active_media_references'), list) else set()
        sections = gu.get('prompt_sections') if isinstance(gu.get('prompt_sections'), dict) else {}
        raw_roles = sections.get('reference_roles')
        entries = _reference_role_strings(raw_roles)

        for asset_id in _member_visual_asset_ids(payload, gu):
            if asset_id in voice_ids:
                continue
            record = records.get(asset_id)
            if not isinstance(record, dict):
                continue  # Existing missing-asset validation owns this failure.
            matching = [entry for entry in entries if asset_id.lower() in entry.lower()]
            structured = _structured_reference_role_matches(raw_roles, asset_id)
            is_active_media = asset_id in active_media

            if is_active_media:
                structured_media = [str(item.get('media_ref') or '').strip() for item in structured]
                if not (
                    any(_MEDIA_REFERENCE_RE.search(entry) for entry in matching)
                    or any(_MEDIA_REFERENCE_RE.fullmatch(ref) for ref in structured_media if ref)
                ):
                    errors.append(
                        f'{gu_id}: REFERENCE_BINDING_FAILURE {asset_id} is active media but prompt_sections.reference_roles '
                        'does not bind it to an explicit @图片N responsibility'
                    )
                if structured and not any(_structured_anchor_is_specific(item, record) for item in structured):
                    errors.append(
                        f'{gu_id}: GU_ASSET_IDENTITY_ANCHOR {asset_id} structured reference role lacks specific inherited visual facts'
                    )
                continue

            # No real media is active for this asset: @图片N would be fabricated.
            if any(_MEDIA_REFERENCE_RE.search(entry) for entry in matching) or any(
                str(item.get('media_ref') or '').strip() for item in structured
            ):
                errors.append(
                    f'{gu_id}: FAKE_MEDIA_REFERENCE {asset_id} is not active media; final GU must use a text identity anchor, not @图片N'
                )
                continue

            structured_specific = any(_structured_anchor_is_specific(item, record) for item in structured)
            if not structured_specific and not any(_entry_has_specific_anchor(entry, asset_id, record) for entry in matching):
                errors.append(
                    f'{gu_id}: GU_ASSET_IDENTITY_ANCHOR {asset_id} is used by current Member SH but final GU lacks '
                    'a specific text identity anchor derived from the current asset record'
                )



_INTERNAL_ANALYSIS_MARKERS = (
    'EMOTION STORY FORGE',
    'Audience Halo',
    'AUDIENCE HALO',
    'CHARACTER + AUDIENCE EMOTION FIELD',
    'AUDIENCE_EMOTION_MAP',
    'forge_locked_audit',
    'AFD MASTER ORCHESTRATOR',
    'Forge AUDIT',
)


def _validate_analysis_artifact_isolation(root: Path, unit_id: str, payload: dict | None, errors: list[str]) -> None:
    if not isinstance(payload, dict):
        return
    screenplay_path = root / 'screenplay' / f'{unit_id}_LOCKED_SCREENPLAY.md'
    screenplay = screenplay_path.read_text(encoding='utf-8') if screenplay_path.is_file() else ''
    storyboard_text = json.dumps(payload, ensure_ascii=False)
    for marker in _INTERNAL_ANALYSIS_MARKERS:
        if marker in storyboard_text and marker not in screenplay:
            errors.append(
                f'ANALYSIS_ARTIFACT_LEAK：{unit_id} 分镜/Prompt包含内部分析标记 {marker!r}，但锁定剧本无该内容证据'
            )


def _validate_storyboard_authority(root: Path, unit_id: str, records: dict[str, dict], voice_ids: set[str], errors: list[str]) -> dict | None:
    json_path = root / 'storyboard' / f'{unit_id}_STORYBOARD.json'
    md_path = root / 'storyboard' / f'{unit_id}_STORYBOARD.md'
    payload = _load_object(json_path)
    if payload is None:
        errors.append(f'{unit_id} 缺少或无法解析结构化SH/GU/PH：storyboard/{unit_id}_STORYBOARD.json')
        return None
    sb_errors = validate_storyboard_payload(payload)
    errors.extend(f'{unit_id} Storyboard：{item}' for item in sb_errors)
    _validate_gu_voice_binding(payload, records, voice_ids, errors)
    _validate_gu_asset_identity_anchors(payload, records, voice_ids, errors)
    if not sb_errors:
        expected = render_storyboard(payload)
        if not md_path.is_file():
            errors.append(f'{unit_id} 缺少Renderer生成的正式分镜Markdown')
        elif md_path.read_text(encoding='utf-8') != expected:
            errors.append(f'{unit_id} STORYBOARD.md 不是结构化JSON的Renderer固定输出')

    for shot in payload.get('edit_shots', []) if isinstance(payload.get('edit_shots'), list) else []:
        if not isinstance(shot, dict):
            continue
        shot_id = str(shot.get('edit_shot_id', 'UNKNOWN'))
        for call in shot.get('visual_asset_calls', []) if isinstance(shot.get('visual_asset_calls'), list) else []:
            if not isinstance(call, dict):
                continue
            asset_id = str(call.get('asset_id', ''))
            if asset_id in voice_ids:
                errors.append(f'{shot_id} 视觉资产调用包含V-series：{asset_id}')
            elif asset_id and asset_id not in records:
                errors.append(f'{shot_id} 引用了不存在的资产：{asset_id}')

    for gu in payload.get('generation_units', []) if isinstance(payload.get('generation_units'), list) else []:
        if not isinstance(gu, dict):
            continue
        gu_id = str(gu.get('generation_unit_id', 'UNKNOWN'))
        for asset_id in gu.get('active_media_references', []) if isinstance(gu.get('active_media_references'), list) else []:
            asset_id = str(asset_id)
            if asset_id in voice_ids:
                errors.append(f'{gu_id} active_media_references 不得包含V-series：{asset_id}')
                continue
            record = records.get(asset_id)
            if record is None:
                errors.append(f'{gu_id} active_media_references 引用不存在资产：{asset_id}')
                continue
            if str(record.get('image_status', '')) != 'GENERATED':
                errors.append(f'{gu_id} active_media_references 的 {asset_id} 必须为GENERATED，当前={record.get("image_status")}')
                continue
            if _existing_media_path(root, record.get('image_file')) is None:
                errors.append(f'{gu_id} active_media_references 的 {asset_id} 缺少真实GENERATED文件：{record.get("image_file")}')
        for voice_id in gu.get('voice_text_assets', []) if isinstance(gu.get('voice_text_assets'), list) else []:
            voice_id = str(voice_id)
            if voice_id not in voice_ids:
                errors.append(f'{gu_id} voice_text_assets 引用的不是现有V-series：{voice_id}')
    return payload





def _validate_storyboard_against_packet(storyboard: dict, packet: dict, story_authority: dict, errors: list[str]) -> None:
    expected_scenes = list(packet.get('scene_scope') or [])
    expected_scene_set = set(expected_scenes)
    actual_scenes = {str(shot.get('scene_id') or '') for shot in storyboard.get('edit_shots', []) if isinstance(shot, dict) and str(shot.get('scene_id') or '').strip()}
    if actual_scenes != expected_scene_set:
        errors.append(
            'UNIT_STORYBOARD_SCENE_SCOPE_INCOMPLETE: '
            f'missing={sorted(expected_scene_set-actual_scenes)} extra={sorted(actual_scenes-expected_scene_set)}'
        )
    expected_atoms = set(str(x) for x in (packet.get('expected_story_atom_ids') or []) if str(x))
    atom_scene = {str(a.get('atom_id')): str(a.get('scene_id')) for a in story_authority.get('atoms', []) if isinstance(a, dict)}
    actual_atoms: set[str] = set()
    for shot in storyboard.get('edit_shots', []) if isinstance(storyboard.get('edit_shots'), list) else []:
        if not isinstance(shot, dict):
            continue
        scene_id = str(shot.get('scene_id') or '')
        coverage = shot.get('coverage') if isinstance(shot.get('coverage'), dict) else {}
        for atom_id in coverage.get('story_atom_ids', []) if isinstance(coverage.get('story_atom_ids'), list) else []:
            atom_id = str(atom_id)
            actual_atoms.add(atom_id)
            if atom_id in atom_scene and atom_scene[atom_id] != scene_id:
                errors.append(
                    f'UNIT_STORYBOARD_STORY_ATOM_SCENE_MISMATCH: {atom_id} expected={atom_scene[atom_id]} actual={scene_id}'
                )
    if actual_atoms != expected_atoms:
        errors.append(
            'UNIT_STORYBOARD_STORY_ATOM_SCOPE_INCOMPLETE: '
            f'missing={sorted(expected_atoms-actual_atoms)} extra={sorted(actual_atoms-expected_atoms)}'
        )

def _has_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_scene_intelligence_payload(data: dict | None, label: str, errors: list[str], expected_scene: str | None = None) -> None:
    result = data.get('SCENE_INTELLIGENCE_RESULT') if isinstance(data, dict) else None
    if not isinstance(result, dict):
        errors.append(f'{label} Scene Intelligence 缺少 SCENE_INTELLIGENCE_RESULT 对象')
        return
    if not _has_text(result.get('scene_id')):
        errors.append(f'{label} Scene Intelligence.scene_id 缺失')
    elif expected_scene and str(result.get('scene_id')) != expected_scene:
        errors.append(f'{label} Scene Intelligence.scene_id={result.get("scene_id")} 与分镜场景 {expected_scene} 不一致')
    if not _has_text(result.get('scene_core')):
        errors.append(f'{label} Scene Intelligence.scene_core 缺失')
    dramatic = result.get('dramatic_function')
    if not isinstance(dramatic, dict) or not _has_text(dramatic.get('primary')):
        errors.append(f'{label} Scene Intelligence.dramatic_function.primary 缺失')
    if not isinstance(result.get('beat_map'), list) or not result.get('beat_map'):
        errors.append(f'{label} Scene Intelligence.beat_map 必须为非空列表')
    if not isinstance(result.get('confidence_overall'), (int, float)):
        errors.append(f'{label} Scene Intelligence.confidence_overall 缺失')


def _validate_router_payload(data: dict | None, label: str, errors: list[str], expected_scene: str | None = None) -> None:
    result = data.get('ROUTER_RESULT') if isinstance(data, dict) else None
    if not isinstance(result, dict):
        errors.append(f'{label} Capability Router 缺少 ROUTER_RESULT 对象')
        return
    if not _has_text(result.get('scene_id')):
        errors.append(f'{label} Capability Router.scene_id 缺失')
    elif expected_scene and str(result.get('scene_id')) != expected_scene:
        errors.append(f'{label} Capability Router.scene_id={result.get("scene_id")} 与分镜场景 {expected_scene} 不一致')
    strategy = result.get('scene_strategy')
    if not isinstance(strategy, dict):
        errors.append(f'{label} Capability Router.scene_strategy 缺失')
    else:
        for key in ('dominant_need', 'routing_density', 'rationale'):
            if not _has_text(strategy.get(key)):
                errors.append(f'{label} Capability Router.scene_strategy.{key} 缺失')
    for key in ('active_capabilities', 'suppressed_capabilities'):
        if not isinstance(result.get(key), list):
            errors.append(f'{label} Capability Router.{key} 必须为列表')
    if not isinstance(result.get('downstream'), dict):
        errors.append(f'{label} Capability Router.downstream 缺失')
    if not isinstance(result.get('routing_confidence'), (int, float)):
        errors.append(f'{label} Capability Router.routing_confidence 缺失')


def _validate_director_craft_payload(data: dict | None, label: str, errors: list[str], expected_scene: str | None = None) -> None:
    result = data.get('DIRECTOR_CRAFT_RESULT') if isinstance(data, dict) else None
    if not isinstance(result, dict):
        errors.append(f'{label} Director Craft 缺少 DIRECTOR_CRAFT_RESULT 对象')
        return
    if not _has_text(result.get('scene_id')):
        errors.append(f'{label} Director Craft.scene_id 缺失')
    elif expected_scene and str(result.get('scene_id')) != expected_scene:
        errors.append(f'{label} Director Craft.scene_id={result.get("scene_id")} 与分镜场景 {expected_scene} 不一致')
    goal = result.get('scene_expression_goal')
    if not isinstance(goal, dict) or not _has_text(goal.get('dominant_read')):
        errors.append(f'{label} Director Craft.scene_expression_goal.dominant_read 缺失')
    beats = result.get('beat_expressions')
    if not isinstance(beats, list) or not beats:
        errors.append(f'{label} Director Craft.beat_expressions 必须为非空列表')
    else:
        for i, beat in enumerate(beats):
            if not isinstance(beat, dict):
                errors.append(f'{label} Director Craft.beat_expressions[{i}] 必须为对象')
                continue
            if not _has_text(beat.get('beat_id')):
                errors.append(f'{label} Director Craft.beat_expressions[{i}].beat_id 缺失')
            if not _has_text(beat.get('dramatic_action')):
                errors.append(f'{label} Director Craft.beat_expressions[{i}].dramatic_action 缺失')
            if not isinstance(beat.get('visible_carriers'), list) or not beat.get('visible_carriers'):
                errors.append(f'{label} Director Craft.beat_expressions[{i}].visible_carriers 必须为非空列表')
    handoff = result.get('handoff_to_shot_design')
    if not isinstance(handoff, dict) or not isinstance(handoff.get('must_be_readable'), list):
        errors.append(f'{label} Director Craft.handoff_to_shot_design.must_be_readable 缺失')
    if not isinstance(result.get('confidence'), (int, float)):
        errors.append(f'{label} Director Craft.confidence 缺失')

def _normalized_script_line(raw: str) -> str:
    line = ' '.join(raw.strip().split())
    if not line or line == '---':
        return ''
    if line.startswith('#'):
        return line.lstrip('#').strip()
    return line


def _locked_screenplay_required_lines(text: str) -> list[str]:
    lines = text.splitlines()

    # Preferred current contract: only the content under each "### 正式剧本正文"
    # is inherited verbatim. Scene-task/result metadata stays upstream and does
    # not have to be duplicated in the director document.
    body_lines: list[str] = []
    in_body = False
    found_body_marker = False
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith('#'):
            heading = stripped.lstrip('#').strip()
            if heading == '正式剧本正文':
                found_body_marker = True
                in_body = True
                continue
            if in_body:
                in_body = False
        if in_body:
            normalized = _normalized_script_line(raw)
            if normalized:
                body_lines.append(normalized)
    if found_body_marker:
        return body_lines

    # Backward-compatible fallback for older/simple locked screenplay files:
    # preserve substantive non-heading lines, but do not force director files
    # to duplicate markdown titles or scene headings.
    required: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped == '---' or stripped.startswith('#'):
            continue
        normalized = _normalized_script_line(raw)
        if normalized:
            required.append(normalized)
    return required


def _validate_director_screenplay_inheritance(
    screenplay_path: Path, director_path: Path, unit_id: str, errors: list[str]
) -> None:
    if not screenplay_path.is_file() or not director_path.is_file():
        return
    screenplay_text = screenplay_path.read_text(encoding='utf-8', errors='ignore')
    director_text = director_path.read_text(encoding='utf-8', errors='ignore')
    required = _locked_screenplay_required_lines(screenplay_text)
    if not required:
        return
    director_lines = [
        normalized
        for raw in director_text.splitlines()
        if (normalized := _normalized_script_line(raw))
    ]

    cursor = 0
    missing: list[str] = []
    for source_line in required:
        for i in range(cursor, len(director_lines)):
            if director_lines[i] == source_line:
                cursor = i + 1
                break
        else:
            missing.append(source_line)
            if len(missing) >= 3:
                break

    if missing:
        sample = ' / '.join(missing)
        errors.append(
            f'{unit_id} 整合导演剧本未完整继承正式编剧剧本正文；缺失或顺序改变：{sample}'
        )



_SCENE_ID_RE = re.compile(r'(?i)\b(SC\s*0*\d+|SCENE\s*0*\d+)\b|第[一二三四五六七八九十百0-9]+场')


def _scene_key(line: str) -> str | None:
    match = _SCENE_ID_RE.search(line)
    if not match:
        return None
    raw = match.group(0).upper().replace(' ', '')
    if raw.startswith('SCENE'):
        raw = 'SC' + raw[5:]
    return raw


def _scope_source_to_unit(text: str, unit_id: str) -> str:
    """Use an explicit unit heading when present; otherwise keep the full source.

    This avoids forcing a multi-episode source through one episode's validator while
    preserving the simple full-film screenplay case where there is no unit heading.
    """
    lines = text.splitlines()
    target = unit_id.strip().upper()
    heading_hits: list[tuple[int, int, str]] = []
    for i, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped.startswith('#'):
            continue
        level = len(stripped) - len(stripped.lstrip('#'))
        title = stripped.lstrip('#').strip()
        heading_hits.append((i, level, title))
    for pos, (start, level, title) in enumerate(heading_hits):
        if target and target in title.upper():
            end = len(lines)
            for next_start, next_level, _ in heading_hits[pos + 1:]:
                if next_level <= level:
                    end = next_start
                    break
            return '\n'.join(lines[start:end])
    return text


def _source_scene_bodies(text: str) -> dict[str, list[str]]:
    scenes: dict[str, list[str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        key = _scene_key(raw) if raw.strip().startswith('#') else None
        if key:
            current = key
            scenes.setdefault(current, [])
            continue
        if current is None:
            continue
        stripped = raw.strip()
        if not stripped or stripped == '---' or stripped.startswith('#'):
            continue
        normalized = _normalized_script_line(raw)
        if normalized:
            scenes[current].append(normalized)
    return scenes


def _locked_scene_bodies(text: str) -> dict[str, list[str]]:
    scenes: dict[str, list[str]] = {}
    current: str | None = None
    in_body = False
    scene_has_body_marker: dict[str, bool] = {}
    fallback_lines: dict[str, list[str]] = {}
    for raw in text.splitlines():
        stripped = raw.strip()
        key = _scene_key(raw) if stripped.startswith('#') else None
        if key:
            current = key
            scenes.setdefault(current, [])
            fallback_lines.setdefault(current, [])
            scene_has_body_marker.setdefault(current, False)
            in_body = False
            continue
        if current is None:
            continue
        if stripped.startswith('#'):
            heading = stripped.lstrip('#').strip()
            if heading == '正式剧本正文':
                scene_has_body_marker[current] = True
                in_body = True
            elif in_body:
                in_body = False
            continue
        if not stripped or stripped == '---':
            continue
        normalized = _normalized_script_line(raw)
        if not normalized:
            continue
        fallback_lines[current].append(normalized)
        if in_body:
            scenes[current].append(normalized)
    for scene_id, has_marker in scene_has_body_marker.items():
        if not has_marker:
            scenes[scene_id] = fallback_lines.get(scene_id, [])
    return scenes


def _authorized_review_section(path: Path) -> str:
    if not path.is_file():
        return ''
    lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
    collecting = False
    start_level = 0
    out: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith('#'):
            level = len(stripped) - len(stripped.lstrip('#'))
            title = stripped.lstrip('#').strip()
            if '已经合法处理的修改' in title:
                collecting = True
                start_level = level
                continue
            if collecting and level <= start_level:
                break
        if collecting:
            out.append(raw)
    return '\n'.join(out)


def _is_subsequence(required: list[str], actual: list[str]) -> bool:
    cursor = 0
    for line in required:
        for i in range(cursor, len(actual)):
            if actual[i] == line:
                cursor = i + 1
                break
        else:
            return False
    return True


def _scene_change_explicitly_authorized(scene_id: str, source_lines: list[str], review_text: str) -> bool:
    if not review_text or scene_id not in review_text.upper().replace(' ', ''):
        return False
    # A scene-level authorization is accepted only when it quotes at least one
    # substantive source line. Generic phrases such as "优化节奏" are not enough.
    return any(len(line) >= 2 and line in review_text for line in source_lines)


def _validate_mature_screenplay_source_lock(root: Path, unit_id: str, errors: list[str]) -> None:
    state = _load_object(root / 'state' / 'pipeline_state.json')
    if not isinstance(state, dict) or state.get('source_maturity') != 'screenplay':
        return
    source_path = root / 'source' / 'normalized_input.md'
    locked_path = root / 'screenplay' / f'{unit_id}_LOCKED_SCREENPLAY.md'
    if not source_path.is_file() or not locked_path.is_file():
        return

    source_text = _scope_source_to_unit(source_path.read_text(encoding='utf-8', errors='ignore'), unit_id)
    source_scenes = _source_scene_bodies(source_text)
    locked_scenes = _locked_scene_bodies(locked_path.read_text(encoding='utf-8', errors='ignore'))
    if not source_scenes or not locked_scenes:
        return
    review_text = _authorized_review_section(root / 'SCRIPT_REVIEW.md')

    for scene_id, source_lines in source_scenes.items():
        if scene_id not in locked_scenes:
            continue
        if _is_subsequence(source_lines, locked_scenes[scene_id]):
            continue
        if _scene_change_explicitly_authorized(scene_id, source_lines, review_text):
            continue
        errors.append(
            f'{unit_id}/{scene_id} 成熟剧本原文动作/对白缺失、改写或顺序改变，且未在SCRIPT_REVIEW.md“已经合法处理的修改”中明确授权并引用受影响原文'
        )


def _require_nonempty(path: Path, label: str, errors: list[str]) -> None:
    if not path.is_file() or not path.read_text(encoding='utf-8', errors='ignore').strip():
        errors.append(f'缺少或为空：{label} ({path})')


def _scene_ids_from_storyboard(payload: dict | None) -> list[str]:
    if not isinstance(payload, dict):
        return []
    out: list[str] = []
    for shot in payload.get('edit_shots', []) if isinstance(payload.get('edit_shots'), list) else []:
        if not isinstance(shot, dict):
            continue
        scene_id = str(shot.get('scene_id') or '').strip()
        if scene_id and scene_id not in out:
            out.append(scene_id)
    return out


SPATIAL_CAPABILITIES = {
    'SPATIAL_TOPOLOGY', 'ROUTE_PLANNING', 'VISIBILITY_RELATION', 'OCCLUSION_CHOREOGRAPHY',
    'LANDMARK_MEMORY', 'THREAT_GEOGRAPHY', 'REVEAL_STAGING', 'FORESHADOW_PAYOFF', 'MOTIF_PROGRESSION',
}


def _state_result_path(root: Path, subdir: str, unit_id: str, scene_id: str, suffix: str, *, single_scene: bool) -> Path:
    per_scene = root / 'state' / subdir / f'{unit_id}_{scene_id}_{suffix}.json'
    if per_scene.is_file():
        return per_scene
    legacy = root / 'state' / subdir / f'{unit_id}_{suffix}.json'
    if single_scene and legacy.is_file():
        return legacy
    return per_scene


def _router_requires_spatial(data: dict | None) -> bool:
    result = data.get('ROUTER_RESULT') if isinstance(data, dict) else None
    if not isinstance(result, dict):
        return False
    active = result.get('active_capabilities') if isinstance(result.get('active_capabilities'), list) else []
    for item in active:
        if isinstance(item, str) and item in SPATIAL_CAPABILITIES:
            return True
        if isinstance(item, dict) and str(item.get('capability') or item.get('id') or '') in SPATIAL_CAPABILITIES:
            return True
    downstream = result.get('downstream') if isinstance(result.get('downstream'), dict) else {}
    routed = downstream.get('spatial_narrative_engine')
    return isinstance(routed, list) and bool(routed)


def _router_has_spatial_topology(data: dict | None) -> bool:
    result = data.get('ROUTER_RESULT') if isinstance(data, dict) else None
    if not isinstance(result, dict):
        return False
    active = result.get('active_capabilities') if isinstance(result.get('active_capabilities'), list) else []
    for item in active:
        if isinstance(item, str) and item == 'SPATIAL_TOPOLOGY':
            return True
        if isinstance(item, dict) and str(item.get('capability') or item.get('id') or '') == 'SPATIAL_TOPOLOGY':
            return True
    return False


def _validate_pipeline_writeback(root: Path, unit_id: str | None, errors: list[str], storyboard_payload: dict | None = None, asset_records: dict[str, dict] | None = None, expected_scene_ids: list[str] | None = None) -> None:
    state = _load_object(root / 'state' / 'pipeline_state.json')
    if state is None:
        errors.append('缺少或无法解析 state/pipeline_state.json')
        return
    required_flags = ('confirmed_brief', 'story_authority_ready', 'asset_library_ready')
    for flag in required_flags:
        if state.get(flag) is not True:
            errors.append(f'pipeline_state.{flag} 必须为 true')

    if state.get('story_authority_ready') is True:
        _require_nonempty(root / 'state' / 'story_authority.json', 'Story Authority', errors)
        _require_nonempty(root / 'state' / 'information_ledger.json', 'Information Ledger', errors)
    _require_nonempty(root / 'state' / 'audience_emotion_architecture.json', '观众情绪架构机器状态', errors)

    if not unit_id:
        return
    for flag in ('scene_intelligence_ready', 'director_craft_ready'):
        if state.get(flag) is not True:
            errors.append(f'pipeline_state.{flag} 必须为 true')

    scene_ids = list(expected_scene_ids or _scene_ids_from_storyboard(storyboard_payload))
    if not scene_ids:
        errors.append(f'{unit_id} 分镜没有可追溯的scene_id')
        return
    single_scene = len(scene_ids) == 1
    for scene_id in scene_ids:
        label = f'{unit_id}/{scene_id}'
        causal_path = root / 'state' / 'audience_causal' / f'{unit_id}_{scene_id}.json'
        _require_nonempty(causal_path, f'{label} 观众情绪因果', errors)

        scene_path = _state_result_path(root, 'scene_intelligence', unit_id, scene_id, 'scene_intelligence', single_scene=single_scene)
        router_path = _state_result_path(root, 'router', unit_id, scene_id, 'router_result', single_scene=single_scene)
        craft_path = _state_result_path(root, 'director_craft', unit_id, scene_id, 'director_craft', single_scene=single_scene)
        scene_data = _load_object(scene_path)
        router_data = _load_object(router_path)
        craft_data = _load_object(craft_path)
        _validate_scene_intelligence_payload(scene_data, label, errors, expected_scene=scene_id)
        _validate_router_payload(router_data, label, errors, expected_scene=scene_id)
        _validate_director_craft_payload(craft_data, label, errors, expected_scene=scene_id)

        if _router_requires_spatial(router_data):
            spatial_path = _state_result_path(root, 'spatial_narrative', unit_id, scene_id, 'spatial_narrative', single_scene=single_scene)
            spatial_data = _load_object(spatial_path)
            result = spatial_data.get('SPATIAL_NARRATIVE_RESULT') if isinstance(spatial_data, dict) else None
            if not isinstance(result, dict):
                errors.append(f'{label} Router已启用空间叙事能力，但缺少 Spatial Narrative 结果')
            else:
                activation_state = str(result.get('activation_state') or '')
                if activation_state not in {'ACTIVE', 'SUPPRESSED'}:
                    errors.append(
                        f'{label} SPATIAL_ACTIVATION_STATE_INVALID activation_state必须为ACTIVE或SUPPRESSED'
                    )
                if str(result.get('scene_id') or '') not in {'', scene_id}:
                    errors.append(f'{label} Spatial Narrative.scene_id={result.get("scene_id")} 与当前场景不一致')
            if isinstance(result, dict) and isinstance(storyboard_payload, dict):
                scene_shots = [
                    shot for shot in storyboard_payload.get('edit_shots', [])
                    if isinstance(shot, dict) and str(shot.get('scene_id') or '') == scene_id
                ]
                for item in validate_scene_geo_contract(
                    scene_id, result, scene_shots, asset_records or {},
                    require_topology=_router_has_spatial_topology(router_data),
                ):
                    errors.append(f'{label} {item}')

def _validate_ledger(root: Path, brief: dict, errors: list[str]) -> None:
    path = root / 'PRODUCTION_LEDGER.json'
    if not path.is_file():
        if brief.get('work_format') in FILM_FORMATS | SERIES_FORMATS:
            errors.append('缺少生产覆盖账本：PRODUCTION_LEDGER.json')
        return
    ledger = _load_object(path)
    if ledger is None:
        errors.append('PRODUCTION_LEDGER.json 无法解析')
        return
    work_format = brief.get('work_format')
    if work_format in FILM_FORMATS:
        target = brief.get('target_total_runtime_seconds')
        if ledger.get('scope_type') != 'film_timeline':
            errors.append('Production Ledger scope_type 与电影项目不一致')
        if isinstance(target, (int, float)) and abs(float(ledger.get('target_runtime_seconds', -1)) - float(target)) > EPSILON:
            errors.append('Production Ledger电影目标时长与Project Brief不一致')
    elif work_format in SERIES_FORMATS:
        if ledger.get('scope_type') != 'episodes':
            errors.append('Production Ledger scope_type 与剧集项目不一致')
        if ledger.get('target_episode_count') != brief.get('episode_count'):
            errors.append('Production Ledger目标集数与Project Brief不一致')


def validate_project_consistency(project_root: str | Path, unit_id: str | None = None) -> list[str]:
    root = Path(project_root).resolve()
    if not root.is_dir():
        return [f'项目目录不存在：{root}']
    errors: list[str] = []
    brief = _load_object(root / 'state' / 'project_brief.json')
    if brief is None:
        errors.append('缺少或无法解析 state/project_brief.json')
        brief = {}

    _validate_emotion_authority(root, errors)
    require_project_baseline = bool(unit_id and (root / 'state' / 'PROJECT_SCOPE.json').is_file() and str(unit_id).startswith('PU'))
    records, voice_ids = _validate_asset_authority(root, errors, require_project_baseline=require_project_baseline)
    _validate_ledger(root, brief, errors)

    storyboard_payload: dict | None = None
    expected_scene_ids: list[str] | None = None
    packet: dict | None = None
    if unit_id:
        scope_path = root / 'state' / 'PROJECT_SCOPE.json'
        if scope_path.is_file() and str(unit_id).startswith('PU'):
            from production_unit_packet import validate_unit_packet
            packet_path = root / 'state' / 'units' / f'{unit_id}_PACKET.json'
            packet = _load_object(packet_path)
            if packet is None:
                errors.append(f'{unit_id} 缺少或无法解析 Production Unit Packet：state/units/{unit_id}_PACKET.json')
            else:
                packet_errors = validate_unit_packet(root, packet, unit_id)
                errors.extend(f'{unit_id} Unit Packet：{item}' for item in packet_errors)
                expected_scene_ids = list(packet.get('scene_scope') or [])
        screenplay_path = root / 'screenplay' / f'{unit_id}_LOCKED_SCREENPLAY.md'
        director_path = root / 'director' / f'{unit_id}_INTEGRATED_DIRECTOR_SCREENPLAY.md'
        _require_nonempty(screenplay_path, f'{unit_id} 正式编剧剧本', errors)
        _require_nonempty(director_path, f'{unit_id} 整合导演剧本', errors)
        _validate_mature_screenplay_source_lock(root, unit_id, errors)
        _validate_director_screenplay_inheritance(screenplay_path, director_path, unit_id, errors)
        storyboard_payload = _validate_storyboard_authority(root, unit_id, records, voice_ids, errors)
        if packet is not None and storyboard_payload is not None:
            story_authority = _load_object(root / 'state' / 'story_authority.json') or {}
            _validate_storyboard_against_packet(storyboard_payload, packet, story_authority, errors)
        _validate_analysis_artifact_isolation(root, unit_id, storyboard_payload, errors)

    _validate_pipeline_writeback(root, unit_id, errors, storyboard_payload, records, expected_scene_ids)
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description='Validate fused AFD + CineWeaver runtime consistency')
    parser.add_argument('--project-root', required=True)
    parser.add_argument('--unit-id')
    args = parser.parse_args()
    errors = validate_project_consistency(args.project_root, args.unit_id)
    if errors:
        print('FAIL')
        for error in errors:
            print('-', error)
        return 1
    print('PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
