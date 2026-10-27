from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from compile_forge_handoff import compile_design, compile_locked_audit
from master_orchestrator import init_state, pass_stage
from migrate_project_state import migrate_project


def _artifact(root: Path, stage: str) -> str:
    path = root / "stage-artifacts" / f"{stage}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stage, encoding="utf-8")
    return path.relative_to(root).as_posix()


def _reach_locked_audit_handoff(root: Path) -> None:
    candidate = root / "lock_candidates" / "EP01.md"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text("# EP01\nlocked", encoding="utf-8")
    init_state(root, "AUTO_ACCEPT_AFTER_QC")
    for stage in (
        "PROJECT_INTAKE",
        "FORGE_DESIGN",
        "DESIGN_HANDOFF",
        "CREATIVE_BIBLE",
        "SCREENWRITER",
    ):
        pass_stage(root, stage, artifact=_artifact(root, stage))
    pass_stage(root, "FORGE_GATE_QC_DEAI", artifact="lock_candidates/EP01.md")
    pass_stage(root, "FORGE_AUDIT", artifact=_artifact(root, "FORGE_AUDIT"))


def _compatibility_projection() -> dict:
    return {
        "project_title": "T",
        "project_type": "series",
        "axis": {"type": "episode", "max": 1, "unit_label": "集"},
        "summary": {},
        "phases": [
            {
                "phase_id": "P01",
                "range_label": "EP01",
                "start": 1,
                "end": 1,
                "name": "建立",
                "primary_emotion": "不安",
                "entry_intensity": 2,
                "peak_intensity": 5,
                "exit_intensity": 4,
            }
        ],
        "nodes": [],
        "fatigue_zones": [],
        "paragraphs": [],
        "actor_emotion_tracks": [
            {
                "character_id": "C1",
                "character_name": "甲",
                "points": [
                    {
                        "position": 1,
                        "intensity": 4,
                        "internal_emotion": "不安",
                        "performed_emotion": "先收起钥匙",
                        "strategy": "回避",
                        "event_basis": "SC01",
                    }
                ],
            }
        ],
    }


def _payload(*, unit_id: str = "EP01", scene_id: str = "SC01") -> dict:
    return {
        "meta": {
            "title": "TEST",
            "runtime": "10s",
            "precision": "SCRIPT_FINE",
            "workflow_stage": "locked_audit",
            "format": "short",
            "quality_route": "STANDARD",
            "blueprint_version": "B1",
        },
        "fact_boundary": {"locked": [], "supported": [], "proposed": [], "verify": []},
        "canonical_names": [],
        "rhythm_causality": [],
        "characters": [],
        "relationship_shifts": [],
        "audience_path": [],
        "breakpoints": [],
        "unknowns": [],
        "directions": [],
        "production_packet": {
            "scope": "unit",
            "incoming_state": {},
            "required_event": [],
            "character_interpretations": [],
            "relationship_transmission": [],
            "audience_knowledge": {},
            "debts_in": [],
            "required_irreversible_change": [],
            "next_unit_interface": {},
        },
        "state_delta": {
            "new_facts": [],
            "knowledge_changes": [],
            "character_changes": [],
            "relationship_debt_changes": [],
            "opened_loops": [],
            "closed_loops": [],
            "last_irreversible_change": "none",
            "next_unit": "none",
        },
        "script_audit": {
            "source_script_version": "S1",
            "precision": "SCRIPT_FINE",
            "causality_findings": [],
            "continuity_findings": [],
            "audience_findings": [],
            "repair_scope": [],
            "lock_status": "LOCKED",
            "blueprint_evidence_diff": [],
        },
        "long_form": {"continuation_ledger": {}},
        "handoff": {
            "premise": "x",
            "human_question": "x",
            "competing_values": [],
            "motifs": [],
            "ending_aftertaste": "x",
            "next_ai_prompt": "x",
        },
        "narrative_topology": {
            "continuity_mode": "continuous",
            "story_time_basis": "story order",
            "audience_time_basis": "screen order",
            "notes": [],
        },
        "audience_lenses": [
            {
                "id": "AUD1",
                "label": "整体观众",
                "perspective": "整体观看立场",
                "question_lens": "发生了什么",
                "evidence_refs": [],
            }
        ],
        "phase_events": [
            {
                "id": "P01",
                "label": "建立",
                "scope_label": "全片",
                "state_change_reason": "初始状态",
                "summary": "建立",
                "confidence": "high",
                "trigger": "开场",
                "story_order": 1,
                "audience_order": 1,
                "character_states": [],
                "audience_states": [],
                "relationship_changes": [],
                "irreversible_changes": [],
                "evidence_refs": [],
            }
        ],
        "phase_links": [],
        "global_emotional_arc": {
            "summary": "总谱",
            "ending_residue": "余味",
            "aggregation_policy": "derive_from_phase_states",
            "phase_ids": ["P01"],
            "major_turns": [],
        },
        "integration": {
            "afd": {
                "unit_id": unit_id,
                "locked_screenplay_path": "lock_candidates/EP01.md",
                "script_version": "S1",
                "script_review_markdown": "# review\nPASS",
                "story_authority": {
                    "atoms": [
                        {
                            "atom_id": "A1",
                            "unit_id": "EP01",
                            "scene_id": "SC01",
                            "type": "action",
                            "content": "门被关上",
                            "locked": True,
                        }
                    ]
                },
                "information_ledger": {
                    "items": [
                        {
                            "info_id": "I1",
                            "truth": "钥匙在抽屉",
                            "character_knowledge": {},
                            "audience_state": {},
                            "reveal_stage": "LATENT",
                            "status": "HIDDEN",
                        }
                    ]
                },
                "audience_emotion_compat_projection": _compatibility_projection(),
                "scene_handoffs": [
                    {
                        "scene_id": scene_id,
                        "story_atom_refs": ["A1"],
                        "information_refs": ["I1"],
                        "must_be_perceptible": ["门被关上"],
                        "must_remain_implicit": ["钥匙存在"],
                        "must_not_be_revealed": ["钥匙在抽屉"],
                        "key_reaction_requests": ["甲停顿"],
                        "key_listener_or_third_party_response": [],
                        "environmental_pressure_or_release": ["门响"],
                        "important_object_or_space_evidence": ["抽屉保持不可读"],
                        "emotion_capacity_note": "SUPPORTED",
                    }
                ],
            }
        },
    }


