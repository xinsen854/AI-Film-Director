from __future__ import annotations

import json
import hashlib
from pathlib import Path

from render_asset_library import render_asset_library
from render_emotion_map import render_emotion_map


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')



def minimal_forge_locked_audit() -> dict:
    return {
        "meta": {"title":"TEST","runtime":"10s","precision":"SCRIPT_FINE","workflow_stage":"locked_audit","format":"short","quality_route":"STANDARD"},
        "fact_boundary": {"locked":[],"supported":[],"proposed":[],"verify":[]},
        "canonical_names": [], "rhythm_causality": [], "characters": [], "relationship_shifts": [],
        "audience_path": [], "breakpoints": [], "unknowns": [], "directions": [],
        "production_packet": {"scope":"unit","incoming_state":{},"required_event":[],"character_interpretations":[],"relationship_transmission":[],"audience_knowledge":{},"debts_in":[],"required_irreversible_change":[],"next_unit_interface":{}},
        "state_delta": {"new_facts":[],"knowledge_changes":[],"character_changes":[],"relationship_debt_changes":[],"opened_loops":[],"closed_loops":[],"last_irreversible_change":"none","next_unit":"none"},
        "script_audit": {"source_script_version":"S1","precision":"SCRIPT_FINE","causality_findings":[],"continuity_findings":[],"audience_findings":[],"repair_scope":[],"lock_status":"LOCKED","blueprint_evidence_diff":[]},
        "long_form": {"continuation_ledger":{}},
        "handoff": {"premise":"x","human_question":"x","competing_values":[],"motifs":[],"ending_aftertaste":"x","next_ai_prompt":"x"},
        "narrative_topology": {"continuity_mode":"continuous","story_time_basis":"story order","audience_time_basis":"screen order","notes":[]},
        "audience_lenses": [{"id":"AUD1","label":"整体观众","perspective":"整体观看立场","question_lens":"发生了什么","evidence_refs":[]}],
        "phase_events": [{"id":"P01","label":"建立","scope_label":"全片","state_change_reason":"初始状态","summary":"建立","confidence":"high","trigger":"开场","story_order":1,"audience_order":1,"character_states":[],"audience_states":[],"relationship_changes":[],"irreversible_changes":[],"evidence_refs":[]}],
        "phase_links": [],
        "global_emotional_arc": {"summary":"全剧情情绪总谱","ending_residue":"余味","aggregation_policy":"derive_from_phase_states","phase_ids":["P01"],"major_turns":[]}
    }


def prepare_forge_emotion_authority(root: Path, *, render_html: bool = True) -> None:
    audit = root / 'state' / 'forge_locked_audit.json'
    dump(audit, minimal_forge_locked_audit())
    dump(root / 'state' / 'audience_emotion_architecture.json', {'compatibility_only': True})
    digest = hashlib.sha256(audit.read_bytes()).hexdigest()
    dump(root / 'state' / 'forge_alignment.json', {
        'alignment_contract':'FORGE_AFD_ALIGNMENT_V1',
        'forge_audit_sha256': digest,
        'lock_status':'LOCKED'
    })
    if render_html:
        render_emotion_map(root)

def prepare_project_prerequisites(root: Path) -> None:
    for d in ('assets', 'screenplay', 'director', 'state/scene_intelligence', 'state/router', 'state/director_craft', 'state/spatial_narrative', 'state/audience_causal'):
        (root / d).mkdir(parents=True, exist_ok=True)
    pipeline_path = root / 'state' / 'pipeline_state.json'
    state = json.loads(pipeline_path.read_text(encoding='utf-8'))
    state.update({
        'confirmed_brief': True,
        'story_authority_ready': True,
        'asset_library_ready': True,
        'scene_intelligence_ready': True,
        'director_craft_ready': True,
    })
    dump(pipeline_path, state)
    asset_payload = {'ASSET_LIBRARY': {
        'contract_version': '4.3',
        'project_asset_policy': {
            'world_and_visual_style': '测试现实主义',
            'character_face_policy': '身份稳定',
            'image_prompt_policy': '可复现',
            'voice_asset_policy': 'V-series text only',
        },
        'quick_index': [], 'character_assets': [], 'location_assets': [], 'prop_assets': [],
        'g_assets': [], 'persistent_states': [], 'voice_assets': [],
    }}
    dump(root / 'assets' / 'ASSET_LIBRARY.json', asset_payload)
    (root / 'assets' / 'ASSET_LIBRARY.md').write_text(render_asset_library(asset_payload), encoding='utf-8')
    if not (root / 'state' / 'story_authority.json').exists():
        dump(root / 'state' / 'story_authority.json', {'atoms': []})
    if not (root / 'state' / 'information_ledger.json').exists():
        dump(root / 'state' / 'information_ledger.json', {'items': []})
    if not (root / 'state' / 'forge_locked_audit.json').exists():
        prepare_forge_emotion_authority(root, render_html=True)
    elif not (root / 'AUDIENCE_EMOTION_MAP.html').exists():
        render_emotion_map(root)


