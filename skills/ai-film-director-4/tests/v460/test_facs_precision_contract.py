from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_facs_policy_is_optional_high_precision_layer_not_new_owner() -> None:
    text = read('references/cineweaver/Director_Craft_Engine_V1.0/runtime/FACS_PRECISION_POLICY.md').lower()
    assert 'optional' in text
    assert 'high-precision' in text or 'high precision' in text
    assert 'not a new owner' in text or 'no new owner' in text
    assert 'close-up' in text or 'closeup' in text
    assert 'not every shot' in text or 'not every beat' in text


def test_facs_provenance_separates_standard_au_vocabulary_from_model_empiricism() -> None:
    text = read('references/cineweaver/Director_Craft_Engine_V1.0/runtime/FACS_PRECISION_POLICY.md').lower()
    assert 'standard' in text and ('action unit' in text or 'au vocabulary' in text)
    assert 'empirical' in text
    assert 'not a guarantee' in text or 'not deterministic' in text
    assert 'provider parameter' in text or 'api parameter' in text


def test_facs_uses_existing_beat_evidence_and_cannot_invent_emotion_or_story() -> None:
    text = read('references/cineweaver/Director_Craft_Engine_V1.0/runtime/FACS_PRECISION_POLICY.md').lower()
    assert 'beat' in text
    assert 'visible carrier' in text or 'observable carrier' in text
    assert 'do not invent' in text or 'must not invent' in text
    assert 'story authority' in text
    assert 'emotion' in text


def test_facs_supports_codes_and_anatomical_fallback_instead_of_code_only_lockin() -> None:
    text = read('references/cineweaver/Director_Craft_Engine_V1.0/runtime/FACS_PRECISION_POLICY.md').lower()
    assert 'codes-only' in text or 'codes only' in text
    assert 'anatomical' in text
    assert 'fallback' in text or 'degrade' in text
    assert 'observable' in text


def test_facs_sheet_is_plan_first_small_optional_and_verified_not_full_dump() -> None:
    text = read('references/cineweaver/Director_Craft_Engine_V1.0/runtime/FACS_PRECISION_POLICY.md').lower()
    assert 'plan first' in text or 'plan-first' in text
    assert 'optional' in text and 'sheet' in text
    assert '49' in text and ('do not' in text or 'anti-pattern' in text)
    assert 'verify' in text or 'verification' in text


def test_seedance_20_profile_marks_facs_as_empirical_prompt_heuristic_only() -> None:
    sd20 = read('references/cineweaver/Shot_Segment_Engine_V1.3/runtime/SEEDANCE_2_0_PROFILE.md').lower()
    sd25 = read('references/cineweaver/Shot_Segment_Engine_V1.3/runtime/SEEDANCE_2_5_PROFILE.md').lower()
    assert 'facs' in sd20 and 'empirical' in sd20
    assert 'not' in sd20 and ('api' in sd20 or 'provider' in sd20)
    # Do not silently promote the 2.0 heuristic to 2.5 without source evidence.
    assert 'facs' not in sd25 or ('not verified' in sd25 or 'do not assume' in sd25 or 'unsupported' in sd25)


def test_shot_handoff_preserves_facs_only_when_adapter_allows_and_falls_back_when_not() -> None:
    text = read('references/cineweaver/Shot_Segment_Engine_V1.3/runtime/DIRECTOR_CRAFT_INTEGRATION.md').lower()
    assert 'facs' in text
    assert 'adapter' in text or 'model profile' in text
    assert 'anatomical' in text or 'observable' in text
    assert 'do not drop' in text or 'must preserve' in text


def test_facs_does_not_add_required_schema_or_global_expression_count_gate() -> None:
    schema = read('references/cineweaver/Director_Craft_Engine_V1.0/schema/DIRECTOR_CRAFT_RESULT.yaml').lower()
    core = read('references/cineweaver/CineKernel_V1.0/core/ENGINE_SPEC.md').lower()
    assert 'facs:' not in schema
    assert 'au_schedule:' not in schema
    assert '3–4 expressions max' not in core
    assert '3-4 expressions max' not in core


def test_facs_source_specific_expression_count_remains_model_heuristic_not_global_blocker() -> None:
    text = read('references/cineweaver/Director_Craft_Engine_V1.0/runtime/FACS_PRECISION_POLICY.md').lower()
    assert '3–4' in text or '3-4' in text
    assert 'heuristic' in text or 'empirical' in text
    assert 'not' in text and ('global hard' in text or 'global blocker' in text or 'universal hard' in text)


def _load_preflight_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location('afd_model_preflight_for_facs', ROOT / 'scripts' / 'model_preflight.py')
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_model_preflight_warns_when_facs_au_text_leaks_to_unverified_profile() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_5_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 't2v', 'resolution': '720p'},
            'prompt_text': 'Close-up. AU12 + AU6, then au 4 as the answer lands.',
        },
        profiles,
    )
    assert any(d['severity'] == 'WARN' and d['code'] == 'FACS_UNVERIFIED_PROFILE' for d in diagnostics), diagnostics
    assert not any(d['severity'] == 'FAIL' and d['code'] == 'FACS_UNVERIFIED_PROFILE' for d in diagnostics), diagnostics


def test_model_preflight_does_not_warn_for_seedance20_facs_heuristic() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_0_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 'std', 'resolution': '720p'},
            'prompt_text': 'Close-up. AU12 (lip-corner puller) with AU6 (cheek raiser).',
        },
        profiles,
    )
    assert not any(d['code'] == 'FACS_UNVERIFIED_PROFILE' for d in diagnostics), diagnostics


def test_model_preflight_does_not_false_positive_on_non_au_words() -> None:
    mod = _load_preflight_module()
    profiles = mod.load_profiles(ROOT / 'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json')
    diagnostics = mod.preflight(
        'SEEDANCE_2_5_HIGGSFIELD',
        {
            'gu_duration_seconds': 8,
            'provider_params': {'mode': 't2v', 'resolution': '720p'},
            'prompt_text': 'AUDIENCE attention stays on the eyes; the face remains restrained.',
        },
        profiles,
    )
    assert not any(d['code'] == 'FACS_UNVERIFIED_PROFILE' for d in diagnostics), diagnostics


def test_final_prompt_qc_requires_prompt_text_in_preflight_request_so_facs_scan_cannot_be_skipped() -> None:
    text = read('references/cineweaver/Final_QC_Engine_V1.3/runtime/PROMPT_QC.md').lower()
    assert 'prompt_text' in text
    assert 'final' in text
    assert 'must' in text or '必须' in text
    assert 'facs_unverified_profile' in text.lower()
