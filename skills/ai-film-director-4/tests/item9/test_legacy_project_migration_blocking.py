from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from init_runtime import create_project


def dump(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def legacy_v2_project(tmp_path: Path) -> Path:
    root = tmp_path / 'legacy_v2'
    (root / 'state').mkdir(parents=True)
    dump(root / 'state' / 'project_brief.json', {
        'project_id': 'LEGACY', 'work_format': 'series', 'episode_count': 1,
        'target_episode_runtime_seconds': 10,
    })
    dump(root / 'state' / 'pipeline_state.json', {
        'project_id': 'LEGACY', 'status': 'PRODUCTION_IN_PROGRESS', 'current_phase': 'shot-segment',
        'current_unit': 'EP01', 'completed_units': [],
    })
    return root


def run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        text=True, capture_output=True, check=False,
    )


def test_new_project_is_stamped_with_current_runtime_contract(tmp_path: Path):
    source = tmp_path / 'source.md'
    source.write_text('SC01\n人物：测试。', encoding='utf-8')
    root = create_project(source, tmp_path / 'projects', 'NEW')

    contract = json.loads((root / 'state' / 'runtime_contract.json').read_text(encoding='utf-8'))
    pipeline = json.loads((root / 'state' / 'pipeline_state.json').read_text(encoding='utf-8'))
    assert contract['runtime_state_version'] == '2.0'
    assert contract['authority_profile'] == 'AFD_CW_SINGLE_AUTHORITY'
    assert pipeline['runtime_state_version'] == '2.0'


def test_unversioned_existing_project_is_blocked_until_migration(tmp_path: Path):
    root = legacy_v2_project(tmp_path)
    result = run('production_ledger.py', 'status', '--project-root', str(root))
    assert result.returncode != 0
    assert 'MIGRATION_REQUIRED' in (result.stdout + result.stderr)


def test_safe_legacy_v2_migration_only_stamps_runtime_state_and_keeps_work(tmp_path: Path):
    root = legacy_v2_project(tmp_path)
    ledger = {
        'schema_version': '1.0', 'project_id': 'LEGACY', 'scope_type': 'episodes', 'status': 'IN_PROGRESS',
        'target_episode_count': 1, 'episodes': [], 'completed_episodes': [],
        'coverage': {'completed_count': 0, 'percentage': 0.0}, 'next_resume': {'episode_id': 'EP01'},
    }
    dump(root / 'PRODUCTION_LEDGER.json', ledger)
    before = (root / 'PRODUCTION_LEDGER.json').read_bytes()

    result = run('migrate_project_state.py', '--project-root', str(root))
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload['status'] == 'MIGRATED'
    assert (root / 'state' / 'runtime_contract.json').is_file()
    pipeline = json.loads((root / 'state' / 'pipeline_state.json').read_text(encoding='utf-8'))
    assert pipeline['runtime_state_version'] == '2.0'
    assert (root / 'PRODUCTION_LEDGER.json').read_bytes() == before
    assert payload['backup_root']
    assert (root / payload['backup_root'] / 'state' / 'pipeline_state.json').is_file()

    status = run('production_ledger.py', 'status', '--project-root', str(root))
    assert status.returncode == 0, status.stdout + status.stderr


def test_known_old_authority_layout_is_not_auto_migrated(tmp_path: Path):
    root = legacy_v2_project(tmp_path)
    dump(root / 'assets' / 'asset_registry.json', {'assets': []})
    before = (root / 'state' / 'pipeline_state.json').read_bytes()

    result = run('migrate_project_state.py', '--project-root', str(root))
    assert result.returncode != 0
    text = result.stdout + result.stderr
    assert 'MIGRATION_BLOCKED' in text
    assert 'asset_registry' in text
    assert not (root / 'state' / 'runtime_contract.json').exists()
    assert (root / 'state' / 'pipeline_state.json').read_bytes() == before


