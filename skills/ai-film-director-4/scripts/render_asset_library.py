#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VISUAL_GROUPS = {
    'character_assets': ('A / B 人物资产', ('A', 'B')),
    'location_assets': ('S 场景资产', ('S',)),
    'prop_assets': ('P 关键道具资产', ('P',)),
    'g_assets': ('G 生物 / 实体 / 群体资产', ('G',)),
}
VALID_STATUSES = {'GENERATED', 'PROMPT_ONLY', 'FAILED', 'MISSING'}
DISPLAY_STATUS = {'GENERATED': '已生成', 'PROMPT_ONLY': '待生成', 'FAILED': '生成失败', 'MISSING': '缺失', 'TEXT_ONLY': '仅文字'}
COMMON_ASSET_FIELDS = ('image_status', 'reference_media', 'use_scope', 'dependencies')
SCALE_REFERENCE_REQUIRED_FIELDS = (
    'reference_id', 'reference_role', 'subject_asset_ids', 'activation_reason', 'relative_scale',
    'image_prompt', 'image_status', 'inherits', 'excludes', 'use_scope', 'dependencies',
)

VOICE_PROFILE_FIELDS = (
    'perceived_age', 'gender_presentation', 'accent_or_regional_quality', 'register', 'timbre',
    'texture', 'resonance', 'pace', 'rhythm', 'volume_tendency', 'emotional_leakage',
    'pressure_behavior', 'prohibitions',
)


def _text(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (str, int, float)):
        return str(value)
    if isinstance(value, list):
        return '；'.join(_text(x) for x in value)
    if isinstance(value, dict):
        return '；'.join(f'{k}={_text(v)}' for k, v in value.items())
    return str(value)


def _nonempty(value: Any) -> bool:
    return bool(_text(value).strip())


