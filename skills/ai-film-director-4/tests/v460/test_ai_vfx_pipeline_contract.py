import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def _load_preflight_module():
    spec = importlib.util.spec_from_file_location('afd_model_preflight_for_vfx', ROOT / 'scripts' / 'model_preflight.py')
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_vfx_policy_is_optional_execution_guidance_not_new_owner_or_api_layer() -> None:
    text = read('references/cineweaver/Shot_Segment_Engine_V1.3/runtime/AI_VFX_PIPELINE.md').lower()
    assert 'optional' in text
    assert '不是新的 owner' in text or 'not a new owner' in text or 'no new owner' in text
    assert 'prompt' in text and ('no api' in text or 'does not add api' in text or '不新增 api' in text)
    assert 'runtime' not in text or 'generation runtime' not in text


def test_vfx_policy_reuses_existing_face_lock_size_ref_and_reference_roles() -> None:
    text = read('references/cineweaver/Shot_Segment_Engine_V1.3/runtime/AI_VFX_PIPELINE.md').lower()
    assert 'face-lock' in text or 'headless' in text
    assert 'size-ref' in text
    assert 'reference role' in text or 'reference_roles' in text
    assert 'reuse' in text or '复用' in text or '不得重复' in text
    assert '不得建立第二套资产库' in text or 'do not create a second asset system' in text


def test_vfx_provenance_keeps_field_workflow_separate_from_platform_facts() -> None:
    text = read('references/cineweaver/Shot_Segment_Engine_V1.3/runtime/AI_VFX_PIPELINE.md').lower()
    assert 'field' in text
    assert 'platform' in text
    assert ('不等于新增 provider parameter' in text or '不等于新增 api parameter' in text or '不是平台参数' in text)


def test_seedance25_profile_routes_plate_transform_to_omni_reference_not_video_edit() -> None:
    text = read('references/cineweaver/Shot_Segment_Engine_V1.3/runtime/SEEDANCE_2_5_PROFILE.md').lower()
    assert 'plate transform' in text or 'plate-transform' in text or '素材替换' in text or '原片替换' in text
    assert 'omni_reference' in text
    assert 'video reference' in text or 'video_references' in text
    assert 'video_edit' in text
    assert 'duration' in text and 'source' in text


def test_vfx_compiler_preserves_plate_as_master_without_rewriting_unrelated_pixels() -> None:
    text = read('references/cineweaver/Shot_Segment_Engine_V1.3/runtime/VIDEO_PROMPT_COMPILER.md').lower()
    assert 'plate' in text or 'source video' in text or '源片' in text
    for token in ('camera', 'framing', 'motion', 'background', 'lighting'):
        assert token in text
    assert 'grain' in text or '颗粒' in text
    assert 'duration' in text
    assert 'preserve' in text or '保持' in text
    assert 'current_gu_only' in text


def test_vfx_failure_rule_is_field_heuristic_not_global_four_attempt_limit() -> None:
    text = read('references/cineweaver/Shot_Segment_Engine_V1.3/runtime/FAILURE_PREVENTION.md').lower()
    assert 'four' in text or '四' in text
    assert 'batch' in text or '批' in text
    assert 'field_heuristic' in text
    assert '不是 afd 全局固定尝试次数' in text or 'not a global fixed attempt limit' in text


def test_vfx_missing_motion_anchor_has_i2v_fallback_and_clean_cut_is_optional_not_global() -> None:
    text = read('references/cineweaver/Shot_Segment_Engine_V1.3/runtime/AI_VFX_PIPELINE.md').lower()
    assert 'anchor' in text or '锚' in text
    assert 'image-to-video' in text or 'i2v' in text
    assert 'empty' in text or '空帧' in text or '空画面' in text
    assert 'optional' in text or 'when useful' in text or '按需' in text


def test_location_asset_qa_adds_vfx_light_selection_without_fixed_batch_or_model_requirement() -> None:
    text = read('references/modules/asset-production/module.md').lower()
    assert 'vfx' in text and ('light' in text or '光线' in text)
    assert '不是 afd 的固定批次要求' in text or 'not a fixed batch requirement' in text
    assert '不要求必须使用 soul cinema' in text or 'does not require soul cinema' in text


def test_model_preflight_plate_transform_rejects_video_edit_route() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_5_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 'video_edit', 'resolution': '720p'},
            'media_roles': ['video_references'],
            'vfx_plate_transform': {'source_duration_seconds': 8},
        },
        profiles,
    )
    assert any(d['severity'] == 'FAIL' and d['code'] == 'VFX_ROUTE_CONFLICT' for d in diagnostics), diagnostics


