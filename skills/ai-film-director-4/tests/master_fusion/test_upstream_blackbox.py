from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
TESTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from master_orchestrator import init_state, load_state, pass_stage
from compile_forge_handoff import compile_design, compile_locked_audit
from render_emotion_map import render_emotion_map
from test_hardening_regressions import _compatibility_projection


def dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def locked_audit_payload() -> dict:
    return {
        'meta': {'title':'BLACKBOX','runtime':'10s','precision':'SCRIPT_FINE','workflow_stage':'locked_audit','format':'short','quality_route':'STANDARD','blueprint_version':'B1'},
        'fact_boundary': {'locked':[],'supported':[],'proposed':[],'verify':[]},
        'canonical_names': [], 'rhythm_causality': [], 'characters': [], 'relationship_shifts': [],
        'audience_path': [], 'breakpoints': [], 'unknowns': [], 'directions': [],
        'production_packet': {'scope':'unit','incoming_state':{},'required_event':[],'character_interpretations':[],'relationship_transmission':[],'audience_knowledge':{},'debts_in':[],'required_irreversible_change':[],'next_unit_interface':{}},
        'state_delta': {'new_facts':[],'knowledge_changes':[],'character_changes':[],'relationship_debt_changes':[],'opened_loops':[],'closed_loops':[],'last_irreversible_change':'none','next_unit':'none'},
        'script_audit': {'source_script_version':'S1','precision':'SCRIPT_FINE','causality_findings':[],'continuity_findings':[],'audience_findings':[],'repair_scope':[],'lock_status':'LOCKED','blueprint_evidence_diff':[]},
        'long_form': {'continuation_ledger':{}},
        'handoff': {'premise':'x','human_question':'x','competing_values':[],'motifs':[],'ending_aftertaste':'x','next_ai_prompt':'x'},
        'narrative_topology': {'continuity_mode':'continuous','story_time_basis':'story order','audience_time_basis':'screen order','notes':[]},
        'audience_lenses': [{'id':'AUD1','label':'整体观众','perspective':'整体观看立场','question_lens':'发生了什么','evidence_refs':[]}],
        'phase_events': [{'id':'P01','label':'建立','scope_label':'全片','state_change_reason':'初始状态','summary':'建立','confidence':'high','trigger':'开场','story_order':1,'audience_order':1,'character_states':[],'audience_states':[],'relationship_changes':[],'irreversible_changes':[],'evidence_refs':[]}],
        'phase_links': [],
        'global_emotional_arc': {'summary':'全剧情情绪总谱','ending_residue':'余味','aggregation_policy':'derive_from_phase_states','phase_ids':['P01'],'major_turns':[]},
        'integration': {'afd': {
            'unit_id':'EP01',
            'locked_screenplay_path':'lock_candidates/EP01_LOCK_CANDIDATE.md',
            'script_version':'S1',
            'script_review_markdown':'# 剧本审查\nPASS',
            'story_authority': {'atoms':[{
                'atom_id':'A1','unit_id':'EP01','scene_id':'SC01','type':'action',
                'content':'真实锁稿正文','locked':True,
            }]},
            'information_ledger': {'items':[{
                'info_id':'I1','truth':'信息真相','character_knowledge':{},'audience_state':{},
                'reveal_stage':'LATENT','status':'HIDDEN',
            }]},
            'audience_emotion_compat_projection': _compatibility_projection(),
            'scene_handoffs': [{
                'scene_id':'SC01','story_atom_refs':['A1'],'information_refs':['I1'],
                'must_be_perceptible':[],'must_remain_implicit':[],'must_not_be_revealed':[],
                'key_reaction_requests':[],'key_listener_or_third_party_response':[],
                'environmental_pressure_or_release':[],'important_object_or_space_evidence':[],
                'emotion_capacity_note':'SUPPORTED'
            }]
        }}
    }


def test_master_blackbox_reaches_scene_intelligence_only_through_forge_locked_audit_and_renderer(tmp_path):
    root = tmp_path
    (root/'state').mkdir()
    (root/'lock_candidates').mkdir()
    (root/'state/afd_visual_production.md').write_text('## AFD视觉\n现实主义', encoding='utf-8')

    init_state(root, 'AUTO_ACCEPT_AFTER_QC')
    pass_stage(root, 'PROJECT_INTAKE', artifact='state/afd_visual_production.md')

    design = root/'forge_design_input.json'
    dump(design, {
        'meta': {'workflow_stage':'design','blueprint_version':'B1'},
        'integration': {'afd': {'creative_bible_story_markdown':'## Forge故事\n锁定故事设计'}}
    })
    pass_stage(root, 'FORGE_DESIGN', artifact='forge_design_input.json')
    compile_design(root, design, root/'state/afd_visual_production.md')
    pass_stage(root, 'DESIGN_HANDOFF', artifact='PROJECT_CREATIVE_BIBLE.md')
    pass_stage(root, 'CREATIVE_BIBLE', artifact='PROJECT_CREATIVE_BIBLE.md')

    candidate = root/'lock_candidates/EP01_LOCK_CANDIDATE.md'
    candidate.write_text('# EP01\nSC01 真实锁稿正文', encoding='utf-8')
    pass_stage(root, 'SCREENWRITER', artifact='lock_candidates/EP01_LOCK_CANDIDATE.md')
    pass_stage(root, 'FORGE_GATE_QC_DEAI', artifact='lock_candidates/EP01_LOCK_CANDIDATE.md')
    state = load_state(root)
    assert state['current_stage'] == 'FORGE_AUDIT'
    assert state['lock_status'] == 'LOCKED'
    assert state['locked_screenplay_sha256']

    audit = root/'forge_locked_audit_input.json'
    dump(audit, locked_audit_payload())
    pass_stage(root, 'FORGE_AUDIT', artifact='forge_locked_audit_input.json')
    compile_locked_audit(root, audit)
    pass_stage(root, 'LOCKED_AUDIT_HANDOFF', artifact='state/forge_locked_audit.json')
    render_emotion_map(root)
    pass_stage(root, 'FORGE_EMOTION_RENDER', artifact='AUDIENCE_EMOTION_MAP.html')

    state = load_state(root)
    assert state['current_stage'] == 'SCENE_INTELLIGENCE'
    html = (root/'AUDIENCE_EMOTION_MAP.html').read_text(encoding='utf-8')
    assert '全剧情情绪总谱' in html
    assert 'Audience Time' in html
    assert 'Story Time' in html
    assert 'CHARACTER + AUDIENCE EMOTION FIELD' in html
    assert 'AUDIENCE HALO' in html
    assert '观众主波浪' not in html
    alignment = json.loads((root/'state/forge_alignment.json').read_text(encoding='utf-8'))
    assert alignment['lock_status'] == 'LOCKED'
    assert alignment['screenplay_sha256'] == state['locked_screenplay_sha256']
