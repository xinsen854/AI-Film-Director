#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

LOCK_CONTRACT = "AFD_SCENE_GEO_LOCK_V1"
LOCKED_FIELDS = (
    "stable_geography",
    "functional_zones",
    "landmark_anchors",
    "entrances_exits",
)
STABLE_TOPOLOGY_KEYS = (
    "zones",
    "entrances",
    "exits",
    "vertical_relations",
    "landmarks",
    "occluders",
)


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(_has_content(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_has_content(item) for item in value)
    return True


def canonical_location_geo(location_record: dict) -> dict:
    return {field: location_record.get(field) for field in LOCKED_FIELDS}


def geo_sha256(location_record: dict) -> str:
    geo = canonical_location_geo(location_record)
    if not any(_has_content(value) for value in geo.values()):
        raise ValueError("location asset has no stable geometry fields to lock")
    payload = json.dumps(geo, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_scene_geo_lock(scene_id: str, location_record: dict) -> dict:
    scene_id = str(scene_id or "").strip()
    asset_id = str(location_record.get("asset_id") or "").strip()
    if not scene_id:
        raise ValueError("scene_id is required")
    if not asset_id.startswith("S"):
        raise ValueError("scene GEO lock requires an S-series location asset")
    digest = geo_sha256(location_record)
    return {
        "lock_contract": LOCK_CONTRACT,
        "lock_id": f"GEO-{scene_id}-{asset_id}-{digest[:12]}",
        "scene_id": scene_id,
        "location_asset_id": asset_id,
        "geo_sha256": digest,
        "locked_fields": list(LOCKED_FIELDS),
        "locked_geometry": canonical_location_geo(location_record),
    }


def _meaningful_spatial_topology(spatial_result: dict) -> bool:
    if str(spatial_result.get("activation_state") or "") != "ACTIVE":
        return False
    topology = spatial_result.get("space_topology")
    if not isinstance(topology, dict):
        return False
    return any(_has_content(topology.get(key)) for key in STABLE_TOPOLOGY_KEYS)


def validate_scene_geo_contract(
    scene_id: str,
    spatial_result: dict,
    scene_shots: list[dict],
    asset_records: dict[str, dict],
    *,
    require_topology: bool = False,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(spatial_result, dict):
        return errors
    if str(spatial_result.get("activation_state") or "") != "ACTIVE":
        return errors
    meaningful_topology = _meaningful_spatial_topology(spatial_result)
    if require_topology and not meaningful_topology:
        return [
            f"{scene_id}: SCENE_GEO_TOPOLOGY_REQUIRED Router activated SPATIAL_TOPOLOGY but ACTIVE spatial result has no stable topology"
        ]
    if not meaningful_topology:
        return errors

    lock = spatial_result.get("scene_geo_lock")
    if not isinstance(lock, dict):
        return [f"{scene_id}: SCENE_GEO_LOCK_REQUIRED meaningful ACTIVE spatial topology requires scene_geo_lock"]

    required = {"lock_contract", "lock_id", "scene_id", "location_asset_id", "geo_sha256", "locked_fields", "locked_geometry"}
    missing = sorted(required - set(lock))
    if missing:
        errors.append(f"{scene_id}: SCENE_GEO_LOCK_INVALID missing {', '.join(missing)}")
        return errors
    if lock.get("lock_contract") != LOCK_CONTRACT:
        errors.append(f"{scene_id}: SCENE_GEO_LOCK_INVALID lock_contract must be {LOCK_CONTRACT}")
    if str(lock.get("scene_id") or "") != str(scene_id):
        errors.append(f"{scene_id}: SCENE_GEO_LOCK_INVALID scene_id mismatch")

    locked_fields = lock.get("locked_fields")
    if not isinstance(locked_fields, list) or set(locked_fields) != set(LOCKED_FIELDS):
        errors.append(
            f"{scene_id}: SCENE_GEO_OVERLOCK locked_fields must be pure location geometry only; "
            "camera/character/blocking state must remain shot-level"
        )

    location_asset_id = str(lock.get("location_asset_id") or "")
    location = asset_records.get(location_asset_id)
    if not isinstance(location, dict) or not location_asset_id.startswith("S"):
        errors.append(f"{scene_id}: SCENE_GEO_LOCATION_MISSING {location_asset_id or '<missing>'}")
        return errors

    try:
        expected = build_scene_geo_lock(scene_id, location)
    except ValueError as exc:
        errors.append(f"{scene_id}: SCENE_GEO_LOCATION_INVALID {exc}")
        return errors

    if (
        str(lock.get("geo_sha256") or "") != expected["geo_sha256"]
        or str(lock.get("lock_id") or "") != expected["lock_id"]
        or lock.get("locked_geometry") != expected["locked_geometry"]
    ):
        errors.append(
            f"{scene_id}: SCENE_GEO_STALE lock does not match current ASSET_LIBRARY stable geography for {location_asset_id}"
        )

    expected_ref = expected["lock_id"]
    expected_hash = expected["geo_sha256"]
    for shot in scene_shots:
        if not isinstance(shot, dict) or str(shot.get("scene_id") or "") != str(scene_id):
            continue
        shot_id = str(shot.get("edit_shot_id") or "UNKNOWN")
        spatial = shot.get("spatial_blocking")
        if not isinstance(spatial, dict):
            errors.append(f"{scene_id}/{shot_id}: SCENE_GEO_SHOT_MISMATCH spatial_blocking missing")
            continue
        if str(spatial.get("location_asset") or "") != location_asset_id:
            errors.append(
                f"{scene_id}/{shot_id}: SCENE_GEO_SHOT_MISMATCH location_asset must remain {location_asset_id}"
            )
        if str(spatial.get("scene_geo_lock_ref") or "") != expected_ref:
            errors.append(
                f"{scene_id}/{shot_id}: SCENE_GEO_SHOT_MISMATCH scene_geo_lock_ref must be {expected_ref}"
            )
        if str(spatial.get("scene_geo_sha256") or "") != expected_hash:
            errors.append(
                f"{scene_id}/{shot_id}: SCENE_GEO_SHOT_MISMATCH scene_geo_sha256 does not match locked geography"
            )
    return errors


def _load_location(asset_library: Path, location_asset_id: str) -> dict:
    payload = json.loads(asset_library.read_text(encoding="utf-8"))
    lib = payload.get("ASSET_LIBRARY") if isinstance(payload, dict) else None
    if not isinstance(lib, dict):
        raise ValueError("ASSET_LIBRARY missing")
    for record in lib.get("location_assets", []) if isinstance(lib.get("location_assets"), list) else []:
        if isinstance(record, dict) and record.get("asset_id") == location_asset_id:
            return record
    raise ValueError(f"location asset not found: {location_asset_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic scene GEO lock from authoritative S-location geometry")
    parser.add_argument("--asset-library", required=True)
    parser.add_argument("--scene-id", required=True)
    parser.add_argument("--location-asset-id", required=True)
    args = parser.parse_args()
    location = _load_location(Path(args.asset_library), args.location_asset_id)
    print(json.dumps(build_scene_geo_lock(args.scene_id, location), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
