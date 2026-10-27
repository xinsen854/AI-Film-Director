#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

CURRENT_RUNTIME_STATE_VERSION = '2.0'
AUTHORITY_PROFILE = 'AFD_CW_SINGLE_AUTHORITY'
RUNTIME_CONTRACT_REL = Path('state/runtime_contract.json')
PIPELINE_STATE_REL = Path('state/pipeline_state.json')

# 这些路径来自旧融合架构；当前2.0单一权威运行链不使用它们。
LEGACY_AUTHORITY_PATHS = (
    Path('assets/asset_registry.json'),
    Path('state/asset_registry.json'),
    Path('state/storyboard'),
    Path('prompts'),
)
SUPPORTED_SCHEMA_VERSIONS = {
    Path('PRODUCTION_LEDGER.json'): {'1.0'},
    Path('state/STORY_COVERAGE_LEDGER.json'): {'1.0'},
}


def _load_object(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _legacy_authority_hits(root: Path) -> list[str]:
    hits: list[str] = []
    for rel in LEGACY_AUTHORITY_PATHS:
        path = root / rel
        if path.is_file():
            hits.append(str(rel))
        elif path.is_dir() and any(path.iterdir()):
            hits.append(str(rel))
    return hits


def _schema_blockers(root: Path) -> list[str]:
    errors: list[str] = []
    for rel, allowed in SUPPORTED_SCHEMA_VERSIONS.items():
        path = root / rel
        if not path.is_file():
            continue
        data = _load_object(path)
        if data is None:
            errors.append(f'{rel} 无法解析为对象')
            continue
        version = str(data.get('schema_version') or '').strip()
        if version not in allowed:
            errors.append(f'{rel} schema_version={version or "<missing>"} 不兼容，支持={sorted(allowed)}')
    return errors


def inspect_runtime_state(project_root: str | Path) -> dict:
    root = Path(project_root).resolve()
    contract_path = root / RUNTIME_CONTRACT_REL
    pipeline_path = root / PIPELINE_STATE_REL
    contract = _load_object(contract_path)
    pipeline = _load_object(pipeline_path)
    legacy_hits = _legacy_authority_hits(root)
    schema_errors = _schema_blockers(root)

    if contract is None:
        return {
            'status': 'MIGRATION_REQUIRED',
            'runtime_state_version': None,
            'errors': ['缺少 state/runtime_contract.json；旧项目必须先迁移'] + schema_errors,
            'legacy_authority_paths': legacy_hits,
        }

    version = str(contract.get('runtime_state_version') or '').strip()
    profile = str(contract.get('authority_profile') or '').strip()
    if version != CURRENT_RUNTIME_STATE_VERSION or profile != AUTHORITY_PROFILE:
        return {
            'status': 'MIGRATION_REQUIRED' if version in {'', '1.0'} else 'MIGRATION_BLOCKED',
            'runtime_state_version': version or None,
            'errors': [
                f'运行状态合同不兼容：version={version or "<missing>"}, authority_profile={profile or "<missing>"}'
            ] + schema_errors,
            'legacy_authority_paths': legacy_hits,
        }

    mixed: list[str] = []
    if pipeline is None:
        mixed.append('缺少或无法解析 state/pipeline_state.json')
    elif str(pipeline.get('runtime_state_version') or '').strip() != CURRENT_RUNTIME_STATE_VERSION:
        mixed.append(
            'runtime_contract 已是2.0，但 pipeline_state.runtime_state_version 不一致或缺失'
        )
    if legacy_hits:
        mixed.append('检测到旧权威运行产物：' + ', '.join(legacy_hits))
    mixed.extend(schema_errors)
    if mixed:
        return {
            'status': 'MIXED_RUNTIME_STATE',
            'runtime_state_version': version,
            'errors': mixed,
            'legacy_authority_paths': legacy_hits,
        }

    return {
        'status': 'CURRENT',
        'runtime_state_version': CURRENT_RUNTIME_STATE_VERSION,
        'authority_profile': AUTHORITY_PROFILE,
        'errors': [],
        'legacy_authority_paths': [],
    }


def require_current_runtime_state(project_root: str | Path) -> dict:
    result = inspect_runtime_state(project_root)
    if result.get('status') != 'CURRENT':
        details = '; '.join(str(x) for x in result.get('errors', []))
        raise ValueError(f'{result.get("status")}：{details}')
    return result