def test_model_preflight_plate_transform_requires_duration_match() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_5_HIGGSFIELD',
        {
            'gu_duration_seconds': 10,
            'provider_params': {'mode': 'omni_reference', 'resolution': '720p'},
            'media_roles': ['video_references'],
            'vfx_plate_transform': {'source_duration_seconds': 8},
        },
        profiles,
    )
    assert any(d['severity'] == 'FAIL' and d['code'] == 'VFX_SOURCE_DURATION_MISMATCH' for d in diagnostics), diagnostics


def test_model_preflight_plate_transform_blocks_unprepared_source_below_model_floor() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_5_HIGGSFIELD',
        {
            'gu_duration_seconds': 4,
            'provider_params': {'mode': 'omni_reference', 'resolution': '720p'},
            'media_roles': ['video_references'],
            'vfx_plate_transform': {'source_duration_seconds': 2.5},
        },
        profiles,
    )
    assert any(d['severity'] == 'FAIL' and d['code'] == 'VFX_SOURCE_PREP_REQUIRED' for d in diagnostics), diagnostics


def test_model_preflight_valid_plate_transform_passes_vfx_checks() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_5_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 'omni_reference', 'resolution': '720p'},
            'media_roles': ['video_references', 'image_references'],
            'vfx_plate_transform': {'source_duration_seconds': 8},
        },
        profiles,
    )
    assert not any(d['severity'] == 'FAIL' and d['code'].startswith('VFX_') for d in diagnostics), diagnostics


def test_ordinary_omni_reference_without_vfx_context_remains_unchanged() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_5_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 'omni_reference', 'resolution': '720p'},
            'media_roles': ['video_references'],
        },
        profiles,
    )
    assert not any(d['code'].startswith('VFX_') for d in diagnostics), diagnostics


def test_model_preflight_plate_transform_rejects_malformed_context() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_5_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 'omni_reference', 'resolution': '720p'},
            'media_roles': ['video_references'],
            'vfx_plate_transform': 'yes',
        },
        profiles,
    )
    assert any(d['severity'] == 'FAIL' and d['code'] == 'VFX_CONTEXT_TYPE' for d in diagnostics), diagnostics


def test_model_preflight_plate_transform_requires_source_duration() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_5_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 'omni_reference', 'resolution': '720p'},
            'media_roles': ['video_references'],
            'vfx_plate_transform': {},
        },
        profiles,
    )
    assert any(d['severity'] == 'FAIL' and d['code'] == 'VFX_SOURCE_DURATION_REQUIRED' for d in diagnostics), diagnostics


def test_model_preflight_plate_transform_requires_gu_duration_so_match_cannot_be_skipped() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_5_HIGGSFIELD',
        {
            'provider_params': {'mode': 'omni_reference', 'resolution': '720p'},
            'media_roles': ['video_references'],
            'vfx_plate_transform': {'source_duration_seconds': 8},
        },
        profiles,
    )
    assert any(d['severity'] == 'FAIL' and d['code'] == 'VFX_GU_DURATION_REQUIRED' for d in diagnostics), diagnostics


def test_model_preflight_plate_transform_requires_actual_video_master_role() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_5_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 'omni_reference', 'resolution': '720p'},
            'media_roles': ['image_references'],
            'vfx_plate_transform': {'source_duration_seconds': 8},
        },
        profiles,
    )
    assert any(d['severity'] == 'FAIL' and d['code'] == 'VFX_VIDEO_MASTER_REQUIRED' for d in diagnostics), diagnostics


def test_seedance20_vfx_lane_is_supported_without_inheriting_seedance25_duration_floor_contract() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_0_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 'std', 'resolution': '4k'},
            'media_roles': ['video_references'],
            'vfx_plate_transform': {'source_duration_seconds': 8},
        },
        profiles,
    )
    assert not any(d['code'] == 'VFX_PROFILE_UNVERIFIED' for d in diagnostics), diagnostics
    assert not any(d['severity'] == 'FAIL' and d['code'].startswith('VFX_') for d in diagnostics), diagnostics


def test_final_prompt_qc_requires_vfx_context_and_source_master_semantic_check_when_workflow_is_active() -> None:
    text = read('references/cineweaver/Final_QC_Engine_V1.3/runtime/PROMPT_QC.md').lower()
    assert 'vfx_plate_transform' in text
    assert 'source master' in text or 'source-master' in text
    assert 'preserve' in text
    assert 'omni_reference' in text
    assert 'video_edit' in text
    assert 'current_gu_only' in text


def test_vfx_policy_contains_distinct_seedance20_and_seedance25_lanes() -> None:
    text = read('references/cineweaver/Shot_Segment_Engine_V1.3/runtime/AI_VFX_PIPELINE.md').lower()
    assert 'seedance 2.0' in text and 'seedance 2.5' in text
    assert 'preservation-vfx' in text or 'preservation vfx' in text
    assert 'omni_reference' in text
    assert 'std' in text
    assert '4k' in text
    assert '不同' in text or 'distinct' in text


