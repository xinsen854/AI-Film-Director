from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_performance_expression_carries_four_part_body_baseline_and_interrupted_business() -> None:
    text = read('references/cineweaver/Director_Craft_Engine_V1.0/runtime/PERFORMANCE_EXPRESSION.md')
    for term in ('center of gravity', 'tempo', 'openness', 'breath'):
        assert term in text.lower()
    assert 'interrupted business' in text.lower() or 'stop the business' in text.lower()
    assert 'not every character' in text.lower() or 'not every beat' in text.lower()


def test_reaction_policy_gives_visible_silent_listener_a_playable_task() -> None:
    text = read('references/cineweaver/Director_Craft_Engine_V1.0/runtime/REACTION_POLICY.md').lower()
    assert 'silent listener' in text
    assert 'playable task' in text
    assert 'do not invent' in text or 'must come from' in text


def test_eye_life_is_mandatory_consideration_not_mandatory_prompt_noise() -> None:
    text = read('references/cineweaver/Director_Craft_Engine_V1.0/runtime/MICRO_EXPRESSION_POLICY.md').lower()
    assert 'eye life' in text
    assert 'mandatory consideration' in text
    assert 'explicit' in text and ('selective' in text or 'only when' in text)


def test_ensemble_scene_direction_and_motive_are_kept_as_optional_unproven_technique() -> None:
    text = read('references/cineweaver/Director_Craft_Engine_V1.0/runtime/ENSEMBLE_COHESION.md')
    lower = text.lower()
    assert 'scene direction' in lower
    assert 'motive' in lower
    assert '[demo' in lower and 'unproven' in lower
    assert 'optional' in lower
    assert 'must not override' in lower
    assert 'story authority' in lower


def test_director_craft_routes_ensemble_technique_without_new_owner_or_required_schema() -> None:
    module = read('references/cineweaver/Director_Craft_Engine_V1.0/module.md').lower()
    schema = read('references/cineweaver/Director_Craft_Engine_V1.0/schema/DIRECTOR_CRAFT_RESULT.yaml').lower()
    assert 'ensemble_cohesion.md' in module
    assert 'multi-character' in module or 'ensemble' in module
    # The experimental technique must not become a new required result object.
    assert 'scene_direction:' not in schema
    assert 'character_motives:' not in schema


def test_latest_acting_source_specific_counts_are_not_promoted_to_global_hard_gates() -> None:
    engine = read('references/cineweaver/CineKernel_V1.0/core/ENGINE_SPEC.md').lower()
    module = read('references/cineweaver/Director_Craft_Engine_V1.0/module.md').lower()
    combined = engine + '\n' + module
    assert '150–220' not in combined
    assert '150-220' not in combined
    assert '2–4 beat changes' not in combined
    assert '2-4 beat changes' not in combined
    assert 'every character must have physical business' not in combined


def test_existing_acting_owner_and_minimum_expression_boundary_remain_intact() -> None:
    engine = read('references/cineweaver/CineKernel_V1.0/core/ENGINE_SPEC.md')
    module = read('references/cineweaver/Director_Craft_Engine_V1.0/module.md')
    assert '# B. PERFORMANCE ENGINE' in engine
    assert 'CHARACTER_PERFORMANCE_IDENTITY' in engine
    assert 'Minimum Necessary Expression' in module
    assert '1–3 high-information observable carriers' in module