def validate_asset_library_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict) or not isinstance(payload.get('ASSET_LIBRARY'), dict):
        return ['ASSET_LIBRARY must be an object']
    lib = payload['ASSET_LIBRARY']
    if 'scale_reference_assets' in lib:
        errors.append('scale_reference_assets parallel family is forbidden; nest supporting scale_reference under one existing visual master asset')
    contract_version = str(lib.get('contract_version') or '')
    if contract_version != '4.3':
        errors.append(f'contract_version must equal 4.3, got {contract_version or "<missing>"}')
    strict_v43 = True
    policy = lib.get('project_asset_policy')
    if not isinstance(policy, dict):
        errors.append('project_asset_policy missing')
    else:
        for key in ('world_and_visual_style', 'character_face_policy', 'image_prompt_policy', 'voice_asset_policy'):
            if not _nonempty(policy.get(key)):
                errors.append(f'project_asset_policy.{key} missing')

    seen: set[str] = set()
    master_visual_ids: set[str] = set()
    character_ids: set[str] = set()
    character_voice_links: list[tuple[str, str]] = []
    scale_reference_candidates: list[tuple[str, str, dict]] = []
    scale_reference_ids: set[str] = set()

    for group, (_, prefixes) in VISUAL_GROUPS.items():
        records = lib.get(group, [])
        if not isinstance(records, list):
            errors.append(f'{group} must be a list')
            continue
        for i, record in enumerate(records):
            prefix = f'{group}[{i}]'
            if not isinstance(record, dict):
                errors.append(f'{prefix} must be an object')
                continue
            asset_id = str(record.get('asset_id') or '')
            if not asset_id or not asset_id.startswith(prefixes):
                errors.append(f'{prefix}.asset_id invalid: {asset_id}')
            if asset_id in seen:
                errors.append(f'duplicate asset_id {asset_id}')
            elif asset_id:
                seen.add(asset_id)
                master_visual_ids.add(asset_id)
                if group == 'character_assets':
                    character_ids.add(asset_id)
            for key in ('name', 'image_prompt'):
                if not _nonempty(record.get(key)):
                    errors.append(f'{prefix}.{key} missing')
            if strict_v43:
                for key in COMMON_ASSET_FIELDS:
                    if key not in record:
                        errors.append(f'{prefix}.{key} missing')
                if 'reference_media' in record and not isinstance(record.get('reference_media'), list):
                    errors.append(f'{prefix}.reference_media must be a list')
                if 'use_scope' in record and (not isinstance(record.get('use_scope'), list) or not record.get('use_scope')):
                    errors.append(f'{prefix}.use_scope must be a non-empty list')
                if 'dependencies' in record and not isinstance(record.get('dependencies'), list):
                    errors.append(f'{prefix}.dependencies must be a list')
            status = record.get('image_status')
            if status is not None and str(status) not in VALID_STATUSES:
                errors.append(f'{prefix}.image_status invalid: {status}')
            if record.get('asset_class') == 'TEXT_VOICE_ASSET':
                errors.append(f'{prefix}: VOICE_MEDIA_LEAK visual group cannot contain TEXT_VOICE_ASSET')
            metadata = record.get('downstream_metadata')
            if isinstance(metadata, dict) and 'scale_reference' in metadata:
                scale_reference_candidates.append((prefix, asset_id, metadata.get('scale_reference')))
            voice_asset_id = str(record.get('voice_asset_id') or '')
            if group == 'character_assets' and voice_asset_id:
                character_voice_links.append((prefix, voice_asset_id))

    for prefix, owner_asset_id, scale in scale_reference_candidates:
        label = f'{prefix}.downstream_metadata.scale_reference'
        if not isinstance(scale, dict):
            errors.append(f'{label} must be an object')
            continue
        for key in SCALE_REFERENCE_REQUIRED_FIELDS:
            if key not in scale:
                errors.append(f'{label}.{key} missing')
        reference_id = str(scale.get('reference_id') or '')
        if not reference_id.startswith('SCALE-'):
            errors.append(f'{label}.reference_id invalid: {reference_id}')
        if reference_id:
            if reference_id in scale_reference_ids:
                errors.append(f'{label}.reference_id duplicate: {reference_id}')
            else:
                scale_reference_ids.add(reference_id)
        if scale.get('reference_role') != 'scale':
            errors.append(f'{label}.reference_role must be scale')
        subjects = scale.get('subject_asset_ids')
        if not isinstance(subjects, list) or len(subjects) < 2 or any(not isinstance(x, str) or not x.strip() for x in subjects):
            errors.append(f'{label}.subject_asset_ids must contain at least two non-empty asset IDs')
            subjects = []
        elif len(set(subjects)) != len(subjects):
            errors.append(f'{label}.subject_asset_ids must be unique')
        if subjects and owner_asset_id not in subjects:
            errors.append(f'{label} must include owner asset {owner_asset_id} in subject_asset_ids')
        for subject_id in subjects:
            if subject_id not in master_visual_ids:
                errors.append(f'{label}.subject_asset_ids references missing master asset: {subject_id}')
        for key in ('activation_reason', 'relative_scale', 'image_prompt'):
            if not _nonempty(scale.get(key)):
                errors.append(f'{label}.{key} missing')
        status = scale.get('image_status')
        if status is None or str(status) not in VALID_STATUSES:
            errors.append(f'{label}.image_status invalid: {status}')
        for key in ('inherits', 'excludes', 'use_scope', 'dependencies'):
            value = scale.get(key)
            if not isinstance(value, list) or not value:
                errors.append(f'{label}.{key} must be a non-empty list')
        dependencies = scale.get('dependencies')
        if isinstance(dependencies, list) and subjects and not set(subjects).issubset(set(str(x) for x in dependencies)):
            errors.append(f'{label}.dependencies must include every subject_asset_id')

    states = lib.get('persistent_states', [])
    if not isinstance(states, list):
        errors.append('persistent_states must be a list')
    else:
        for i, state in enumerate(states):
            prefix = f'persistent_states[{i}]'
            if not isinstance(state, dict):
                errors.append(f'{prefix} must be an object')
                continue
            metadata = state.get('downstream_metadata')
            if isinstance(metadata, dict) and 'scale_reference' in metadata:
                errors.append(f'{prefix}.downstream_metadata.scale_reference is only allowed on an existing visual master asset')
            sid = str(state.get('state_id') or '')
            parent = str(state.get('inherits_from') or '')
            if '-ST' not in sid:
                errors.append(f'{prefix}.state_id invalid: {sid}')
            if sid in seen:
                errors.append(f'duplicate asset_id {sid}')
            elif sid:
                seen.add(sid)
            for key in ('inherits_from', 'visible_change', 'image_prompt'):
                if not _nonempty(state.get(key)):
                    errors.append(f'{prefix}.{key} missing')
            if strict_v43:
                for key in COMMON_ASSET_FIELDS:
                    if key not in state:
                        errors.append(f'{prefix}.{key} missing')
                if 'reference_media' in state and not isinstance(state.get('reference_media'), list):
                    errors.append(f'{prefix}.reference_media must be a list')
                if 'use_scope' in state and (not isinstance(state.get('use_scope'), list) or not state.get('use_scope')):
                    errors.append(f'{prefix}.use_scope must be a non-empty list')
                if 'dependencies' in state and not isinstance(state.get('dependencies'), list):
                    errors.append(f'{prefix}.dependencies must be a list')
            status = state.get('image_status')
            if status is not None and str(status) not in VALID_STATUSES:
                errors.append(f'{prefix}.image_status invalid: {status}')
            if parent and parent not in master_visual_ids:
                errors.append(f'{prefix}.inherits_from missing master asset: {parent}')
            if parent and sid and not sid.startswith(parent + '-ST'):
                errors.append(f'{prefix}.state_id must inherit namespace from {parent}: {sid}')

    voices = lib.get('voice_assets', [])
    voice_ids: set[str] = set()
    if not isinstance(voices, list):
        errors.append('voice_assets must be a list')
    else:
        for i, voice in enumerate(voices):
            prefix = f'voice_assets[{i}]'
            if not isinstance(voice, dict):
                errors.append(f'{prefix} must be an object')
                continue
            metadata = voice.get('downstream_metadata')
            if isinstance(metadata, dict) and 'scale_reference' in metadata:
                errors.append(f'{prefix}.downstream_metadata.scale_reference is only allowed on an existing visual master asset')
            vid = str(voice.get('asset_id') or '')
            if not vid.startswith('V'):
                errors.append(f'{prefix}.asset_id invalid: {vid}')
            if vid in seen:
                errors.append(f'duplicate asset_id {vid}')
            elif vid:
                seen.add(vid)
                voice_ids.add(vid)
            if voice.get('media_asset') is not False:
                errors.append(f'{prefix}: VOICE_MEDIA_LEAK media_asset must be false')
            for file_key in ('image_file', 'audio_file', 'video_file'):
                if voice.get(file_key) not in (None, ''):
                    errors.append(f'{prefix}: VOICE_MEDIA_LEAK {file_key} must be null')
            if voice.get('visual_cost_units') != 0 or voice.get('seedance_reference_slot_cost') != 0:
                errors.append(f'{prefix}: VOICE_MEDIA_LEAK V-series must cost zero media slots')
            profile = voice.get('voice_profile')
            if not isinstance(profile, dict) or not profile:
                errors.append(f'{prefix}.voice_profile missing')
            elif strict_v43:
                for key in VOICE_PROFILE_FIELDS:
                    if not _nonempty(profile.get(key)):
                        errors.append(f'{prefix}.voice_profile.{key} missing')
            if strict_v43:
                if not isinstance(voice.get('use_scope'), list) or not voice.get('use_scope'):
                    errors.append(f'{prefix}.use_scope must be a non-empty list')
                if not isinstance(voice.get('dependencies'), list):
                    errors.append(f'{prefix}.dependencies must be a list')
            character_asset_id = str(voice.get('character_asset_id') or '')
            if character_asset_id and character_asset_id not in character_ids:
                errors.append(f'{prefix}.character_asset_id missing character asset: {character_asset_id}')

    for prefix, voice_asset_id in character_voice_links:
        if voice_asset_id not in voice_ids:
            errors.append(f'{prefix}.voice_asset_id missing V-series asset: {voice_asset_id}')
    return errors

