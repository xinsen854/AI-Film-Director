#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / 'scripts'


def _run(script: str, *args: str, cwd: Path) -> None:
    command = [sys.executable, str(SCRIPTS / script), *args]
    print('RUN:', ' '.join(command))
    result = subprocess.run(command, cwd=str(cwd), check=False)
    if result.returncode != 0:
        raise RuntimeError(f'{script} failed with exit code {result.returncode}')


def _load_mode(project_root: Path) -> str:
    brief_path = project_root / 'state' / 'project_brief.json'
    if not brief_path.is_file():
        raise FileNotFoundError(f'missing project brief: {brief_path}')
    brief = json.loads(brief_path.read_text(encoding='utf-8'))
    mode = str(brief.get('execution_mode') or 'FULL').upper()
    if mode not in {'FULL', 'QUICK'}:
        raise ValueError(f'unsupported execution_mode: {mode}')
    return mode


def _load_production_scope(project_root: Path) -> str:
    brief_path = project_root / 'state' / 'project_brief.json'
    if not brief_path.is_file():
        raise FileNotFoundError(f'missing project brief: {brief_path}')
    brief = json.loads(brief_path.read_text(encoding='utf-8'))
    scope = str(brief.get('production_scope') or 'PROJECT').upper()
    if scope not in {'PROJECT', 'UNIT', 'PILOT'}:
        raise ValueError(f'unsupported production_scope: {scope}')
    return scope


def run_pipeline(project_root: str | Path) -> str:
    root = Path(project_root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f'project root not found: {root}')
    mode = _load_mode(root)
    production_scope = _load_production_scope(root)

    forge_audit = root / 'state' / 'forge_locked_audit.json'
    emotion_html = root / 'AUDIENCE_EMOTION_MAP.html'
    if forge_audit.is_file():
        _run('compile_forge_handoff.py', '--stage', 'validate-alignment', '--project-root', str(root), cwd=root)
        _run('render_emotion_map.py', str(forge_audit), str(emotion_html), cwd=root)
    elif mode == 'FULL':
        raise FileNotFoundError(f'missing FULL-mode Forge locked audit: {forge_audit}')

    asset_json = root / 'assets' / 'ASSET_LIBRARY.json'
    if asset_json.is_file():
        _run(
            'render_asset_library.py', '--input', str(asset_json),
            '--output', str(root / 'assets' / 'ASSET_LIBRARY.md'), cwd=root,
        )
        _run('validate_asset_files.py', '--project-root', str(root), cwd=root)
    elif mode == 'FULL':
        raise FileNotFoundError(f'missing FULL-mode asset library: {asset_json}')

    storyboard_dir = root / 'storyboard'
    storyboards = sorted(storyboard_dir.glob('*_STORYBOARD.json')) if storyboard_dir.is_dir() else []
    if not storyboards and mode == 'FULL':
        raise FileNotFoundError(f'no structured storyboards found in {storyboard_dir}')
    for source in storyboards:
        target = source.with_suffix('.md')
        _run('validate_cineweaver_storyboard.py', '--input', str(source), cwd=root)
        _run('render_storyboard.py', '--input', str(source), '--output', str(target), cwd=root)

    if mode == 'QUICK':
        print(f'PASS: QUICK pipeline validated available artifacts for production_scope={production_scope}; formal eight-file export was not claimed.')
        return mode

    if production_scope != 'PROJECT':
        _run('hard_delivery_qc.py', '--project-root', str(root), cwd=root)
        print(f'PASS: FULL pipeline validated production_scope={production_scope}; project-complete export was not claimed.')
        return mode

    hard_args = ('--project-root', str(root), '--scope', 'project') if (root / 'state' / 'PROJECT_SCOPE.json').is_file() else ('--project-root', str(root))
    _run('hard_delivery_qc.py', *hard_args, cwd=root)
    _run('build_exports.py', '--project-root', str(root), cwd=root)
    print('PASS: FULL + PROJECT pipeline completed and formal export gate passed.')
    return mode


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Run AI Film Director render, validation, QC and export stages in the required order.'
    )
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()
    try:
        run_pipeline(args.project_root)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f'FAIL: {exc}')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
