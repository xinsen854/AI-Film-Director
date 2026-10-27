#!/usr/bin/env python3
"""Render one emotion-diagnosis JSON payload as a standalone offline HTML file."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path


TOKEN = "REPORT_DATA"
WORKFLOW_STAGES = {"design", "draft", "locked_audit"}
FORMATS = {"feature", "tv", "short", "animation", "branded"}
PRECISIONS = {"OUTLINE_COARSE", "SCRIPT_FINE", "MIXED"}
QUALITY_ROUTES = {"STANDARD", "SERIES", "S-CANDIDATE"}


def _is_nonempty(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple)):
        return bool(value)
    return bool(value)


def _require_object(payload: dict, key: str, errors: list[str]) -> dict:
    value = payload.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} must be an object")
        return {}
    return value


def _require_list(payload: dict, key: str, errors: list[str]) -> list:
    value = payload.get(key)
    if not isinstance(value, list):
        errors.append(f"{key} must be an array")
        return []
    return value


CONFIDENCE_LEVELS = {"high", "medium", "low"}
EVIDENCE_LEVELS = {"EXPLICIT", "SUPPORTED", "INFERRED", "UNKNOWN"}
LINK_FAMILIES = {"SEQUENCE", "BRANCH", "MERGE", "PARALLEL", "RETURN", "REFRAME", "ECHO", "RESET", "INTERRUPT", "CONSEQUENCE", "CUSTOM"}
LAYER_FAMILIES = {"reality", "memory", "subjective", "hypothesis", "recorded", "custom"}


def _validate_emotions(emotions: object, path: str, errors: list[str], palette_ids: set[str]) -> None:
    """Validate open semantic emotions while keeping a stable visual palette.

    Legacy items may use a palette id directly in ``emotion``. New semantic items may
    use any stable semantic id, but must project to the visual palette through
    ``family`` or ``blend``. This keeps analysis vocabulary open without forcing the
    HTML to invent new colors.
    """
    if not isinstance(emotions, list):
        errors.append(f"{path} must be an array")
        return
    total = 0.0
    for index, item in enumerate(emotions, start=1):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path} must be an object")
            continue
        emotion = item.get("emotion")
        weight = item.get("weight")
        if not _is_nonempty(emotion):
            errors.append(f"{item_path}.emotion is required")
        try:
            numeric = float(weight)
        except (TypeError, ValueError):
            errors.append(f"{item_path}.weight must be numeric 0..1")
            continue
        if not 0 <= numeric <= 1:
            errors.append(f"{item_path}.weight must be within 0..1")
        total += numeric

        family = item.get("family")
        blend = item.get("blend")
        direct_palette = bool(_is_nonempty(emotion) and (not palette_ids or str(emotion) in palette_ids))
        if family is not None:
            if not _is_nonempty(family):
                errors.append(f"{item_path}.family must be a non-empty palette id when provided")
            elif palette_ids and str(family) not in palette_ids:
                errors.append(f"{item_path}.family references unknown palette id: {family}")
        if blend is not None:
            if not isinstance(blend, list) or not blend:
                errors.append(f"{item_path}.blend must be a non-empty array when provided")
            else:
                blend_total = 0.0
                for bindex, comp in enumerate(blend, start=1):
                    cpath = f"{item_path}.blend[{bindex}]"
                    if not isinstance(comp, dict):
                        errors.append(f"{cpath} must be an object")
                        continue
                    comp_emotion = comp.get("emotion")
                    if not _is_nonempty(comp_emotion):
                        errors.append(f"{cpath}.emotion is required")
                    elif palette_ids and str(comp_emotion) not in palette_ids:
                        errors.append(f"{cpath}.emotion references unknown palette id: {comp_emotion}")
                    try:
                        comp_weight = float(comp.get("weight"))
                    except (TypeError, ValueError):
                        errors.append(f"{cpath}.weight must be numeric 0..1")
                        continue
                    if not 0 <= comp_weight <= 1:
                        errors.append(f"{cpath}.weight must be within 0..1")
                    blend_total += comp_weight
                if blend_total <= 0:
                    errors.append(f"{item_path}.blend weights must sum to > 0")
                elif blend_total > 1.001:
                    errors.append(f"{item_path}.blend weights must sum to <= 1.0")
        if not direct_palette and not _is_nonempty(family) and not isinstance(blend, list):
            errors.append(f"{item_path} semantic emotion must provide family or blend for visual projection")

        confidence = item.get("confidence")
        if confidence is not None and confidence not in CONFIDENCE_LEVELS:
            errors.append(f"{item_path}.confidence must be high, medium, or low")
        evidence_level = item.get("evidence_level")
        if evidence_level is not None and evidence_level not in EVIDENCE_LEVELS:
            errors.append(f"{item_path}.evidence_level must be one of {sorted(EVIDENCE_LEVELS)}")
        coords = item.get("coordinates")
        if coords is not None:
            if not isinstance(coords, dict):
                errors.append(f"{item_path}.coordinates must be an object")
            else:
                for key, value in coords.items():
                    if key not in {"valence", "arousal", "approach", "agency", "connection", "certainty"}:
                        continue
                    try:
                        coord = float(value)
                    except (TypeError, ValueError):
                        errors.append(f"{item_path}.coordinates.{key} must be numeric -1..1")
                        continue
                    if not -1 <= coord <= 1:
                        errors.append(f"{item_path}.coordinates.{key} must be within -1..1")
    if emotions and total > 1.001:
        errors.append(f"{path} weights must sum to <= 1.0")


def _validate_keyframes(keyframes: object, path: str, errors: list[str], palette_ids: set[str], driver_ids: set[str] | None = None) -> None:
    if not isinstance(keyframes, list):
        errors.append(f"{path} must be an array")
        return
    last_at = -1.0
    allowed_motion = {"cohere", "expand", "contract", "tremor", "drift", "split", "bridge", "hold"}
    for index, frame in enumerate(keyframes, start=1):
        frame_path = f"{path}[{index}]"
        if not isinstance(frame, dict):
            errors.append(f"{frame_path} must be an object")
            continue
        try:
            at = float(frame.get("at"))
        except (TypeError, ValueError):
            errors.append(f"{frame_path}.at must be numeric 0..1")
            continue
        if not 0 <= at <= 1:
            errors.append(f"{frame_path}.at must be within 0..1")
        if at < last_at:
            errors.append(f"{path} at values must be monotonic")
        last_at = at
        if not _is_nonempty(frame.get("label")):
            errors.append(f"{frame_path}.label is required")
        _validate_emotions(frame.get("emotions"), f"{frame_path}.emotions", errors, palette_ids)
        intensity = frame.get("intensity")
        if intensity is not None:
            try:
                numeric_intensity = float(intensity)
            except (TypeError, ValueError):
                errors.append(f"{frame_path}.intensity must be numeric 0..1")
            else:
                if not 0 <= numeric_intensity <= 1:
                    errors.append(f"{frame_path}.intensity must be within 0..1")
        motion = frame.get("motion")
        if motion is not None and motion not in allowed_motion:
            errors.append(f"{frame_path}.motion must be one of {sorted(allowed_motion)}")
        confidence = frame.get("confidence")
        if confidence is not None and confidence not in CONFIDENCE_LEVELS:
            errors.append(f"{frame_path}.confidence must be high, medium, or low")
        evidence_level = frame.get("evidence_level")
        if evidence_level is not None and evidence_level not in EVIDENCE_LEVELS:
            errors.append(f"{frame_path}.evidence_level must be one of {sorted(EVIDENCE_LEVELS)}")
        driver_ref = frame.get("driver_ref")
        if driver_ref is not None:
            if not _is_nonempty(driver_ref):
                errors.append(f"{frame_path}.driver_ref must be non-empty when provided")
            elif driver_ids is not None and str(driver_ref) not in driver_ids:
                errors.append(f"{frame_path}.driver_ref references unknown phase driver id: {driver_ref}")



def _last_emotions(state: dict) -> list:
    """Return the locked end-of-phase emotion mix for one state."""
    exit_state = state.get("exit_state")
    if isinstance(exit_state, dict) and isinstance(exit_state.get("emotions"), list):
        return copy.deepcopy(exit_state.get("emotions") or [])
    frames = state.get("keyframes")
    if isinstance(frames, list) and frames:
        usable = [frame for frame in frames if isinstance(frame, dict)]
        if usable:
            frame = max(usable, key=lambda item: float(item.get("at", 0) or 0))
            return copy.deepcopy(frame.get("emotions") or [])
    entry_state = state.get("entry_state")
    if isinstance(entry_state, dict):
        return copy.deepcopy(entry_state.get("emotions") or [])
    return []


def _last_audience_frame(state: dict) -> dict:
    frames = state.get("keyframes")
    if not isinstance(frames, list) or not frames:
        return {"emotions": [], "label": "阶段状态"}
    usable = [frame for frame in frames if isinstance(frame, dict)]
    if not usable:
        return {"emotions": [], "label": "阶段状态"}
    return max(usable, key=lambda item: float(item.get("at", 0) or 0))


def _ordered_phase_ids(phases: list, order_key: str) -> list[str]:
    indexed = []
    for index, phase in enumerate(phases):
        if not isinstance(phase, dict):
            continue
        raw_order = phase.get(order_key)
        try:
            order = float(raw_order)
        except (TypeError, ValueError):
            order = float(index + 1)
        indexed.append((order, index, str(phase.get("id") or f"P{index + 1:02d}")))
    indexed.sort(key=lambda item: (item[0], item[1]))
    return [phase_id for _, _, phase_id in indexed]


def derive_render_model(payload: dict) -> dict:
    """Build the unique render model from locked phase states.

    `global_emotional_arc` remains a narrative summary contract, but its duplicated
    emotion nodes are not trusted as a second source of truth. Character and audience
    river nodes are derived from `phase_events` so local and global views cannot drift.
    """
    phases = payload.get("phase_events") or []
    topology = payload.get("narrative_topology") or {}
    continuity_mode = topology.get("continuity_mode") or "continuous"
    old_global = payload.get("global_emotional_arc") or {}
    old_character = {
        str(arc.get("character")): arc
        for arc in old_global.get("character_arcs") or []
        if isinstance(arc, dict) and arc.get("character")
    }
    character_throughlines = {
        str(item.get("character")): item.get("throughline") or ""
        for item in old_global.get("character_throughlines") or []
        if isinstance(item, dict) and item.get("character")
    }
    audience_throughlines = {
        str(item.get("segment_id")): item.get("throughline") or ""
        for item in old_global.get("audience_throughlines") or []
        if isinstance(item, dict) and item.get("segment_id")
    }
    segments_source = payload.get("audience_lenses") if isinstance(payload.get("audience_lenses"), list) else payload.get("audience_segments")
    segments = [item for item in segments_source or [] if isinstance(item, dict)]
    segment_defs = {str(item.get("id")): item for item in segments if item.get("id")}

    character_nodes: dict[str, list[dict]] = {}
    audience_nodes: dict[str, list[dict]] = {str(item.get("id")): [] for item in segments if item.get("id")}

    for phase_index, phase in enumerate(phases):
        if not isinstance(phase, dict):
            continue
        phase_id = str(phase.get("id") or f"P{phase_index + 1:02d}")
        for state in phase.get("character_states") or []:
            if not isinstance(state, dict) or not state.get("character"):
                continue
            character = str(state.get("character"))
            if continuity_mode == "reset":
                continuity_group = f"{character}::{phase_id}"
            elif continuity_mode == "mixed":
                continuity_group = str(state.get("continuity_group") or f"UNSPECIFIED::{character}::{phase_id}")
            else:
                continuity_group = str(state.get("continuity_group") or f"{character}::continuous")
            exit_state = state.get("exit_state") if isinstance(state.get("exit_state"), dict) else {}
            character_nodes.setdefault(character, []).append({
                "phase_id": phase_id,
                "emotions": _last_emotions(state),
                "cognition": exit_state.get("cognition") or state.get("cognition_shift") or "",
                "relationship": exit_state.get("relationship") or state.get("relationship_shift") or "",
                "agency": exit_state.get("agency") or state.get("choice_shift") or "",
                "continuity_group": continuity_group,
                "evidence_refs": copy.deepcopy(state.get("evidence_refs") or []),
                "confidence": state.get("confidence") or exit_state.get("confidence") or "medium",
                "narrative_layer_id": phase.get("narrative_layer_id") or "REALITY",
            })

        for state in phase.get("audience_states") or []:
            if not isinstance(state, dict) or not state.get("segment_id"):
                continue
            segment_id = str(state.get("segment_id"))
            last = _last_audience_frame(state)
            audience_nodes.setdefault(segment_id, []).append({
                "phase_id": phase_id,
                "emotions": copy.deepcopy(last.get("emotions") or []),
                "knowledge": state.get("knowledge_state") or "",
                "question": state.get("misread_or_question") or "",
                "reappraisal": state.get("reappraisal") or "",
                "continuity_group": f"audience::{segment_id}",
                "evidence_refs": copy.deepcopy(state.get("evidence_refs") or []),
                "confidence": state.get("confidence") or last.get("confidence") or "medium",
                "narrative_layer_id": phase.get("narrative_layer_id") or "REALITY",
            })

    character_arcs = []
    for character, nodes in character_nodes.items():
        source = old_character.get(character) or {}
        character_arcs.append({
            "character": character,
            "throughline": character_throughlines.get(character) or source.get("throughline") or "由阶段退出状态自动聚合",
            "nodes": nodes,
        })

    audience_segment_arcs = []
    for segment in segments:
        segment_id = str(segment.get("id") or "")
        if not segment_id:
            continue
        audience_segment_arcs.append({
            "segment_id": segment_id,
            "name": segment.get("label") or segment_id,
            "throughline": audience_throughlines.get(segment_id) or segment.get("question_lens") or segment.get("perspective") or "",
            "nodes": audience_nodes.get(segment_id, []),
        })

    return {
        "orders": {
            "story": _ordered_phase_ids(phases, "story_order"),
            "audience": _ordered_phase_ids(phases, "audience_order"),
        },
        "character_arcs": character_arcs,
        "audience_segment_arcs": audience_segment_arcs,
        "continuity_mode": continuity_mode,
        "summary": old_global.get("summary") or "",
        "major_turns": copy.deepcopy(old_global.get("major_turns") or []),
        "ending_residue": old_global.get("ending_residue") or "",
        "aggregation_policy": "derive_from_phase_states",
    }

def _validate_adaptive_emotion(payload: dict, stage: object, lock_status: object, errors: list[str]) -> None:
    final_locked = stage == "locked_audit" and lock_status == "LOCKED"
    topology = payload.get("narrative_topology")
    phases = payload.get("phase_events")
    global_arc = payload.get("global_emotional_arc")
    phase_links = payload.get("phase_links")
    audience_segments = payload.get("audience_lenses") if payload.get("audience_lenses") is not None else payload.get("audience_segments")

    if final_locked:
        if not isinstance(topology, dict):
            errors.append("locked_audit requires narrative_topology as an object")
        if not isinstance(phases, list):
            errors.append("locked_audit requires phase_events as an array")
        if not isinstance(global_arc, dict):
            errors.append("locked_audit requires global_emotional_arc as an object")
        if not isinstance(phase_links, list):
            errors.append("locked_audit requires phase_links as an array")
        if not isinstance(audience_segments, list):
            errors.append("locked_audit requires audience_lenses (preferred) or legacy audience_segments as an array")

    if topology is not None:
        if not isinstance(topology, dict):
            errors.append("narrative_topology must be an object")
        else:
            if topology.get("continuity_mode") not in {"continuous", "reset", "mixed"}:
                errors.append("narrative_topology.continuity_mode must be continuous, reset, or mixed")
            for key in ("story_time_basis", "audience_time_basis"):
                if not _is_nonempty(topology.get(key)):
                    errors.append(f"narrative_topology.{key} is required")
            if topology.get("notes") is not None and not isinstance(topology.get("notes"), list):
                errors.append("narrative_topology.notes must be an array")
            layers = topology.get("narrative_layers")
            if layers is not None and not isinstance(layers, list):
                errors.append("narrative_topology.narrative_layers must be an array when provided")
            elif isinstance(layers, list):
                seen_layers: set[str] = set()
                for lindex, layer in enumerate(layers, start=1):
                    lpath = f"narrative_topology.narrative_layers[{lindex}]"
                    if not isinstance(layer, dict):
                        errors.append(f"{lpath} must be an object")
                        continue
                    for key in ("id", "label", "family"):
                        if not _is_nonempty(layer.get(key)):
                            errors.append(f"{lpath}.{key} is required")
                    layer_id = str(layer.get("id") or "")
                    if layer_id in seen_layers:
                        errors.append(f"{lpath}.id is duplicated: {layer_id}")
                    if layer_id:
                        seen_layers.add(layer_id)
                    if layer.get("family") not in LAYER_FAMILIES:
                        errors.append(f"{lpath}.family must be one of {sorted(LAYER_FAMILIES)}")

    palette_ids: set[str] = set()
    palette = payload.get("emotion_palette")
    if palette is not None:
        if not isinstance(palette, list):
            errors.append("emotion_palette must be an array")
        else:
            for index, item in enumerate(palette, start=1):
                path = f"emotion_palette[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{path} must be an object")
                    continue
                for key in ("id", "label", "color"):
                    if not _is_nonempty(item.get(key)):
                        errors.append(f"{path}.{key} is required")
                emotion_id = str(item.get("id", ""))
                if emotion_id:
                    if emotion_id in palette_ids:
                        errors.append(f"{path}.id is duplicated: {emotion_id}")
                    palette_ids.add(emotion_id)

    audience_segment_ids: set[str] = set()
    if audience_segments is not None:
        if not isinstance(audience_segments, list):
            errors.append("audience_segments must be an array")
        else:
            for segment_index, segment in enumerate(audience_segments, start=1):
                segment_path = f"audience_segments[{segment_index}]"
                if not isinstance(segment, dict):
                    errors.append(f"{segment_path} must be an object")
                    continue
                segment_id = segment.get("id")
                if not _is_nonempty(segment_id):
                    errors.append(f"{segment_path}.id is required")
                else:
                    segment_id = str(segment_id)
                    if segment_id in audience_segment_ids:
                        errors.append(f"{segment_path}.id is duplicated: {segment_id}")
                    audience_segment_ids.add(segment_id)
                for key in ("label", "perspective", "question_lens"):
                    if not _is_nonempty(segment.get(key)):
                        errors.append(f"{segment_path}.{key} is required")
                if not isinstance(segment.get("evidence_refs"), list):
                    errors.append(f"{segment_path}.evidence_refs must be an array")

    phase_ids: set[str] = set()
    if phases is not None:
        if not isinstance(phases, list):
            errors.append("phase_events must be an array")
        else:
            for phase_index, phase in enumerate(phases, start=1):
                phase_path = f"phase_events[{phase_index}]"
                if not isinstance(phase, dict):
                    errors.append(f"{phase_path} must be an object")
                    continue
                phase_id = phase.get("id")
                if not _is_nonempty(phase_id):
                    errors.append(f"{phase_path}.id is required")
                else:
                    phase_id = str(phase_id)
                    if phase_id in phase_ids:
                        errors.append(f"{phase_path}.id is duplicated: {phase_id}")
                    phase_ids.add(phase_id)
                for key in ("label", "scope_label", "state_change_reason", "summary", "confidence"):
                    if not _is_nonempty(phase.get(key)):
                        errors.append(f"{phase_path}.{key} is required")
                drivers = phase.get("drivers")
                if drivers is None and not _is_nonempty(phase.get("trigger")):
                    errors.append(f"{phase_path} requires trigger or drivers[]")
                if drivers is not None and not isinstance(drivers, list):
                    errors.append(f"{phase_path}.drivers must be an array when provided")
                for key in ("story_order", "audience_order"):
                    try:
                        float(phase.get(key))
                    except (TypeError, ValueError):
                        errors.append(f"{phase_path}.{key} must be numeric")
                if phase.get("confidence") not in {"high", "medium", "low"}:
                    errors.append(f"{phase_path}.confidence must be high, medium, or low")
                if phase.get("mechanisms") is not None and not isinstance(phase.get("mechanisms"), list):
                    errors.append(f"{phase_path}.mechanisms must be an array")
                if phase.get("relative_span") is not None:
                    try:
                        span = float(phase.get("relative_span"))
                    except (TypeError, ValueError):
                        errors.append(f"{phase_path}.relative_span must be numeric > 0")
                    else:
                        if span <= 0:
                            errors.append(f"{phase_path}.relative_span must be > 0")
                for key in ("character_states", "audience_states", "relationship_changes", "irreversible_changes", "evidence_refs"):
                    if not isinstance(phase.get(key), list):
                        errors.append(f"{phase_path}.{key} must be an array")

                driver_ids: set[str] = set()
                if isinstance(phase.get("drivers"), list):
                    last_driver_at = -1.0
                    for driver_index, driver in enumerate(phase.get("drivers") or [], start=1):
                        driver_path = f"{phase_path}.drivers[{driver_index}]"
                        if not isinstance(driver, dict):
                            errors.append(f"{driver_path} must be an object")
                            continue
                        for key in ("id", "label", "observable_event"):
                            if not _is_nonempty(driver.get(key)):
                                errors.append(f"{driver_path}.{key} is required")
                        driver_id = str(driver.get("id") or "")
                        if driver_id:
                            if driver_id in driver_ids:
                                errors.append(f"{driver_path}.id is duplicated: {driver_id}")
                            driver_ids.add(driver_id)
                        try:
                            driver_at = float(driver.get("at"))
                        except (TypeError, ValueError):
                            errors.append(f"{driver_path}.at must be numeric 0..1")
                        else:
                            if not 0 <= driver_at <= 1:
                                errors.append(f"{driver_path}.at must be within 0..1")
                            if driver_at < last_driver_at:
                                errors.append(f"{phase_path}.drivers at values must be monotonic")
                            last_driver_at = driver_at
                        if not isinstance(driver.get("evidence_refs"), list):
                            errors.append(f"{driver_path}.evidence_refs must be an array")

                layer_id = phase.get("narrative_layer_id")
                layers = topology.get("narrative_layers") if isinstance(topology, dict) else None
                if layer_id is not None and isinstance(layers, list):
                    known_layers = {str(layer.get("id")) for layer in layers if isinstance(layer, dict) and layer.get("id")}
                    if known_layers and str(layer_id) not in known_layers:
                        errors.append(f"{phase_path}.narrative_layer_id references unknown narrative layer id: {layer_id}")

                for state_index, state in enumerate(phase.get("character_states") or [], start=1):
                    state_path = f"{phase_path}.character_states[{state_index}]"
                    if not isinstance(state, dict):
                        errors.append(f"{state_path} must be an object")
                        continue
                    if not _is_nonempty(state.get("character")):
                        errors.append(f"{state_path}.character is required")
                    for edge in ("entry_state", "exit_state"):
                        value = state.get(edge)
                        if not isinstance(value, dict):
                            errors.append(f"{state_path}.{edge} must be an object")
                        else:
                            _validate_emotions(value.get("emotions"), f"{state_path}.{edge}.emotions", errors, palette_ids)
                    _validate_keyframes(state.get("keyframes"), f"{state_path}.keyframes", errors, palette_ids, driver_ids)
                    if not isinstance(state.get("evidence_refs"), list):
                        errors.append(f"{state_path}.evidence_refs must be an array")
                    if isinstance(topology, dict) and topology.get("continuity_mode") == "mixed" and not _is_nonempty(state.get("continuity_group")):
                        errors.append(f"{state_path}.continuity_group is required when narrative_topology.continuity_mode=mixed")

                for state_index, state in enumerate(phase.get("audience_states") or [], start=1):
                    state_path = f"{phase_path}.audience_states[{state_index}]"
                    if not isinstance(state, dict):
                        errors.append(f"{state_path} must be an object")
                        continue
                    if not _is_nonempty(state.get("segment")):
                        errors.append(f"{state_path}.segment is required")
                    segment_id = state.get("segment_id")
                    if not _is_nonempty(segment_id):
                        errors.append(f"{state_path}.segment_id is required")
                    elif audience_segment_ids and str(segment_id) not in audience_segment_ids:
                        errors.append(f"{state_path}.segment_id references unknown audience segment id: {segment_id}")
                    _validate_keyframes(state.get("keyframes"), f"{state_path}.keyframes", errors, palette_ids, driver_ids)
                    if not isinstance(state.get("evidence_refs"), list):
                        errors.append(f"{state_path}.evidence_refs must be an array")

    if phase_links is not None:
        if not isinstance(phase_links, list):
            errors.append("phase_links must be an array")
        else:
            for link_index, link in enumerate(phase_links, start=1):
                link_path = f"phase_links[{link_index}]"
                if not isinstance(link, dict):
                    errors.append(f"{link_path} must be an object")
                    continue
                from_id = link.get("from")
                to_id = link.get("to")
                for key, value in (("from", from_id), ("to", to_id)):
                    if not _is_nonempty(value):
                        errors.append(f"{link_path}.{key} is required")
                    elif phase_ids and str(value) not in phase_ids:
                        errors.append(f"{link_path}.{key} references unknown phase id: {value}")
                if link.get("kind") is not None and not _is_nonempty(link.get("kind")):
                    errors.append(f"{link_path}.kind must be a non-empty string when provided")
                family = link.get("family")
                if family is not None and str(family).upper() not in LINK_FAMILIES:
                    errors.append(f"{link_path}.family must be one of {sorted(LINK_FAMILIES)}")
                if not isinstance(link.get("evidence_refs"), list):
                    errors.append(f"{link_path}.evidence_refs must be an array")

    phase_clusters = payload.get("phase_clusters")
    if phase_clusters is not None:
        if not isinstance(phase_clusters, list):
            errors.append("phase_clusters must be an array when provided")
        else:
            cluster_ids: set[str] = set()
            for cindex, cluster in enumerate(phase_clusters, start=1):
                cpath = f"phase_clusters[{cindex}]"
                if not isinstance(cluster, dict):
                    errors.append(f"{cpath} must be an object")
                    continue
                for key in ("id", "label", "phase_ids", "summary", "evidence_refs"):
                    if key not in cluster:
                        errors.append(f"{cpath}.{key} is required")
                cid = str(cluster.get("id") or "")
                if cid:
                    if cid in cluster_ids:
                        errors.append(f"{cpath}.id is duplicated: {cid}")
                    cluster_ids.add(cid)
                if not isinstance(cluster.get("phase_ids"), list) or not cluster.get("phase_ids"):
                    errors.append(f"{cpath}.phase_ids must be a non-empty array")
                else:
                    for pid in cluster.get("phase_ids") or []:
                        if phase_ids and str(pid) not in phase_ids:
                            errors.append(f"{cpath}.phase_ids references unknown phase id: {pid}")
                if not isinstance(cluster.get("evidence_refs"), list):
                    errors.append(f"{cpath}.evidence_refs must be an array")

    if global_arc is not None:
        if not isinstance(global_arc, dict):
            errors.append("global_emotional_arc must be an object")
        else:
            if not _is_nonempty(global_arc.get("summary")):
                errors.append("global_emotional_arc.summary is required")
            if not _is_nonempty(global_arc.get("ending_residue")):
                errors.append("global_emotional_arc.ending_residue is required")
            policy = global_arc.get("aggregation_policy")
            if policy is not None and policy != "derive_from_phase_states":
                errors.append("global_emotional_arc.aggregation_policy must be derive_from_phase_states when provided")
            for key in ("phase_ids", "major_turns"):
                if not isinstance(global_arc.get(key), list):
                    errors.append(f"global_emotional_arc.{key} must be an array")
            for key in ("character_throughlines", "audience_throughlines"):
                if global_arc.get(key) is not None and not isinstance(global_arc.get(key), list):
                    errors.append(f"global_emotional_arc.{key} must be an array when provided")

            referenced: list[tuple[str, str]] = []
            for phase_id in global_arc.get("phase_ids") or []:
                referenced.append(("global_emotional_arc.phase_ids", str(phase_id)))

            for item_index, item in enumerate(global_arc.get("character_throughlines") or [], start=1):
                item_path = f"global_emotional_arc.character_throughlines[{item_index}]"
                if not isinstance(item, dict):
                    errors.append(f"{item_path} must be an object")
                    continue
                for key in ("character", "throughline"):
                    if not _is_nonempty(item.get(key)):
                        errors.append(f"{item_path}.{key} is required")

            for item_index, item in enumerate(global_arc.get("audience_throughlines") or [], start=1):
                item_path = f"global_emotional_arc.audience_throughlines[{item_index}]"
                if not isinstance(item, dict):
                    errors.append(f"{item_path} must be an object")
                    continue
                if not _is_nonempty(item.get("segment_id")):
                    errors.append(f"{item_path}.segment_id is required")
                elif audience_segment_ids and str(item.get("segment_id")) not in audience_segment_ids:
                    errors.append(f"{item_path}.segment_id references unknown audience segment id: {item.get('segment_id')}")
                if not _is_nonempty(item.get("throughline")):
                    errors.append(f"{item_path}.throughline is required")

            # Legacy v0.9 duplicate nodes remain accepted for backward compatibility,
            # but the renderer ignores their emotions and derives the visual model from phase states.
            legacy_character_arcs = global_arc.get("character_arcs")
            if legacy_character_arcs is not None:
                if not isinstance(legacy_character_arcs, list):
                    errors.append("global_emotional_arc.character_arcs must be an array when provided")
                else:
                    for arc_index, arc in enumerate(legacy_character_arcs, start=1):
                        if not isinstance(arc, dict):
                            errors.append(f"global_emotional_arc.character_arcs[{arc_index}] must be an object")
                            continue
                        for node_index, node in enumerate(arc.get("nodes") or [], start=1):
                            if isinstance(node, dict):
                                referenced.append((f"global_emotional_arc.character_arcs[{arc_index}].nodes[{node_index}]", str(node.get("phase_id", ""))))
            legacy_audience_arc = global_arc.get("audience_arc")
            if legacy_audience_arc is not None:
                if not isinstance(legacy_audience_arc, dict):
                    errors.append("global_emotional_arc.audience_arc must be an object when provided")
                else:
                    for node_index, node in enumerate(legacy_audience_arc.get("nodes") or [], start=1):
                        if isinstance(node, dict):
                            referenced.append((f"global_emotional_arc.audience_arc.nodes[{node_index}]", str(node.get("phase_id", ""))))

            for turn_index, turn in enumerate(global_arc.get("major_turns") or [], start=1):
                turn_path = f"global_emotional_arc.major_turns[{turn_index}]"
                if not isinstance(turn, dict):
                    errors.append(f"{turn_path} must be an object")
                    continue
                if not _is_nonempty(turn.get("phase_id")):
                    errors.append(f"{turn_path}.phase_id is required")
                else:
                    referenced.append((turn_path, str(turn.get("phase_id"))))
                if not _is_nonempty(turn.get("label")):
                    errors.append(f"{turn_path}.label is required")
                if not isinstance(turn.get("evidence_refs"), list):
                    errors.append(f"{turn_path}.evidence_refs must be an array")

            if phase_ids:
                for path, phase_id in referenced:
                    if phase_id and phase_id not in phase_ids:
                        errors.append(f"{path} references unknown phase id: {phase_id}")


def validate_payload(payload: object) -> list[str]:
    """Validate the staged forge payload before embedding it in HTML.

    This is intentionally a small dependency-free contract check. It validates
    shape, stage gates, and cross-references; it does not judge dramatic quality.
    """
    if not isinstance(payload, dict):
        return ["report payload must be a JSON object"]

    errors: list[str] = []
    meta = _require_object(payload, "meta", errors)
    if meta:
        for key in ("title", "runtime", "precision", "workflow_stage"):
            if not _is_nonempty(meta.get(key)):
                errors.append(f"meta.{key} is required")
        if meta.get("format") not in FORMATS:
            errors.append(f"meta.format must be one of {sorted(FORMATS)}")
        if meta.get("precision") not in PRECISIONS:
            errors.append(f"meta.precision must be one of {sorted(PRECISIONS)}")
        if meta.get("workflow_stage") not in WORKFLOW_STAGES:
            errors.append(f"meta.workflow_stage must be one of {sorted(WORKFLOW_STAGES)}")
        if meta.get("quality_route") is not None and meta.get("quality_route") not in QUALITY_ROUTES:
            errors.append(f"meta.quality_route must be one of {sorted(QUALITY_ROUTES)}")

    fact_boundary = _require_object(payload, "fact_boundary", errors)
    for key in ("locked", "supported", "proposed", "verify"):
        if key not in fact_boundary or not isinstance(fact_boundary.get(key), list):
            errors.append(f"fact_boundary.{key} must be an array")

    for key in ("canonical_names", "rhythm_causality", "characters", "relationship_shifts", "audience_path", "breakpoints", "unknowns", "directions"):
        _require_list(payload, key, errors)

    rhythm = payload.get("rhythm_causality")
    if isinstance(rhythm, list):
        seen_ids: set[str] = set()
        for index, event in enumerate(rhythm, start=1):
            if not isinstance(event, dict):
                errors.append(f"rhythm_causality[{index}] must be an object")
                continue
            event_id = event.get("id")
            if not _is_nonempty(event_id):
                errors.append(f"rhythm_causality[{index}].id is required")
            elif str(event_id) in seen_ids:
                errors.append(f"rhythm_causality[{index}].id is duplicated: {event_id}")
            else:
                seen_ids.add(str(event_id))
            for key in ("label", "event", "basis", "confidence"):
                if not _is_nonempty(event.get(key)):
                    errors.append(f"rhythm_causality[{index}].{key} is required")
            if event.get("confidence") not in {"high", "medium", "low"}:
                errors.append(f"rhythm_causality[{index}].confidence must be high, medium, or low")

    stage = meta.get("workflow_stage")

    packet = payload.get("production_packet")
    if packet is not None:
        packet = _require_object(payload, "production_packet", errors)
        for key in ("scope", "incoming_state", "required_event", "character_interpretations", "relationship_transmission", "audience_knowledge", "debts_in", "required_irreversible_change", "next_unit_interface"):
            if key not in packet:
                errors.append(f"production_packet.{key} is required")
    elif stage in {"draft", "locked_audit"}:
        errors.append("production_packet is required for draft and locked_audit stages")

    state_delta = payload.get("state_delta")
    if state_delta is not None:
        state_delta = _require_object(payload, "state_delta", errors)
        for key in ("new_facts", "knowledge_changes", "character_changes", "relationship_debt_changes", "opened_loops", "closed_loops", "last_irreversible_change", "next_unit"):
            if key not in state_delta:
                errors.append(f"state_delta.{key} is required")
    elif stage == "locked_audit":
        errors.append("state_delta is required for locked_audit stage")

    script_audit = payload.get("script_audit")
    if script_audit is not None:
        script_audit = _require_object(payload, "script_audit", errors)
        for key in ("source_script_version", "precision", "causality_findings", "continuity_findings", "audience_findings", "repair_scope", "lock_status"):
            if key not in script_audit:
                errors.append(f"script_audit.{key} is required")
    elif stage == "locked_audit":
        errors.append("script_audit is required for locked_audit stage")
        script_audit = {}

    lock_status = script_audit.get("lock_status") if isinstance(script_audit, dict) else None
    if script_audit and lock_status not in {"DRAFT", "LOCKED"}:
        errors.append("script_audit.lock_status must be DRAFT or LOCKED")

    diff = script_audit.get("blueprint_evidence_diff") if isinstance(script_audit, dict) else None
    if diff is not None:
        if not isinstance(diff, list):
            errors.append("script_audit.blueprint_evidence_diff must be an array")
        else:
            allowed_statuses = {"realized", "partial", "missing", "contradicted", "unknown"}
            for index, row in enumerate(diff, start=1):
                if not isinstance(row, dict):
                    errors.append(f"script_audit.blueprint_evidence_diff[{index}] must be an object")
                    continue
                for key in ("blueprint_item_id", "intent", "expected_evidence", "observed_evidence", "status", "impact", "evidence_refs"):
                    if key not in row:
                        errors.append(f"script_audit.blueprint_evidence_diff[{index}].{key} is required")
                if row.get("status") not in allowed_statuses:
                    errors.append(
                        f"script_audit.blueprint_evidence_diff[{index}].status must be one of {sorted(allowed_statuses)}"
                    )
                if "evidence_refs" in row and not isinstance(row.get("evidence_refs"), list):
                    errors.append(f"script_audit.blueprint_evidence_diff[{index}].evidence_refs must be an array")

    long_form = payload.get("long_form")
    if long_form is not None:
        long_form = _require_object(payload, "long_form", errors)
        if long_form and not isinstance(long_form.get("continuation_ledger"), dict):
            errors.append("long_form.continuation_ledger must be an object")
    elif stage == "locked_audit":
        errors.append("long_form is required for locked_audit stage")

    handoff = payload.get("handoff")
    if handoff is not None:
        handoff = _require_object(payload, "handoff", errors)
        for key in ("premise", "human_question", "competing_values", "motifs", "ending_aftertaste", "next_ai_prompt"):
            if key not in handoff:
                errors.append(f"handoff.{key} is required")
    elif stage == "locked_audit":
        errors.append("handoff is required for locked_audit stage")

    route = meta.get("quality_route")
    if route == "S-CANDIDATE":
        necessity = payload.get("story_necessity")
        if not isinstance(necessity, dict):
            errors.append("S-CANDIDATE requires story_necessity")
        else:
            for key in ("why_now", "why_this_protagonist", "no_rational_exit", "inaction_cost", "form_necessity", "verdict", "evidence_refs", "strongest_counterexample", "confidence", "responsible_layer"):
                if key not in necessity:
                    errors.append(f"story_necessity.{key} is required for S-CANDIDATE")
            if necessity.get("verdict") not in {"pass", "revise", "block"}:
                errors.append("story_necessity.verdict must be pass, revise, or block")
        for key in ("opposition_engine", "decision_chains", "ending_tournament", "episode_distinction_matrix", "peak_aftermath_ledger"):
            value = payload.get(key)
            expected = "object" if key == "opposition_engine" else "array"
            if (expected == "object" and not isinstance(value, dict)) or (expected == "array" and not isinstance(value, list)):
                errors.append(f"S-CANDIDATE requires {key} as an {expected}")
        decisions = payload.get("decision_chains")
        if isinstance(decisions, list) and not decisions:
            errors.append("S-CANDIDATE decision_chains must not be empty")
        endings = payload.get("ending_tournament")
        if isinstance(endings, list) and len(endings) < 3:
            errors.append("S-CANDIDATE ending_tournament must contain at least three candidates")

    if stage == "locked_audit":
        if lock_status != "LOCKED":
            errors.append("locked_audit requires script_audit.lock_status=LOCKED")
        diff = script_audit.get("blueprint_evidence_diff")
        if not isinstance(diff, list):
            errors.append("locked_audit requires script_audit.blueprint_evidence_diff as an array")
        if script_audit.get("precision") not in {"SCRIPT_FINE", "MIXED"}:
            errors.append("locked_audit requires script_audit.precision=SCRIPT_FINE or MIXED")

    _validate_adaptive_emotion(payload, stage, lock_status, errors)

    return errors


def encode_for_script(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return (
        encoded.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def render(input_path: Path, output_path: Path) -> None:
    with input_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    errors = validate_payload(payload)
    if errors:
        raise ValueError("report schema validation failed: " + "; ".join(errors))

    template_path = Path(__file__).resolve().parent.parent / "assets" / "emotion-map-template.html"
    template = template_path.read_text(encoding="utf-8")
    if template.count(TOKEN) != 1:
        raise ValueError("HTML template must contain exactly one report-data token")

    render_payload = copy.deepcopy(payload)
    render_payload["_render_model"] = derive_render_model(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(template.replace(TOKEN, encode_for_script(render_payload)), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render an offline emotion diagnosis HTML report")
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_html", type=Path)
    parser.add_argument("--validate-only", action="store_true", help="validate payload without rendering HTML")
    args = parser.parse_args()
    try:
        with args.input_json.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        errors = validate_payload(payload)
        if errors:
            raise ValueError("report schema validation failed: " + "; ".join(errors))
        if not args.validate_only:
            render(args.input_json, args.output_html)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"render failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