def test_stage_pass_rejects_missing_artifact(tmp_path: Path) -> None:
    init_state(tmp_path)
    try:
        pass_stage(tmp_path, "PROJECT_INTAKE", artifact="missing.json")
    except ValueError as exc:
        assert "STAGE_ARTIFACT" in str(exc)
    else:
        raise AssertionError("a stage must not pass with a missing artifact")


def test_design_bridge_accepts_canonical_state_forge_design_source(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    design = state / "forge_design.json"
    design.write_text(
        json.dumps(
            {
                "meta": {"workflow_stage": "design", "blueprint_version": "B1"},
                "integration": {"afd": {"creative_bible_story_markdown": "## 故事\n权威源"}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    visual = state / "afd_visual_production.md"
    visual.write_text("## 视觉\n写实", encoding="utf-8")
    init_state(tmp_path)
    pass_stage(tmp_path, "PROJECT_INTAKE", artifact=visual.relative_to(tmp_path).as_posix())
    pass_stage(tmp_path, "FORGE_DESIGN", artifact=design.relative_to(tmp_path).as_posix())
    result = compile_design(tmp_path, design, visual)
    assert result["design_sha256"]
    assert (tmp_path / "PROJECT_CREATIVE_BIBLE.md").is_file()


def test_bridge_rejects_unsafe_unit_id_without_writing_outside_project(tmp_path: Path) -> None:
    _reach_locked_audit_handoff(tmp_path)
    escaped_name = f"escaped_{tmp_path.name}"
    source = tmp_path / "audit.json"
    source.write_text(json.dumps(_payload(unit_id=f"../../{escaped_name}"), ensure_ascii=False), encoding="utf-8")
    try:
        compile_locked_audit(tmp_path, source)
    except ValueError as exc:
        assert "unit_id" in str(exc)
    else:
        raise AssertionError("unsafe unit_id must be rejected")
    assert not (tmp_path.parent / f"{escaped_name}_LOCKED_SCREENPLAY.md").exists()


def test_bridge_validates_projection_shapes_and_references_before_writing(tmp_path: Path) -> None:
    _reach_locked_audit_handoff(tmp_path)
    bad = _payload()
    bad["integration"]["afd"]["story_authority"] = {}
    source = tmp_path / "audit.json"
    source.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    try:
        compile_locked_audit(tmp_path, source)
    except ValueError as exc:
        assert "story_authority" in str(exc)
    else:
        raise AssertionError("invalid AFD projections must be rejected")
    assert not (tmp_path / "state" / "forge_locked_audit.json").exists()
    assert not (tmp_path / "screenplay" / "EP01_LOCKED_SCREENPLAY.md").exists()


def test_bridge_failure_leaves_no_partial_formal_outputs(tmp_path: Path) -> None:
    _reach_locked_audit_handoff(tmp_path)
    source = tmp_path / "audit.json"
    source.write_text(json.dumps(_payload(scene_id=""), ensure_ascii=False), encoding="utf-8")
    try:
        compile_locked_audit(tmp_path, source)
    except ValueError:
        pass
    else:
        raise AssertionError("empty scene_id must fail")
    for relative in (
        "state/forge_locked_audit.json",
        "screenplay/EP01_LOCKED_SCREENPLAY.md",
        "SCRIPT_REVIEW.md",
        "state/story_authority.json",
    ):
        assert not (tmp_path / relative).exists(), relative


def test_alignment_detects_derived_artifact_tampering(tmp_path: Path) -> None:
    _reach_locked_audit_handoff(tmp_path)
    source = tmp_path / "audit.json"
    source.write_text(json.dumps(_payload(), ensure_ascii=False), encoding="utf-8")
    compile_locked_audit(tmp_path, source)
    (tmp_path / "state" / "story_authority.json").write_text('{"atoms": []}', encoding="utf-8")
    from compile_forge_handoff import validate_alignment

    errors = validate_alignment(tmp_path)
    assert any("story_authority.json" in item for item in errors)


def test_current_pre_fusion_project_is_not_reported_as_migration_noop(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    (state / "runtime_contract.json").write_text(
        json.dumps({"runtime_state_version": "2.0", "authority_profile": "AFD_CW_SINGLE_AUTHORITY"}),
        encoding="utf-8",
    )
    (state / "pipeline_state.json").write_text(
        json.dumps({"runtime_state_version": "2.0"}), encoding="utf-8"
    )
    result = migrate_project(tmp_path)
    assert result["status"] == "MIGRATION_BLOCKED"
    assert any("master_orchestrator" in item for item in result["errors"])
