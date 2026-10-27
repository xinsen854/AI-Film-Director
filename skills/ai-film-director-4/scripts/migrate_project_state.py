#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from runtime_state import (
    AUTHORITY_PROFILE,
    CURRENT_RUNTIME_STATE_VERSION,
    PIPELINE_STATE_REL,
    RUNTIME_CONTRACT_REL,
    _legacy_authority_hits,
    _load_object,
    _schema_blockers,
    inspect_runtime_state,
)


def _dump(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def migrate_project(project_root: str | Path) -> dict:
    root = Path(project_root).resolve()
    if not root.is_dir():
        return {'status': 'MIGRATION_BLOCKED', 'errors': [f'项目目录不存在：{root}'], 'changed_files': []}

    current = inspect_runtime_state(root)
    master_path = root / 'state' / 'master_orchestrator.json'
    if current.get('status') == 'CURRENT' and not master_path.is_file():
        return {
            'status': 'MIGRATION_BLOCKED',
            'errors': [
                '缺少 state/master_orchestrator.json；该项目属于 Master+Forge 融合前运行状态，'
                '无法在不重建 Forge DESIGN/锁稿 AUDIT 语义的情况下自动迁移'
            ],
            'changed_files': [],
        }
    if current.get('status') == 'CURRENT':
        return {'status': 'NOOP', 'runtime_state_version': CURRENT_RUNTIME_STATE_VERSION, 'changed_files': []}
    # 已经声明当前合同却混有旧状态，禁止自动修复，避免把半新半旧项目伪装成安全。
    if current.get('status') == 'MIXED_RUNTIME_STATE':
        return {'status': 'MIGRATION_BLOCKED', 'errors': current.get('errors', []), 'changed_files': []}

    blockers: list[str] = []
    pipeline_path = root / PIPELINE_STATE_REL
    pipeline = _load_object(pipeline_path)
    if pipeline is None:
        blockers.append('缺少或无法解析 state/pipeline_state.json')

    legacy_hits = _legacy_authority_hits(root)
    if legacy_hits:
        blockers.append('旧权威结构无法自动迁移到2.0单一权威：' + ', '.join(legacy_hits))
    blockers.extend(_schema_blockers(root))

    contract_path = root / RUNTIME_CONTRACT_REL
    contract = _load_object(contract_path)
    if contract is not None:
        version = str(contract.get('runtime_state_version') or '').strip()
        if version not in {'', '1.0', CURRENT_RUNTIME_STATE_VERSION}:
            blockers.append(f'未知 runtime_state_version={version}，禁止猜测迁移')

    if blockers:
        return {'status': 'MIGRATION_BLOCKED', 'errors': blockers, 'changed_files': []}

    assert pipeline is not None
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup_root = root / 'state' / 'migration_backups' / stamp
    backup_pipeline = backup_root / PIPELINE_STATE_REL
    backup_pipeline.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pipeline_path, backup_pipeline)
    if contract_path.is_file():
        backup_contract = backup_root / RUNTIME_CONTRACT_REL
        backup_contract.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(contract_path, backup_contract)

    new_pipeline = dict(pipeline)
    new_pipeline['runtime_state_version'] = CURRENT_RUNTIME_STATE_VERSION
    _dump(pipeline_path, new_pipeline)
    _dump(contract_path, {
        'runtime_state_version': CURRENT_RUNTIME_STATE_VERSION,
        'authority_profile': AUTHORITY_PROFILE,
    })
    return {
        'status': 'MIGRATED',
        'runtime_state_version': CURRENT_RUNTIME_STATE_VERSION,
        'changed_files': [str(PIPELINE_STATE_REL), str(RUNTIME_CONTRACT_REL)],
        'backup_root': str(backup_root.relative_to(root)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Safely migrate legacy project runtime state into the 2.0 single-authority contract')
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()
    result = migrate_project(args.project_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get('status') in {'MIGRATED', 'NOOP'} else 2


if __name__ == '__main__':
    raise SystemExit(main())
