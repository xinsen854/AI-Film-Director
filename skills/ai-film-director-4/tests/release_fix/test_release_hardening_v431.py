from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_dependencies_are_declared_for_runtime_and_tests() -> None:
    runtime = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    testing = (ROOT / "requirements-test.txt").read_text(encoding="utf-8")
    assert "standard library" in runtime
    assert "pytest" in testing
    assert "Pillow" in testing


def test_one_click_pipeline_has_a_working_help_entrypoint() -> None:
    script = ROOT / "scripts" / "run_pipeline.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=str(ROOT), text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "--project-root" in result.stdout


def test_project_brief_supports_full_and_quick_execution_modes() -> None:
    schema = json.loads((ROOT / "schemas" / "project_brief.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["execution_mode"]["enum"] == ["FULL", "QUICK"]
    assert schema["properties"]["music_strategy"]["enum"] == ["NO_BGM", "LOCKED_CUE", "DESIGN_ALLOWED"]
    assert schema["properties"]["delivery_target"]["enum"] == ["PLANNING_AND_PROMPTS", "PLANNING_PROMPTS_AND_IMAGES"]


def test_golden_sample_documents_variable_story_driven_timing() -> None:
    sample = ROOT / "examples" / "sample_project"
    assert (sample / "README.md").is_file()
    storyboard = json.loads((sample / "storyboard" / "SAMPLE_STORYBOARD.json").read_text(encoding="utf-8"))
    durations = [shot["edit_shot_duration"] for shot in storyboard["edit_shots"]]
    assert sum(durations) == 30.0
    assert len(set(durations)) > 1
    assert all("duration_basis" in shot for shot in storyboard["edit_shots"])
