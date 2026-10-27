from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_skill_package import validate_skill_root  # type: ignore  # noqa: E402

CONTRACT_REL = "references/contracts/asset-prompt-contract.md"
ASSET_ENGINE = ROOT / "references/cineweaver/Asset_Engine_V4.1/module.md"
PROMPT_POLICY = ROOT / "references/cineweaver/Asset_Engine_V4.1/runtime/IMAGE_PROMPT_POLICY.md"
ASSET_PROD = ROOT / "references/modules/asset-production/module.md"


def test_asset_engine_and_asset_production_explicitly_load_approved_prompt_contract() -> None:
    for path in (ASSET_ENGINE, PROMPT_POLICY, ASSET_PROD):
        text = path.read_text(encoding="utf-8")
        assert CONTRACT_REL in text
    policy = PROMPT_POLICY.read_text(encoding="utf-8")
    assert "故意不显示头部" in policy
    assert "大型3/4面部身份近景" in policy


def test_asset_production_cannot_erase_contract_during_technical_conversion() -> None:
    text = ASSET_PROD.read_text(encoding="utf-8")
    assert "技术转换" in text
    assert "不得删除" in text or "不得移除" in text
    assert "故意不显示头部" in text


def test_package_validator_detects_missing_asset_prompt_execution_link(tmp_path: Path) -> None:
    clone = tmp_path / "skill"
    shutil.copytree(ROOT, clone, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
    target = clone / "references/modules/asset-production/module.md"
    text = target.read_text(encoding="utf-8").replace(CONTRACT_REL, "references/contracts/missing-contract.md")
    target.write_text(text, encoding="utf-8")

    errors = validate_skill_root(clone, verify_integrity=False)
    assert any("asset prompt contract execution link missing" in error for error in errors), errors


def test_current_450_package_has_no_asset_prompt_execution_link_error() -> None:
    errors = validate_skill_root(ROOT, verify_integrity=False)
    assert not any("asset prompt contract execution link missing" in error for error in errors), errors
