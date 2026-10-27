#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from skill_integrity import verify_manifest

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
MODULES = [
    'project-intake', 'story-development', 'screenplay-authority',
    'audience-emotion-architecture', 'audience-emotion-causality',
    'scene-direction', 'asset-production', 'quality-delivery',
]
CINEWEAVER_ENGINES = [
    'CineKernel_V1.0', 'Scene_Intelligence_V1.0', 'Capability_Router_V1.1',
    'Director_Craft_Engine_V1.0', 'Spatial_Narrative_Engine_V1.0',
    'Asset_Engine_V4.1', 'Shot_Segment_Engine_V1.3', 'Final_QC_Engine_V1.3',
]
REQUIRED = [
    'SKILL.md', 'PACKAGE_MANIFEST.json', 'MANIFEST.sha256', 'agents/openai.yaml',
    'requirements.txt', 'requirements-test.txt',
    'references/contracts/production-unit-packet.md', 'references/contracts/production-ledger-contract.md',
    'references/contracts/story-authority-contract.md', 'references/contracts/asset-prompt-contract.md',
    'references/contracts/screenplay-format.md', 'references/contracts/director-screenplay-format.md',
    'references/contracts/audience-emotion-architecture-format.md',
    'references/libraries/audience-emotion-mechanisms.json', 'references/libraries/scene-direction-patterns.json',
    'scripts/production_ledger.py', 'scripts/validate_unit_consistency.py',
    'scripts/init_runtime.py', 'scripts/validate_project_outputs.py', 'scripts/render_emotion_map.py',
    'scripts/render_storyboard.py', 'scripts/validate_cineweaver_storyboard.py', 'scripts/render_asset_library.py',
    'scripts/build_exports.py', 'scripts/run_pipeline.py', 'scripts/skill_integrity.py', 'scripts/verify_release.py',
    'scripts/master_orchestrator.py', 'scripts/compile_forge_handoff.py', 'scripts/verify_master_fusion.py',
    'examples/sample_project/README.md', 'examples/sample_project/storyboard/SAMPLE_STORYBOARD.json',
    'schemas/project_brief.schema.json', 'schemas/production_ledger.schema.json', 'schemas/story_authority.schema.json',
    'schemas/information_ledger.schema.json', 'schemas/production_unit_packet.schema.json',
    'schemas/audience_emotion_architecture.schema.json', 'schemas/cineweaver_storyboard_result.schema.json',
    'schemas/cineweaver_asset_library.schema.json', 'schemas/master_orchestrator_state.schema.json',
    'references/forge/design.md', 'references/forge/human-truth-screenwriter.md', 'references/forge/gate.md',
    'references/forge/audit.md', 'references/forge/emotion-renderer.md', 'references/forge/SOURCE_PROVENANCE.json',
    'references/model-profiles/HIGGSFIELD_MODEL_SURFACES.json', 'references/model-profiles/SOURCE_PROVENANCE.md',
    'references/cineweaver/Shot_Segment_Engine_V1.3/runtime/SEEDANCE_2_0_PROFILE.md',
    'references/cineweaver/Shot_Segment_Engine_V1.3/runtime/SEEDANCE_2_5_PROFILE.md',
    'references/cineweaver/Shot_Segment_Engine_V1.3/runtime/FAILURE_PREVENTION.md',
    'scripts/model_preflight.py',
    'schemas/project_scope.schema.json',
    'scripts/project_scope.py',
    'scripts/build_unit_packet.py',
    'scripts/validate_unit_packet.py',
    'schemas/project_asset_requirements.schema.json',
    'schemas/project_asset_baseline.schema.json',
    'scripts/project_asset_baseline.py',
]

ASSET_PROMPT_CONTRACT_EXECUTION_LINKS = [
    'references/cineweaver/Asset_Engine_V4.1/module.md',
    'references/cineweaver/Asset_Engine_V4.1/runtime/IMAGE_PROMPT_POLICY.md',
    'references/modules/asset-production/module.md',
]
ASSET_PROMPT_CONTRACT_REL = 'references/contracts/asset-prompt-contract.md'


