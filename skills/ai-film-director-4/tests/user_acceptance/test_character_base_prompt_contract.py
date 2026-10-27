from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "references" / "contracts" / "asset-prompt-contract.md"


def test_character_base_prompt_is_replaced_by_approved_three_image_template() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    base_section = text.split("# 二、人物基础资产Prompt", 1)[1].split(
        "# 三、人物状态资产Prompt", 1
    )[0]

    for token in (
        "画面一：大型3/4面部身份近景",
        "画面二：正面完整身体参考，从颈部以下至脚部",
        "故意不显示头部",
        "画面三：背面完整身体参考",
        "中性灰色背景，平坦均匀照明",
        "真实未经修饰的皮肤，清晰可见毛孔和自然肤色差异",
        "不使用胶片颗粒，不磨皮，不美颜，不添加文字",
        "所有画面表现同一个人物",
    ):
        assert token in base_section

    for obsolete_heading in (
        "## 1. 身体与比例",
        "## 2. 面部身份",
        "## 3. 头发",
        "## 4. 基础服装",
        "## 5. 身体气质",
        "## 6. 生物学亲属相似性（只有剧情明确时）",
        "## 7. 多视图板",
    ):
        assert obsolete_heading not in base_section


def test_character_state_prompt_contract_is_preserved() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    state_section = text.split("# 三、人物状态资产Prompt", 1)[1].split(
        "# 四、场景基础资产Prompt", 1
    )[0]

    for token in (
        "继承自：Axxx",
        "上一状态：",
        "然后只写Delta",
        "### 淋湿示例维度",
    ):
        assert token in state_section
