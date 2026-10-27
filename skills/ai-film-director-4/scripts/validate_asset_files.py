#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from PIL import Image, UnidentifiedImageError
except Exception:
    Image = None
    UnidentifiedImageError = Exception

VALID_STATUSES = {'GENERATED', 'PROMPT_ONLY', 'FAILED', 'MISSING'}
VISUAL_GROUPS = ('character_assets', 'location_assets', 'prop_assets', 'g_assets')
METADATA_FIELDS = ('file_size', 'width', 'height', 'mime_type', 'sha256')


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _iter_visual_records(lib: dict):
    for group in VISUAL_GROUPS:
        records = lib.get(group)
        if not isinstance(records, list):
            continue
        for record in records:
            if isinstance(record, dict):
                yield record
                metadata = record.get('downstream_metadata')
                scale = metadata.get('scale_reference') if isinstance(metadata, dict) else None
                if isinstance(scale, dict):
                    scale_record = dict(scale)
                    scale_record['asset_id'] = str(scale.get('reference_id') or 'UNKNOWN_SCALE_REFERENCE')
                    yield scale_record
    states = lib.get('persistent_states')
    if isinstance(states, list):
        for record in states:
            if isinstance(record, dict):
                yield record


def _record_id(record: dict) -> str:
    return str(record.get('asset_id') or record.get('state_id') or 'UNKNOWN_ASSET')


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_generated_file(root: Path, value: object) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, 'missing'
    project = root.resolve()
    generated_root = (project / 'assets' / 'generated').resolve()
    raw = Path(value)
    candidate = raw if raw.is_absolute() else project / raw
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(generated_root)
    except (OSError, ValueError):
        return None, 'escape'
    if not resolved.is_file():
        return None, 'missing'
    return resolved, None


def _inspect_image(path: Path) -> tuple[dict | None, str | None]:
    try:
        if path.stat().st_size <= 0:
            return None, '图片文件为空'
    except OSError as exc:
        return None, f'无法读取图片文件：{exc}'
    if Image is None:
        return None, '图像解码器不可用'
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
            fmt = (image.format or '').upper()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        return None, f'图片无法解码：{exc}'
    if width <= 0 or height <= 0:
        return None, '图片宽高非法'
    mime_by_format = {'PNG': 'image/png', 'JPEG': 'image/jpeg', 'WEBP': 'image/webp'}
    mime_type = mime_by_format.get(fmt)
    if mime_type is None:
        return None, f'不支持的图片格式：{fmt or "UNKNOWN"}'
    allowed_ext = {'PNG': {'.png'}, 'JPEG': {'.jpg', '.jpeg'}, 'WEBP': {'.webp'}}[fmt]
    if path.suffix.lower() not in allowed_ext:
        return None, f'文件扩展名与真实图片格式不一致：{path.suffix}/{fmt}'
    return {
        'file_size': path.stat().st_size,
        'width': int(width),
        'height': int(height),
        'mime_type': mime_type,
        'sha256': _sha256(path),
    }, None


def validate_generated_asset_files(project_root: str | Path) -> list[str]:
    root = Path(project_root).resolve()
    payload = _load(root / 'assets' / 'ASSET_LIBRARY.json')
    lib = payload.get('ASSET_LIBRARY') if isinstance(payload.get('ASSET_LIBRARY'), dict) else None
    if lib is None:
        return []  # ASSET_LIBRARY存在性/结构由既有资产链和Final Delivery负责，不复制第二套。

    errors: list[str] = []
    for record in _iter_visual_records(lib):
        rid = _record_id(record)
        status = str(record.get('image_status') or 'MISSING')
        if status not in VALID_STATUSES:
            errors.append(f'ASSET_STATUS_INVALID：{rid} image_status非法：{status}')
            continue
        if status != 'GENERATED':
            continue

        path, path_error = _resolve_generated_file(root, record.get('image_file'))
        if path_error == 'escape':
            errors.append(f'ASSET_FILE_INVALID：{rid} image_file必须位于 assets/generated：{record.get("image_file")}')
            continue
        if path is None:
            errors.append(f'ASSET_FILE_INVALID：{rid} 标记GENERATED但真实图片文件不存在')
            continue

        metadata, inspect_error = _inspect_image(path)
        if inspect_error:
            errors.append(f'ASSET_FILE_INVALID：{rid} {inspect_error}')
            continue
        assert metadata is not None
        for key in METADATA_FIELDS:
            recorded = record.get(key)
            if recorded in (None, ''):
                errors.append(f'ASSET_FILE_INVALID：{rid} 已生成资产缺少验证字段 {key}')
            elif recorded != metadata[key]:
                errors.append(f'ASSET_FILE_INVALID：{rid} {key}与真实文件不一致：记录={recorded} 实际={metadata[key]}')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate real generated visual asset files without changing CineWeaver asset definitions')
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()
    errors = validate_generated_asset_files(args.project_root)
    if errors:
        print('FAIL')
        for error in errors:
            print('-', error)
        return 1
    print('PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