def _render_dict(data: dict, skip: set[str] | None = None) -> list[str]:
    skip = skip or set()
    lines: list[str] = []
    for key, value in data.items():
        if key in skip:
            continue
        display_key = {
            'name': '标准名称', 'image_status': '状态', 'reference_media': 'Reference',
            'use_scope': '使用范围', 'dependencies': '依赖关系', 'voice_profile': '稳定声线',
        }.get(key, key)
        if key == 'image_status' and isinstance(value, str):
            value = DISPLAY_STATUS.get(value, value)
        if isinstance(value, dict):
            lines.append(f'- {display_key}：')
            for sub_key, sub_value in value.items():
                lines.append(f'  - {sub_key}：{_text(sub_value)}')
        else:
            lines.append(f'- {display_key}：{_text(value)}')
    return lines


def _index_rows(lib: dict) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for group in ('character_assets', 'location_assets', 'prop_assets', 'g_assets'):
        for record in lib.get(group, []) or []:
            rows.append((str(record.get('asset_id','')), str(record.get('name','')), group, str(record.get('image_file') or ''), DISPLAY_STATUS.get(str(record.get('image_status') or ''), str(record.get('image_status') or ''))))
    for state in lib.get('persistent_states', []) or []:
        rows.append((str(state.get('state_id','')), str(state.get('state_category') or '持续状态'), 'persistent_state', str(state.get('image_file') or ''), DISPLAY_STATUS.get(str(state.get('image_status') or ''), str(state.get('image_status') or ''))))
    for group in ('character_assets', 'location_assets', 'prop_assets', 'g_assets'):
        for record in lib.get(group, []) or []:
            metadata = record.get('downstream_metadata') if isinstance(record, dict) else None
            scale = metadata.get('scale_reference') if isinstance(metadata, dict) else None
            if isinstance(scale, dict):
                rows.append((
                    str(scale.get('reference_id') or ''),
                    '比例参考',
                    'supporting_scale_reference',
                    str(scale.get('image_file') or ''),
                    DISPLAY_STATUS.get(str(scale.get('image_status') or ''), str(scale.get('image_status') or '')),
                ))
    for voice in lib.get('voice_assets', []) or []:
        rows.append((str(voice.get('asset_id','')), str(voice.get('name','')), 'voice_text', '', DISPLAY_STATUS['TEXT_ONLY']))
    return sorted(rows, key=lambda row: row[0])


