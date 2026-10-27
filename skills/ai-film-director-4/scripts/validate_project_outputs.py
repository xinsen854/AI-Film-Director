#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from render_asset_library import validate_asset_library_payload
from render_storyboard import validate_storyboard_payload
from validate_unit_consistency import validate_project_consistency


def _load_object(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _require_file(path: Path, label: str, errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f'缺少{label}：{path}')
        return
    if not path.read_text(encoding='utf-8', errors='ignore').strip():
        errors.append(f'{label}为空：{path}')


def _validate_project_level(root: Path, errors: list[str]) -> None:
    for relative, label in [
        ('PROJECT_BRIEF.md', '项目Brief'),
        ('PROJECT_CREATIVE_BIBLE.md', '项目创作母版'),
        ('SCRIPT_REVIEW.md', '剧本审查结果'),
        ('AUDIENCE_EMOTION_MAP.html', 'Forge观众情绪HTML'),
        ('state/forge_locked_audit.json', 'Forge锁稿审计'),
        ('state/forge_alignment.json', 'Forge/AFD对齐状态'),
        ('state/audience_emotion_architecture.json', 'AFD兼容情绪投影'),
        ('assets/ASSET_LIBRARY.json', '唯一资产权威JSON'),
        ('assets/ASSET_LIBRARY.md', '资产总表与详细生成提示词'),
    ]:
        _require_file(root / relative, label, errors)

    brief = _load_object(root / 'state' / 'project_brief.json')
    if brief is None:
        errors.append('缺少或无法解析已确认项目Brief：state/project_brief.json')

    asset_payload = _load_object(root / 'assets' / 'ASSET_LIBRARY.json')
    if asset_payload is not None:
        errors.extend(f'ASSET_LIBRARY：{e}' for e in validate_asset_library_payload(asset_payload))


def _validate_unit(root: Path, unit_id: str, errors: list[str]) -> None:
    _require_file(root / 'screenplay' / f'{unit_id}_LOCKED_SCREENPLAY.md', '正式编剧剧本', errors)
    _require_file(root / 'director' / f'{unit_id}_INTEGRATED_DIRECTOR_SCREENPLAY.md', '整合导演剧本', errors)
    _require_file(root / 'storyboard' / f'{unit_id}_STORYBOARD.json', '结构化SH/GU/PH分镜', errors)
    _require_file(root / 'storyboard' / f'{unit_id}_STORYBOARD.md', '正式分镜与视频生成Prompt', errors)

    payload = _load_object(root / 'storyboard' / f'{unit_id}_STORYBOARD.json')
    if payload is not None:
        errors.extend(f'{unit_id} Storyboard：{e}' for e in validate_storyboard_payload(payload))


def validate_project(project_root: str | Path, unit_id: str | None = None) -> list[str]:
    root = Path(project_root).resolve()
    if not root.is_dir():
        return [f'项目目录不存在：{root}']
    errors: list[str] = []
    _validate_project_level(root, errors)
    if unit_id:
        _validate_unit(root, unit_id, errors)
    errors.extend(validate_project_consistency(root, unit_id))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate fused project outputs without legacy per-SHOT prompt files or character-count budgets')
    parser.add_argument('--project-root', required=True)
    parser.add_argument('--unit-id')
    args = parser.parse_args()
    errors = validate_project(args.project_root, args.unit_id)
    if errors:
        print('FAIL')
        for item in errors:
            print('-', item)
        return 1
    print('PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
