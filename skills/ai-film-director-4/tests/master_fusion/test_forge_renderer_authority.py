from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from render_emotion_map import render_emotion_map, validate_emotion_payload


def minimal_locked_audit():
    return {
      "meta": {"title":"测试","runtime":"60s","precision":"SCRIPT_FINE","workflow_stage":"locked_audit","format":"short","quality_route":"STANDARD"},
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
      "global_emotional_arc": {"summary":"全剧情总谱","ending_residue":"余味","aggregation_policy":"derive_from_phase_states","phase_ids":["P01"],"major_turns":[]}
    }


def test_formal_renderer_reads_forge_locked_audit_and_emits_forge_visual_system(tmp_path):
    state = tmp_path/'state'; state.mkdir()
    (state/'forge_locked_audit.json').write_text(json.dumps(minimal_locked_audit(), ensure_ascii=False), encoding='utf-8')
    out = render_emotion_map(tmp_path)
    html = out.read_text(encoding='utf-8')
    for marker in ['全剧情情绪总谱','Audience Time','Story Time','CHARACTER + AUDIENCE EMOTION FIELD','AUDIENCE HALO']:
        assert marker in html
    assert '观众主波浪' not in html


def test_old_afd_emotion_projection_is_not_valid_forge_audit():
    old = {"emotion_contract_version":"4.3","actor_emotion_tracks":[]}
    errors = validate_emotion_payload(old)
    assert errors
    assert any('meta' in e or 'fact_boundary' in e for e in errors)


def test_production_scripts_use_forge_locked_audit_not_compat_projection():
    run = (ROOT/'scripts/run_pipeline.py').read_text(encoding='utf-8')
    build = (ROOT/'scripts/build_exports.py').read_text(encoding='utf-8')
    unit = (ROOT/'scripts/validate_unit_consistency.py').read_text(encoding='utf-8')
    for text in (run, build, unit):
        assert 'forge_locked_audit.json' in text
    assert "_run('render_emotion_map.py', '--project-root'" not in run


def test_forge_critical_source_provenance_is_hash_locked():
    provenance = json.loads((ROOT/'references/forge/SOURCE_PROVENANCE.json').read_text(encoding='utf-8'))
    assert provenance['upstream_version'] == 'v1.1.4'
    for item in provenance['critical_files']:
        path = ROOT / item['path']
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']