def test_seedance20_profile_documents_vfx_source_plate_std_and_4k_quality_boundary() -> None:
    text = read('references/cineweaver/Shot_Segment_Engine_V1.3/runtime/SEEDANCE_2_0_PROFILE.md').lower()
    assert 'vfx' in text
    assert 'source' in text or '源片' in text
    assert 'std' in text
    assert '4k' in text
    assert 'field' in text or 'practitioner' in text
    assert 'not' in text or '不是' in text


def test_model_preflight_seedance20_vfx_requires_std_lane() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_0_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 'fast', 'resolution': '720p'},
            'media_roles': ['video_references'],
            'vfx_plate_transform': {'source_duration_seconds': 8},
        },
        profiles,
    )
    assert any(d['severity'] == 'FAIL' and d['code'] == 'VFX_SD20_ROUTE_CONFLICT' for d in diagnostics), diagnostics


def test_model_preflight_seedance20_vfx_requires_video_reference_master() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_0_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 'std', 'resolution': '4k'},
            'media_roles': ['image_references'],
            'vfx_plate_transform': {'source_duration_seconds': 8},
        },
        profiles,
    )
    assert any(d['severity'] == 'FAIL' and d['code'] == 'VFX_VIDEO_MASTER_REQUIRED' for d in diagnostics), diagnostics


def test_model_preflight_seedance20_non4k_vfx_is_quality_warning_not_hard_block() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_0_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 'std', 'resolution': '720p'},
            'media_roles': ['video_references'],
            'vfx_plate_transform': {'source_duration_seconds': 8},
        },
        profiles,
    )
    assert any(d['severity'] == 'WARN' and d['code'] == 'VFX_SD20_4K_RECOMMENDED' for d in diagnostics), diagnostics
    assert not any(d['severity'] == 'FAIL' and d['code'] == 'VFX_SD20_4K_RECOMMENDED' for d in diagnostics), diagnostics


def test_model_preflight_vfx_rejects_nonfinite_durations_when_context_is_active() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_5_HIGGSFIELD',
        {
            'gu_duration_seconds': float('nan'),
            'provider_params': {'mode': 'omni_reference', 'resolution': '720p'},
            'media_roles': ['video_references'],
            'vfx_plate_transform': {'source_duration_seconds': float('inf')},
        },
        profiles,
    )
    codes = {d['code'] for d in diagnostics if d['severity'] == 'FAIL'}
    assert 'VFX_GU_DURATION_REQUIRED' in codes
    assert 'VFX_SOURCE_DURATION_REQUIRED' in codes


def test_seedance20_vfx_requires_source_and_gu_runtime_metadata_for_auditable_planning() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_0_HIGGSFIELD',
        {
            'provider_params': {'mode': 'std', 'resolution': '4k'},
            'media_roles': ['video_references'],
            'vfx_plate_transform': {},
        },
        profiles,
    )
    codes = {d['code'] for d in diagnostics if d['severity'] == 'FAIL'}
    assert 'VFX_GU_DURATION_REQUIRED' in codes
    assert 'VFX_SOURCE_DURATION_REQUIRED' in codes


def test_seedance20_vfx_source_duration_mismatch_is_warning_not_hard_equality() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_0_HIGGSFIELD',
        {
            'gu_duration_seconds': 10,
            'provider_params': {'mode': 'std', 'resolution': '4k'},
            'media_roles': ['video_references'],
            'vfx_plate_transform': {'source_duration_seconds': 8},
        },
        profiles,
    )
    assert any(d['severity'] == 'WARN' and d['code'] == 'VFX_SD20_SOURCE_DURATION_DRIFT' for d in diagnostics), diagnostics
    assert not any(d['severity'] == 'FAIL' and d['code'] == 'VFX_SOURCE_DURATION_MISMATCH' for d in diagnostics), diagnostics


def test_non_vfx_seedance20_fast_and_non4k_remain_legal_without_vfx_warnings() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_0_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 'fast', 'resolution': '720p'},
            'media_roles': ['video_references'],
        },
        profiles,
    )
    assert not any(d['code'].startswith('VFX_') for d in diagnostics), diagnostics


def test_vfx_metadata_is_not_added_to_project_or_storyboard_required_schema() -> None:
    schema_text = '\n'.join(p.read_text(encoding='utf-8') for p in (ROOT / 'schemas').glob('*') if p.is_file())
    schema_text += '\n' + '\n'.join(
        p.read_text(encoding='utf-8')
        for p in (ROOT / 'references/cineweaver').rglob('*schema*')
        if p.is_file()
    )
    assert 'vfx_plate_transform' not in schema_text.lower()
