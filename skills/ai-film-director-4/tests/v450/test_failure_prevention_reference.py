from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "references/cineweaver/Shot_Segment_Engine_V1.3"
FAILURE = ENGINE / "runtime/FAILURE_PREVENTION.md"


def test_failure_prevention_reference_exists_with_provenance_strengths() -> None:
    text = FAILURE.read_text(encoding="utf-8")
    assert "PLATFORM" in text
    assert "MODEL_DIALECT" in text
    assert "FIELD_HEURISTIC" in text
    assert "不得" in text and "全局硬" in text


def test_failure_prevention_covers_initial_p0_failure_classes() -> None:
    text = FAILURE.read_text(encoding="utf-8")
    for phrase in (
        "source/keyframe",
        "adjacent-object",
        "action reversal",
        "dominant camera",
        "spatial geometry",
        "completion endpoint",
    ):
        assert phrase.lower() in text.lower()


def test_shot_segment_and_prompt_qc_link_failure_prevention_without_new_owner() -> None:
    module = (ENGINE / "module.md").read_text(encoding="utf-8")
    qc = (ROOT / "references/cineweaver/Final_QC_Engine_V1.3/runtime/PROMPT_QC.md").read_text(encoding="utf-8")
    assert "FAILURE_PREVENTION.md" in module
    assert "FAILURE_PREVENTION.md" in qc
    assert "不新增 Owner" in qc or "不形成新 Owner" in qc
