from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import validate_unit_consistency as consistency


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _state(root: Path, maturity: str) -> None:
    path = root / 'state' / 'pipeline_state.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'source_maturity': maturity}, ensure_ascii=False), encoding='utf-8')


def _run(root: Path) -> list[str]:
    validator = getattr(consistency, '_validate_mature_screenplay_source_lock', None)
    assert validator is not None, '缺少成熟剧本原文保护硬校验器'
    errors: list[str] = []
    validator(root, 'FILM', errors)
    return errors


SOURCE = '''# 《测试片》\n\n**类型：**现实剧情\n\n## SC01｜店内｜清晨｜内\n\n许程走来。\n\n没有说话。\n\n扶住凳子。\n\n许国安又试了一次。\n\n还是没解开。\n\n**许程**\n我来。\n\n许国安让开。\n'''


def test_screenplay_maturity_rejects_unauthorized_action_order_change(tmp_path: Path):
    root = tmp_path / 'project'
    _state(root, 'screenplay')
    _write(root, 'source/normalized_input.md', SOURCE)
    _write(root, 'SCRIPT_REVIEW.md', '# 剧本审查\n\n## 已经合法处理的修改\n\n- 无。\n')
    _write(root, 'screenplay/FILM_LOCKED_SCREENPLAY.md', '''# FILM｜正式编剧剧本\n\n## SC01｜店内｜清晨｜内\n\n### 正式剧本正文\n许程走来。\n\n没有说话。\n\n扶住凳子。\n\n**许程**\n我来。\n\n许国安又试了一次。\n\n还是没解开。\n\n许国安让开。\n''')

    errors = _run(root)

    assert errors
    assert any('成熟剧本' in e and ('顺序' in e or '未经审查' in e or '原文' in e) for e in errors)


def test_screenplay_maturity_allows_explicitly_reviewed_action_order_change(tmp_path: Path):
    root = tmp_path / 'project'
    _state(root, 'screenplay')
    _write(root, 'source/normalized_input.md', SOURCE)
    _write(root, 'SCRIPT_REVIEW.md', '''# 剧本审查\n\n## 已经合法处理的修改\n\n- SC01 顺序调整授权：原文“许国安又试了一次。”移动到“我来。”之后；原因：已在本轮剧本审查中明确批准。\n''')
    _write(root, 'screenplay/FILM_LOCKED_SCREENPLAY.md', '''# FILM｜正式编剧剧本\n\n## SC01｜店内｜清晨｜内\n\n### 正式剧本正文\n许程走来。\n\n没有说话。\n\n扶住凳子。\n\n**许程**\n我来。\n\n许国安又试了一次。\n\n还是没解开。\n\n许国安让开。\n''')

    errors = _run(root)

    assert errors == []


def test_non_screenplay_maturity_is_not_overrestricted(tmp_path: Path):
    root = tmp_path / 'project'
    _state(root, 'outline')
    _write(root, 'source/normalized_input.md', SOURCE)
    _write(root, 'SCRIPT_REVIEW.md', '# 剧本审查\n')
    _write(root, 'screenplay/FILM_LOCKED_SCREENPLAY.md', '''# FILM｜正式编剧剧本\n\n## SC01｜店内｜清晨｜内\n\n### 正式剧本正文\n这里允许从大纲创作成完整场景。\n''')

    errors = _run(root)

    assert errors == []