def render_asset_library(payload: dict) -> str:
    errors = validate_asset_library_payload(payload)
    if errors:
        raise ValueError('Asset library validation failed:\n- ' + '\n- '.join(errors))
    lib = payload['ASSET_LIBRARY']
    lines = ['# 资产总表与详细生成提示词', '']
    lines += ['## 项目资产策略', '']
    lines += _render_dict(lib.get('project_asset_policy', {})) + ['']
    lines += ['## 资产快速索引', '', '| 编号 | 名称 | 类型 | 图片文件 | 状态 |', '|---|---|---|---|---|']
    for row in _index_rows(lib):
        lines.append('| ' + ' | '.join(row) + ' |')
    lines.append('')

    lines += ['## A / B 人物资产', '']
    for record in lib.get('character_assets', []) or []:
        lines += [f"### {record['asset_id']}｜{record.get('name','')}", '']
        lines += _render_dict(record, {'image_prompt'})
        lines += ['', '**Canonical Prompt｜标准生成提示词**', '', str(record.get('image_prompt','')), '']

    lines += ['## V 系列声音资产', '']
    for voice in lib.get('voice_assets', []) or []:
        lines += [f"### {voice['asset_id']}｜{voice.get('name','')}", '']
        lines += _render_dict(voice) + ['']

    lines += ['## 持续状态资产', '']
    for state in lib.get('persistent_states', []) or []:
        lines += [f"### {state['state_id']}｜{state.get('state_category','持续状态')}", '']
        lines += _render_dict(state, {'image_prompt'})
        lines += ['', '**Canonical Prompt｜标准生成提示词**', '', str(state.get('image_prompt','')), '']

    for group, (title, _) in (
        ('location_assets', VISUAL_GROUPS['location_assets']),
        ('prop_assets', VISUAL_GROUPS['prop_assets']),
        ('g_assets', VISUAL_GROUPS['g_assets']),
    ):
        lines += [f'## {title}', '']
        for record in lib.get(group, []) or []:
            lines += [f"### {record['asset_id']}｜{record.get('name','')}", '']
            lines += _render_dict(record, {'image_prompt'})
            lines += ['', '**Canonical Prompt｜标准生成提示词**', '', str(record.get('image_prompt','')), '']

    return '\n'.join(lines).rstrip() + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate and render authoritative CineWeaver Asset Library JSON')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding='utf-8'))
    errors = validate_asset_library_payload(payload)
    if errors:
        print('FAIL')
        for error in errors:
            print('-', error)
        return 1
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_asset_library(payload), encoding='utf-8')
    print(out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
