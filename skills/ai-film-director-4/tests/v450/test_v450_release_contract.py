from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_release_contract_names_450_model_preflight_and_fresh_zip_gate() -> None:
    text = (ROOT / "references/contracts/release-validation-contract.md").read_text(encoding="utf-8")
    assert "4.7.1" in text
    assert "model_preflight.py" in text
    assert "HIGGSFIELD_MODEL_SURFACES.json" in text
    assert "verify_release.py --zip-file" in text


def test_verify_release_identifies_450_release() -> None:
    text = (ROOT / "scripts/verify_release.py").read_text(encoding="utf-8")
    assert "AI Film Director 4.7.1 Fusion" in text


def test_450_remains_prompt_planning_skill_not_video_api_runtime() -> None:
    manifest = json.loads((ROOT / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    boundary = manifest["media_execution_boundary"]
    assert boundary["direct_video_generation"] is False
    assert boundary["direct_tts_or_final_audio_generation"] is False
    assert not (ROOT / "scripts/generation_runtime.py").exists()
    assert not (ROOT / "scripts/take_review.py").exists()
    assert not (ROOT / "scripts/provider_client.py").exists()


def test_450_release_keeps_eight_delivery_files_unchanged() -> None:
    manifest = json.loads((ROOT / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["delivery_files"] == [
        "01_项目需求确认单.md",
        "02_剧本审查与修改结论.md",
        "03_正式编剧剧本.md",
        "04_整合导演剧本.md",
        "05_双层情绪规划图.html",
        "06_资产总表与详细生成提示词.md",
        "07_正式分镜与视频模型最终Prompt.md",
        "08_Story_Coverage_Ledger.html",
    ]


def test_package_validator_requires_new_450_adapter_and_prevention_files(tmp_path: Path) -> None:
    import shutil
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from validate_skill_package import validate_skill_root

    for rel in (
        "references/cineweaver/Shot_Segment_Engine_V1.3/runtime/SEEDANCE_2_0_PROFILE.md",
        "references/cineweaver/Shot_Segment_Engine_V1.3/runtime/SEEDANCE_2_5_PROFILE.md",
        "references/cineweaver/Shot_Segment_Engine_V1.3/runtime/FAILURE_PREVENTION.md",
    ):
        clone = tmp_path / rel.split("/")[-1]
        shutil.copytree(ROOT, clone, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        (clone / rel).unlink()
        errors = validate_skill_root(clone, verify_integrity=False)
        assert any(f"missing required file: {rel}" in error for error in errors), errors
