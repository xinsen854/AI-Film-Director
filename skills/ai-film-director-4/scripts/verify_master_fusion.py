#!/usr/bin/env python3
"""Reverse-architecture audit for the AFD Master + Forge fusion.

This validator reasons backward from the promised final package contract:
formal delivery -> AFD production -> CineWeaver director chain -> Forge locked
AUDIT -> Forge screenplay/design -> AFD intake.  It checks that no competing
public Skill or legacy emotion authority can satisfy the same formal role.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_STAGES = [
    'PROJECT_INTAKE','FORGE_DESIGN','DESIGN_HANDOFF','CREATIVE_BIBLE',
    'SCREENWRITER','FORGE_GATE_QC_DEAI','SCRIPT_LOCK','FORGE_AUDIT',
    'LOCKED_AUDIT_HANDOFF','FORGE_EMOTION_RENDER','SCENE_INTELLIGENCE',
    'CAPABILITY_ROUTER','DIRECTOR_CRAFT','SCENE_DIRECTION','ASSET_ENGINE',
    'SPATIAL','SHOT_SEGMENT','FINAL_HARD_QC','PRODUCTION_LEDGER','EXPORTS',
]
ROOT_ORDER_TOKENS = [
    '01 项目接入','02 Forge DESIGN','03 设计桥接','04 项目创作圣经',
    '05 Human-Truth Screenwriter','06 Forge Gate / QC / De-AI','07 剧本锁定控制器',
    '08 Forge AUDIT','09 锁稿审计桥接','10 Forge Emotion Renderer',
    '11 Scene Intelligence','12 Capability Router','13 Director Craft','14 AFD Scene Direction',
    '15 Asset Engine','16 Spatial','17 Shot / Segment','18 Final Hard QC','19 Production Ledger','20 八件套导出',
]
ADAPTERS = {
    'references/modules/story-development/module.md': 'ADAPTER_ONLY',
    'references/modules/screenplay-authority/module.md': 'PROJECTION_ONLY',
    'references/modules/audience-emotion-architecture/module.md': 'COMPATIBILITY_PROJECTION_ONLY',
    'references/modules/audience-emotion-causality/module.md': 'HANDOFF_PROJECTION_ONLY',
}
FORGE_FACADES = [
    'references/forge/design.md',
    'references/forge/human-truth-screenwriter.md',
    'references/forge/gate.md',
    'references/forge/audit.md',
    'references/forge/emotion-renderer.md',
]
PRODUCTION_CONTROL_FILES = [
    'SKILL.md',
    'references/contracts/audience-emotion-architecture-format.md',
    'references/modules/audience-emotion-architecture/module.md',
    'references/modules/audience-emotion-causality/module.md',
    'scripts/run_pipeline.py',
    'scripts/build_exports.py',
    'scripts/validate_unit_consistency.py',
]
FORGE_MARKERS = [
    '全剧情情绪总谱', 'Audience Time', 'Story Time',
    'CHARACTER + AUDIENCE EMOTION FIELD', 'AUDIENCE HALO',
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_stage_literal(path: Path) -> list[str] | None:
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    except (OSError, SyntaxError):
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'STAGES':
                    try:
                        value = ast.literal_eval(node.value)
                    except Exception:
                        return None
                    return value if isinstance(value, list) else None
    return None


def _minimal_locked_audit() -> dict:
    return {
        'meta': {'title':'REVERSE_AUDIT','runtime':'10s','precision':'SCRIPT_FINE','workflow_stage':'locked_audit','format':'short','quality_route':'STANDARD'},
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
    }


def _renderer_smoke(root: Path) -> list[str]:
    renderer = root / 'scripts/render_emotion_map.py'
    if not renderer.is_file():
        return ['formal Forge renderer wrapper missing: scripts/render_emotion_map.py']
    with tempfile.TemporaryDirectory(prefix='afd_master_reverse_') as tmp:
        tmp = Path(tmp)
        source = tmp / 'audit.json'
        target = tmp / 'map.html'
        source.write_text(json.dumps(_minimal_locked_audit(), ensure_ascii=False), encoding='utf-8')
        result = subprocess.run(
            [sys.executable, str(renderer), str(source), str(target)],
            cwd=str(root), text=True, capture_output=True, check=False,
            env={**__import__('os').environ, 'PYTHONDONTWRITEBYTECODE':'1'},
        )
        if result.returncode != 0:
            return ['Forge renderer smoke test failed: ' + (result.stdout + result.stderr).strip()]
        if not target.is_file():
            return ['Forge renderer smoke test did not create HTML']
        html = target.read_text(encoding='utf-8')
        errors = [f'Forge renderer marker missing: {marker}' for marker in FORGE_MARKERS if marker not in html]
        if '观众主波浪' in html or 'emotion_contract_version=4.3' in html:
            errors.append('legacy AFD emotion visual leaked into formal Forge renderer output')
        return errors


def validate_master_fusion(skill_root: str | Path, *, smoke_render: bool = True) -> list[str]:
    root = Path(skill_root).resolve()
    errors: list[str] = []
    if not root.is_dir():
        return [f'skill root not found: {root}']

    # 1) Reverse from public entry: exactly one discoverable Skill/agent entry.
    skills = list(root.rglob('SKILL.md'))
    if skills != [root / 'SKILL.md']:
        errors.append(f'public entry conflict: expected one root SKILL.md, found {len(skills)}')
    forge_agents = list((root / 'references/forge').rglob('openai.yaml')) if (root/'references/forge').is_dir() else []
    if forge_agents:
        errors.append('embedded Forge agents/openai.yaml would compete with master entry')

    # 2) Master must own sequence, not creative semantics.
    master = root / 'scripts/master_orchestrator.py'
    stages = _read_stage_literal(master) if master.is_file() else None
    if stages != EXPECTED_STAGES:
        errors.append(f'master stage order mismatch: {stages!r}')
    skill = (root/'SKILL.md').read_text(encoding='utf-8') if (root/'SKILL.md').is_file() else ''
    positions = []
    for token in ROOT_ORDER_TOKENS:
        pos = skill.find(token)
        if pos < 0:
            errors.append(f'root master order token missing: {token}')
        positions.append(pos)
    if all(pos >= 0 for pos in positions) and positions != sorted(positions):
        errors.append('root master 20-stage order is not monotonic')
    for token in ('总控 = 状态机 + 路由器 + 闸门', 'Bridge compiles; bridge never interprets.', '情绪 HTML 是分析/交付物，不是剧情素材'):
        if token not in skill:
            errors.append(f'master invariant missing: {token}')

    # 3) Forge must be internalized and old AFD upstream must be adapters only.
    for rel in FORGE_FACADES:
        path = root / rel
        if not path.is_file() or not path.read_text(encoding='utf-8').strip():
            errors.append(f'Forge internal facade missing: {rel}')
    for path in (root/'references/forge/source').glob('*/source_skill.md') if (root/'references/forge/source').is_dir() else []:
        text = path.read_text(encoding='utf-8')[:1500]
        if 'ARCHIVAL_SOURCE_ONLY' not in text or '非执行入口' not in text:
            errors.append(f'Forge source skill not marked archival: {path.relative_to(root).as_posix()}')
    for rel, marker in ADAPTERS.items():
        path = root / rel
        text = path.read_text(encoding='utf-8') if path.is_file() else ''
        if marker not in text:
            errors.append(f'{rel} missing {marker}')

    # 4) Formal emotion authority must point to exact Forge critical source.
    if (root/'scripts/render_legacy_afd_emotion_map.py').exists():
        errors.append('legacy AFD renderer file still present in fusion package')
    provenance_path = root/'references/forge/SOURCE_PROVENANCE.json'
    if not provenance_path.is_file():
        errors.append('Forge SOURCE_PROVENANCE.json missing')
    else:
        try:
            provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
            if provenance.get('upstream_version') != 'v1.1.4':
                errors.append('Forge source provenance version is not v1.1.4')
            for item in provenance.get('critical_files', []):
                path = root / str(item.get('path',''))
                if not path.is_file():
                    errors.append(f'Forge source file missing: {item.get("path")}')
                elif _sha(path) != item.get('sha256'):
                    errors.append(f'Forge source hash mismatch: {item.get("path")}')
        except Exception as exc:
            errors.append(f'invalid Forge source provenance: {exc}')

    wrapper = (root/'scripts/render_emotion_map.py').read_text(encoding='utf-8') if (root/'scripts/render_emotion_map.py').is_file() else ''
    if "references' / 'forge' / 'source' / 'emotion-story-forge'" not in wrapper or "forge_locked_audit.json" not in wrapper:
        errors.append('formal renderer wrapper is not wired to embedded Forge locked-audit renderer')
    for rel in PRODUCTION_CONTROL_FILES:
        path = root / rel
        text = path.read_text(encoding='utf-8') if path.is_file() else ''
        if 'render_legacy_afd_emotion_map' in text:
            errors.append(f'legacy emotion renderer referenced by production control: {rel}')
    for rel in ('scripts/run_pipeline.py','scripts/build_exports.py','scripts/validate_unit_consistency.py'):
        text = (root/rel).read_text(encoding='utf-8') if (root/rel).is_file() else ''
        if 'forge_locked_audit.json' not in text:
            errors.append(f'formal production file does not depend on Forge locked audit: {rel}')
    build = (root/'scripts/build_exports.py').read_text(encoding='utf-8') if (root/'scripts/build_exports.py').is_file() else ''
    if 'render_forge_emotion_map(root)' not in build:
        errors.append('export path does not forcibly rerender formal 05 from Forge audit')

    # 5) Deterministic bridges and lock controller must exist.
    for rel in ('scripts/compile_forge_handoff.py','schemas/master_orchestrator_state.schema.json'):
        if not (root/rel).is_file():
            errors.append(f'master integration file missing: {rel}')
    bridge = (root/'scripts/compile_forge_handoff.py').read_text(encoding='utf-8') if (root/'scripts/compile_forge_handoff.py').is_file() else ''
    for token in ('integration.afd', 'compiler will not infer missing semantics', 'forge_audit_sha256', 'screenplay_sha256'):
        if token not in bridge:
            errors.append(f'bridge deterministic invariant missing: {token}')

    if smoke_render and not errors:
        errors.extend(_renderer_smoke(root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description='Reverse-audit AFD Master + Forge fusion architecture')
    parser.add_argument('--skill-root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--skip-smoke-render', action='store_true')
    args = parser.parse_args()
    errors = validate_master_fusion(args.skill_root, smoke_render=not args.skip_smoke_render)
    if errors:
        print('FAIL: master fusion reverse audit')
        for item in errors:
            print('-', item)
        return 1
    print('PASS: master fusion reverse audit')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