def validate_skill_root(root: str | Path, verify_integrity: bool = True) -> list[str]:
    root = Path(root).resolve()
    errors: list[str] = []
    if not root.is_dir():
        return [f'skill root not found: {root}']
    skills = list(root.rglob('SKILL.md'))
    if skills != [root / 'SKILL.md']:
        errors.append(f'expected exactly one installable SKILL.md, found {len(skills)}')
    skill_text = (root / 'SKILL.md').read_text(encoding='utf-8') if (root / 'SKILL.md').is_file() else ''
    if 'name: ai-film-director' not in skill_text:
        errors.append('root skill name is not ai-film-director')
    for module in MODULES:
        path = root / 'references' / 'modules' / module / 'module.md'
        if not path.is_file() or not path.read_text(encoding='utf-8').strip():
            errors.append(f'missing AFD module: {module}')
        if f'`{module}`' not in skill_text:
            errors.append(f'master routing does not name AFD module: {module}')
    for engine in CINEWEAVER_ENGINES:
        path = root / 'references' / 'cineweaver' / engine / 'module.md'
        if not path.is_file() or not path.read_text(encoding='utf-8').strip():
            errors.append(f'missing CineWeaver engine module: {engine}')
    for rel in REQUIRED:
        if not (root / rel).is_file():
            errors.append(f'missing required file: {rel}')
    for rel in ASSET_PROMPT_CONTRACT_EXECUTION_LINKS:
        path = root / rel
        if path.is_file() and ASSET_PROMPT_CONTRACT_REL not in path.read_text(encoding='utf-8'):
            errors.append(f'asset prompt contract execution link missing: {rel}')
    manifest_path = root / 'PACKAGE_MANIFEST.json'
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            if manifest.get('package') != 'ai-film-director':
                errors.append('manifest package mismatch')
            if manifest.get('internal_modules') != MODULES:
                errors.append('manifest internal_modules mismatch')
            if manifest.get('cineweaver_engines') != CINEWEAVER_ENGINES:
                errors.append('manifest cineweaver_engines mismatch')
            if manifest.get('edition') != 'AI-Film-Director-4.7.1-Fusion':
                errors.append('manifest edition mismatch')
            if manifest.get('fusion_build') != 'AFD-Master-Orchestrator-Forge-v1.1':
                errors.append('manifest fusion_build mismatch')
            if manifest.get('master_orchestrator') != 'scripts/master_orchestrator.py':
                errors.append('manifest master_orchestrator mismatch')
            if manifest.get('forge_source_version') != 'v1.1.4':
                errors.append('manifest Forge source version mismatch')
            if manifest.get('emotion_truth_source') != 'state/forge_locked_audit.json':
                errors.append('manifest emotion truth source mismatch')
            if manifest.get('fusion_reverse_audit') != 'scripts/verify_master_fusion.py':
                errors.append('manifest fusion reverse audit mismatch')
            expected_v470 = {
                'project_scope_schema': 'schemas/project_scope.schema.json',
                'project_scope_builder': 'scripts/project_scope.py',
                'production_unit_packet_builder': 'scripts/build_unit_packet.py',
                'production_unit_packet_validator': 'scripts/validate_unit_packet.py',
                'project_asset_requirements_schema': 'schemas/project_asset_requirements.schema.json',
                'project_asset_baseline_schema': 'schemas/project_asset_baseline.schema.json',
                'project_asset_baseline_validator': 'scripts/project_asset_baseline.py',
                'project_hard_qc': 'scripts/hard_delivery_qc.py',
            }
            for key, expected in expected_v470.items():
                if manifest.get(key) != expected:
                    errors.append(f'manifest 4.7 contract mismatch: {key}')
            for legacy_key in ('asset_engine_source_directory_label', 'shot_segment_engine_source_directory_label'):
                if legacy_key in manifest:
                    errors.append(f'manifest legacy version-label workaround is forbidden: {legacy_key}')
            if manifest.get('integrity_manifest') != 'MANIFEST.sha256':
                errors.append('manifest integrity_manifest mismatch')
        except Exception as exc:
            errors.append(f'invalid manifest: {exc}')
    if verify_integrity and (root / 'MANIFEST.sha256').is_file():
        ok, problems = verify_manifest(root)
        if not ok:
            errors.extend(f'integrity: {problem}' for problem in problems)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate fused single-card AI Film Director Skill package')
    parser.add_argument('--skill-root', default=str(DEFAULT_ROOT))
    parser.add_argument('--skip-integrity', action='store_true')
    args = parser.parse_args()
    errors = validate_skill_root(args.skill_root, verify_integrity=not args.skip_integrity)
    if errors:
        print('FAIL')
        for error in errors:
            print('-', error)
        return 1
    print(f'PASS: single installable skill + {len(MODULES)} AFD modules + {len(CINEWEAVER_ENGINES)} embedded CineWeaver engines')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
