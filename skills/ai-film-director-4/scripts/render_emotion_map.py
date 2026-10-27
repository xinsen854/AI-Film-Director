#!/usr/bin/env python3
"""Canonical formal emotion renderer for the fused package.

This is a thin integration wrapper around the untouched Forge v1.1.4 renderer
embedded under references/forge/source/emotion-story-forge/. It never renders
from the AFD compatibility projection.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
from pathlib import Path
from types import ModuleType

SKILL_ROOT = Path(__file__).resolve().parents[1]
FORGE_RENDERER_PATH = (
    SKILL_ROOT / 'references' / 'forge' / 'source' / 'emotion-story-forge' /
    'scripts' / 'render_emotion_map.py'
)


def _load_forge_renderer() -> ModuleType:
    if not FORGE_RENDERER_PATH.is_file():
        raise FileNotFoundError(f'embedded Forge renderer missing: {FORGE_RENDERER_PATH}')
    spec = importlib.util.spec_from_file_location('afd_embedded_forge_emotion_renderer', FORGE_RENDERER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot load embedded Forge renderer: {FORGE_RENDERER_PATH}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_FORGE = _load_forge_renderer()
validate_emotion_payload = _FORGE.validate_payload
validate_payload = _FORGE.validate_payload
derive_render_model = _FORGE.derive_render_model


def render(input_path: str | Path, output_path: str | Path) -> Path:
    source = Path(input_path).resolve()
    target = Path(output_path).resolve()
    _FORGE.render(source, target)
    return target


def render_emotion_html(payload: dict) -> str:
    """Return exact Forge renderer output for one already-authored audit payload."""
    with tempfile.TemporaryDirectory(prefix='forge_emotion_render_') as tmp:
        tmp_root = Path(tmp)
        source = tmp_root / 'audit.json'
        target = tmp_root / 'map.html'
        source.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        _FORGE.render(source, target)
        return target.read_text(encoding='utf-8')


def render_emotion_map(project_root: str | Path) -> Path:
    root = Path(project_root).resolve()
    source = root / 'state' / 'forge_locked_audit.json'
    target = root / 'AUDIENCE_EMOTION_MAP.html'
    if not source.is_file():
        raise FileNotFoundError(f'Forge locked audit missing: {source}')
    _FORGE.render(source, target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description='Render formal 05 only from Forge locked audit')
    parser.add_argument('input_json', nargs='?')
    parser.add_argument('output_html', nargs='?')
    parser.add_argument('--project-root')
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    try:
        if args.project_root:
            root = Path(args.project_root).resolve()
            source = root / 'state' / 'forge_locked_audit.json'
            output = root / 'AUDIENCE_EMOTION_MAP.html'
        else:
            if not args.input_json:
                raise ValueError('input_json or --project-root is required')
            source = Path(args.input_json).resolve()
            output = Path(args.output_html).resolve() if args.output_html else None
        payload = json.loads(source.read_text(encoding='utf-8'))
        errors = _FORGE.validate_payload(payload)
        if errors:
            raise ValueError('Forge locked-audit schema validation failed: ' + '; '.join(errors))
        if not args.validate_only:
            if output is None:
                raise ValueError('output_html is required unless --validate-only')
            _FORGE.render(source, output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f'FAIL: {exc}')
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