def test_unknown_ledger_schema_version_blocks_migration_without_rewriting(tmp_path: Path):
    root = legacy_v2_project(tmp_path)
    dump(root / 'PRODUCTION_LEDGER.json', {
        'schema_version': '9.9', 'project_id': 'LEGACY', 'scope_type': 'episodes', 'status': 'IN_PROGRESS',
        'coverage': {}, 'next_resume': {},
    })
    before = (root / 'PRODUCTION_LEDGER.json').read_bytes()

    result = run('migrate_project_state.py', '--project-root', str(root))
    assert result.returncode != 0
    assert 'MIGRATION_BLOCKED' in (result.stdout + result.stderr)
    assert 'schema_version' in (result.stdout + result.stderr)
    assert (root / 'PRODUCTION_LEDGER.json').read_bytes() == before


def test_half_new_half_old_state_is_blocked_not_silently_repaired(tmp_path: Path):
    root = legacy_v2_project(tmp_path)
    dump(root / 'state' / 'runtime_contract.json', {
        'runtime_state_version': '2.0', 'authority_profile': 'AFD_CW_SINGLE_AUTHORITY'
    })
    # pipeline_state故意没有runtime_state_version，形成半新半旧。
    result = run('production_ledger.py', 'status', '--project-root', str(root))
    assert result.returncode != 0
    text = result.stdout + result.stderr
    assert 'MIXED_RUNTIME_STATE' in text


def test_current_marker_with_old_authority_artifacts_is_blocked(tmp_path: Path):
    root = legacy_v2_project(tmp_path)
    pipeline = json.loads((root / 'state' / 'pipeline_state.json').read_text(encoding='utf-8'))
    pipeline['runtime_state_version'] = '2.0'
    dump(root / 'state' / 'pipeline_state.json', pipeline)
    dump(root / 'state' / 'runtime_contract.json', {
        'runtime_state_version': '2.0', 'authority_profile': 'AFD_CW_SINGLE_AUTHORITY'
    })
    (root / 'state' / 'storyboard').mkdir(parents=True)
    dump(root / 'state' / 'storyboard' / 'SH001.json', {'shot_id': 'SH001'})

    result = run('production_ledger.py', 'status', '--project-root', str(root))
    assert result.returncode != 0
    assert 'MIXED_RUNTIME_STATE' in (result.stdout + result.stderr)


def test_final_export_cli_blocks_unversioned_project_before_delivery(tmp_path: Path):
    root = legacy_v2_project(tmp_path)
    result = run('build_exports.py', '--project-root', str(root))
    assert result.returncode != 0
    assert 'MIGRATION_REQUIRED' in (result.stdout + result.stderr)


def test_direct_production_ledger_api_cannot_bypass_runtime_version_gate(tmp_path: Path):
    from production_ledger import load_or_initialize
    root = legacy_v2_project(tmp_path)
    with pytest.raises(ValueError, match='MIGRATION_REQUIRED'):
        load_or_initialize(root)


def test_direct_export_api_cannot_bypass_runtime_version_gate(tmp_path: Path):
    from build_exports import build_exports
    root = legacy_v2_project(tmp_path)
    with pytest.raises(ValueError, match='MIGRATION_REQUIRED'):
        build_exports(root)


def test_unknown_story_coverage_schema_version_also_blocks_migration(tmp_path: Path):
    root = legacy_v2_project(tmp_path)
    dump(root / 'state' / 'STORY_COVERAGE_LEDGER.json', {
        'schema_version': '9.9', 'project_id': 'LEGACY', 'enabled': True,
        'story_atoms': [], 'scenes': [], 'dialogues': [], 'information': [],
    })
    result = run('migrate_project_state.py', '--project-root', str(root))
    assert result.returncode != 0
    text = result.stdout + result.stderr
    assert 'MIGRATION_BLOCKED' in text
    assert 'STORY_COVERAGE_LEDGER.json' in text
    assert 'schema_version' in text