def prepare_scene_chain(root: Path, unit_id: str, scene_id: str = 'SC01', *, per_scene: bool = False, spatial_active: bool = False, create_spatial: bool = True) -> None:
    prepare_project_prerequisites(root)
    (root / 'screenplay' / f'{unit_id}_LOCKED_SCREENPLAY.md').write_text(f'# {unit_id} 正式编剧剧本\n{scene_id} 测试内容\n', encoding='utf-8')
    (root / 'director' / f'{unit_id}_INTEGRATED_DIRECTOR_SCREENPLAY.md').write_text(
        f'# {unit_id} 整合导演剧本\n## 正式编剧剧本\n{scene_id} 测试内容\n## 导演执行\n{scene_id} 测试导演执行\n',
        encoding='utf-8',
    )
    dump(root / 'state' / 'audience_causal' / f'{unit_id}_{scene_id}.json', {
        'scene_id': scene_id, 'target_viewer_state': '理解当前变化', 'audience_state_before': {},
        'story_triggers': ['当前动作'], 'information_released': [], 'information_withheld': [],
        'cognitive_shift': '理解动作结果', 'why_emotion_changes': '当前剧情刺激', 'audience_state_after': {},
        'support_level': 'SUPPORTED', 'evidence': ['当前剧情'], 'director_handoff': {'must_be_perceptible': ['动作结果']},
    })
    suffix = f'{unit_id}_{scene_id}' if per_scene else unit_id
    dump(root / 'state' / 'scene_intelligence' / f'{suffix}_scene_intelligence.json', {
        'SCENE_INTELLIGENCE_RESULT': {
            'scene_id': scene_id, 'scene_core': '测试场景核心',
            'dramatic_function': {'primary': '推进当前剧情'},
            'beat_map': [{'beat_id': 'B1', 'change_basis': '人物完成动作'}],
            'confidence_overall': 0.9,
        }
    })
    active = ['SPATIAL_TOPOLOGY'] if spatial_active else []
    downstream = {'asset_engine': [], 'performance_engine': [], 'director_craft_engine': [], 'cinekernel': [], 'spatial_narrative_engine': active.copy()}
    dump(root / 'state' / 'router' / f'{suffix}_router_result.json', {
        'ROUTER_RESULT': {
            'scene_id': scene_id,
            'scene_strategy': {'dominant_need': '清楚执行当前动作', 'routing_density': 'LOW', 'rationale': '测试最小必要能力'},
            'active_capabilities': active, 'suppressed_capabilities': [], 'downstream': downstream, 'routing_confidence': 0.9,
        }
    })
    dump(root / 'state' / 'director_craft' / f'{suffix}_director_craft.json', {
        'DIRECTOR_CRAFT_RESULT': {
            'scene_id': scene_id,
            'scene_expression_goal': {'dominant_read': '动作与反应清楚'},
            'beat_expressions': [{'beat_id': 'B1', 'dramatic_action': '完成当前动作', 'visible_carriers': ['视线变化']}],
            'handoff_to_shot_design': {'must_be_readable': ['动作结果']},
            'confidence': 0.9,
        }
    })
    if spatial_active and create_spatial:
        dump(root / 'state' / 'spatial_narrative' / f'{unit_id}_{scene_id}_spatial_narrative.json', {
            'SPATIAL_NARRATIVE_RESULT': {'scene_id': scene_id, 'activation_state': 'ACTIVE'}
        })


def prepare_upstream_chain(root: Path, unit_id: str, *, create_empty_authority: bool = False) -> None:
    # Backward-compatible single-scene fixture used by the earlier low-level tests.
    prepare_scene_chain(root, unit_id, 'SC01', per_scene=False)
    if create_empty_authority and not (root / 'state' / 'story_authority.json').exists():
        dump(root / 'state' / 'story_authority.json', {'atoms': []})
