from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import validate_unit_consistency as consistency


def _write_pair(tmp_path: Path, screenplay: str, director: str) -> tuple[Path, Path]:
    screenplay_path = tmp_path / 'EP01_LOCKED_SCREENPLAY.md'
    director_path = tmp_path / 'EP01_INTEGRATED_DIRECTOR_SCREENPLAY.md'
    screenplay_path.write_text(screenplay, encoding='utf-8')
    director_path.write_text(director, encoding='utf-8')
    return screenplay_path, director_path


def _run_validator(screenplay_path: Path, director_path: Path) -> list[str]:
    validator = getattr(consistency, '_validate_director_screenplay_inheritance', None)
    assert validator is not None, '缺少03完整继承02正文的硬校验器'
    errors: list[str] = []
    validator(screenplay_path, director_path, 'EP01', errors)
    return errors


def test_director_screenplay_rejects_summary_that_drops_locked_dialogue(tmp_path: Path):
    screenplay_path, director_path = _write_pair(
        tmp_path,
        '''# EP01｜正式编剧剧本\n\n## SC01｜钟表店｜夜｜内\n\n许程坐下。\n\n**许程**\n明天九点二十。\n\n**许国安**\n不去。\n''',
        '''# EP01｜整合导演剧本\n\n# SC01｜钟表店｜夜｜内\n\n## 正式编剧剧本\n医院对白在同一双人关系镜头开始，父亲拒绝去医院。\n\n## 导演执行\n- 保持双人关系。\n''',
    )

    errors = _run_validator(screenplay_path, director_path)

    assert errors
    assert any('完整继承' in error or '缺失' in error or '逐行' in error for error in errors)


def test_director_screenplay_accepts_locked_text_in_order_with_director_annotations(tmp_path: Path):
    screenplay_path, director_path = _write_pair(
        tmp_path,
        '''# EP01｜正式编剧剧本\n\n## SC01｜钟表店｜夜｜内\n\n许程坐下。\n\n**许程**\n明天九点二十。\n\n**许国安**\n不去。\n''',
        '''# EP01｜整合导演剧本\n\n# SC01｜钟表店｜夜｜内\n\n## 正式编剧剧本\n许程坐下。\n\n**许程**\n明天九点二十。\n\n**许国安**\n不去。\n\n## 导演执行\n- Blocking：两人维持桌边距离。\n- 对白表演：父亲回答短促，不加解释。\n''',
    )

    errors = _run_validator(screenplay_path, director_path)

    assert errors == []


def test_director_screenplay_does_not_need_to_duplicate_non_body_screenplay_metadata(tmp_path: Path):
    screenplay_path, director_path = _write_pair(
        tmp_path,
        '''# EP01｜正式编剧剧本\n\n## SC01｜钟表店｜夜｜内\n\n### 场景戏剧任务\n- 谁要什么：儿子要父亲去医院。\n\n### 正式剧本正文\n许程坐下。\n\n**许程**\n明天九点二十。\n\n**许国安**\n不去。\n\n### 场景结果\n- 父亲继续拒绝。\n''',
        '''# EP01｜整合导演剧本\n\n# SC01｜钟表店｜夜｜内\n\n## 正式编剧剧本\n许程坐下。\n\n**许程**\n明天九点二十。\n\n**许国安**\n不去。\n\n## 导演执行\n- Blocking：两人维持桌边距离。\n''',
    )

    errors = _run_validator(screenplay_path, director_path)

    assert errors == []
