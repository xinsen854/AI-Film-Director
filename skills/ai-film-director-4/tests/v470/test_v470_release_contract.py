from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]


def test_v470_version_and_manifest_contract():
    skill=(ROOT/'SKILL.md').read_text(encoding='utf-8')
    agent=(ROOT/'agents/openai.yaml').read_text(encoding='utf-8')
    manifest=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    assert 'version: "4.7.1-fusion"' in skill
    assert '# AI Film Director 4.7.1 Fusion' in skill
    assert manifest['edition']=='AI-Film-Director-4.7.1-Fusion'
    assert manifest['package_version']=='4.7.1-fusion'
    assert 'AI Film Director 4.7.1 Fusion' in agent


def test_v470_manifest_registers_project_scope_unit_packet_and_asset_baseline():
    manifest=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    expected={
      'project_scope_schema':'schemas/project_scope.schema.json',
      'project_scope_builder':'scripts/project_scope.py',
      'production_unit_packet_builder':'scripts/build_unit_packet.py',
      'production_unit_packet_validator':'scripts/validate_unit_packet.py',
      'project_asset_requirements_schema':'schemas/project_asset_requirements.schema.json',
      'project_asset_baseline_schema':'schemas/project_asset_baseline.schema.json',
      'project_asset_baseline_validator':'scripts/project_asset_baseline.py',
      'project_hard_qc':'scripts/hard_delivery_qc.py',
    }
    for key,value in expected.items():
        assert manifest.get(key)==value


def test_v470_package_validator_requires_new_project_scope_files():
    text=(ROOT/'scripts/validate_skill_package.py').read_text(encoding='utf-8')
    for token in [
      'schemas/project_scope.schema.json','scripts/project_scope.py',
      'scripts/build_unit_packet.py','scripts/validate_unit_packet.py',
      'schemas/project_asset_requirements.schema.json','schemas/project_asset_baseline.schema.json',
      'scripts/project_asset_baseline.py',
    ]:
        assert token in text


def test_v470_master_state_schema_registers_real_project_loop_fields():
    schema=json.loads((ROOT/'schemas/master_orchestrator_state.schema.json').read_text(encoding='utf-8'))
    props=schema['properties']
    for key in ['project_scope_active','project_stage','scope_manifest_sha256','planned_units','completed_units','current_unit_id','unit_stage','project_asset_requirements_sha256','project_asset_baseline_lock_sha256']:
        assert key in props
