from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPILER = ROOT / "references/cineweaver/Shot_Segment_Engine_V1.3/runtime/VIDEO_PROMPT_COMPILER.md"
QC = ROOT / "references/cineweaver/Final_QC_Engine_V1.3/runtime/PROMPT_QC.md"


def test_compiler_formalizes_reference_transfer_metadata_without_replacing_existing_roles() -> None:
    text = COMPILER.read_text(encoding="utf-8")
    for token in ("role", "inherits[]", "excludes[]", "fidelity", "fidelity_target"):
        assert token in text
    assert "兼容" in text
    assert "reference_roles" in text


def test_fidelity_is_internal_prompt_metadata_not_provider_parameter() -> None:
    compiler = COMPILER.read_text(encoding="utf-8")
    qc = QC.read_text(encoding="utf-8")
    assert "不是" in compiler and "provider" in compiler.lower() and "参数" in compiler
    assert "full-preserve" in compiler
    assert "partial-preserve" in compiler
    assert "attribute-transfer" in compiler
    assert "loose-guide" in compiler
    assert "attribute-transfer" in compiler and "target" in compiler.lower()
    assert "fidelity" in qc.lower() and "provider" in qc.lower()


def test_reference_role_requires_transfer_and_exclusion_when_contamination_is_plausible() -> None:
    text = COMPILER.read_text(encoding="utf-8")
    assert "负责什么" in text
    assert "不继承什么" in text or "排除什么" in text
