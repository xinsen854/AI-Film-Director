#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from normalize_source import read_source
from runtime_state import AUTHORITY_PROFILE, CURRENT_RUNTIME_STATE_VERSION

RUNTIME_DIRS = (
    'source',
    'screenplay',
    'director',
    'assets/generated',
    'storyboard',
    'exports',
    'state/units',
    'state/audience_causal',
    'state/director',
    'state/scene_intelligence',
    'state/router',
    'state/director_craft',
    'state/spatial_narrative',
    'state/cineweaver_qc',
)

MATURITIES = {'idea', 'outline', 'treatment', 'screenplay', 'existing_project'}


def infer_maturity(text: str, source_name: str = '') -> str:
    sample = text[:12000]
    lower_name = source_name.lower()
    if any(token in lower_name for token in ('screenplay', 'script', '剧本')):
        return 'screenplay'
    scene_signals = len(re.findall(r'(?im)^\s*(sc\d+|scene\s+\d+|第[一二三四五六七八九十百0-9]+场)', sample))
    dialogue_signals = len(re.findall(r'(?m)^\s*[^\n]{1,16}\s*[：:]\s*[^\n]+$', sample))
    if scene_signals >= 2 and dialogue_signals >= 3:
        return 'screenplay'
    if len(sample) >= 5000:
        return 'treatment'
    if len(sample) >= 800 or re.search(r'(?m)^\s*(第.+[集幕章]|EP\s*\d+)', sample, re.I):
        return 'outline'
    return 'idea'


def create_project(
    input_path: str | Path,
    output_root: str | Path,
    project_id: str,
    source_maturity: str = 'auto',
) -> Path:
    source = Path(input_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    maturity = infer_maturity(read_source(source), source.name) if source_maturity == 'auto' else source_maturity
    if maturity not in MATURITIES:
        raise ValueError(f'无效 source_maturity: {source_maturity}')

    project_root = Path(output_root).resolve() / project_id
    if project_root.exists() and any(project_root.iterdir()):
        raise FileExistsError(f'项目目录非空，拒绝覆盖: {project_root}')
    project_root.mkdir(parents=True, exist_ok=True)
    for relative in RUNTIME_DIRS:
        (project_root / relative).mkdir(parents=True, exist_ok=True)

    original_name = 'original' + (source.suffix.lower() or '.txt')
    shutil.copy2(source, project_root / 'source' / original_name)
    normalized = read_source(source)
    (project_root / 'source' / 'normalized_input.md').write_text(normalized, encoding='utf-8')

    state = {
        'project_id': project_id,
        'source_maturity': maturity,
        'status': 'INITIALIZED',
        'current_phase': 'project-intake',
        'current_unit': None,
        'confirmed_brief': False,
        'story_authority_ready': False,
        'asset_library_ready': False,
        'scene_intelligence_ready': False,
        'director_craft_ready': False,
        'completed_units': [],
        'runtime_state_version': CURRENT_RUNTIME_STATE_VERSION,
    }
    (project_root / 'state' / 'pipeline_state.json').write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    (project_root / 'state' / 'runtime_contract.json').write_text(
        json.dumps({
            'runtime_state_version': CURRENT_RUNTIME_STATE_VERSION,
            'authority_profile': AUTHORITY_PROFILE,
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    return project_root


def main() -> int:
    parser = argparse.ArgumentParser(description='Create the runtime skeleton for one film project')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output-root', default='projects')
    parser.add_argument('--project-id', required=True)
    parser.add_argument('--source-maturity', default='auto', choices=['auto', *sorted(MATURITIES)])
    args = parser.parse_args()
    root = create_project(args.input, args.output_root, args.project_id, args.source_maturity)
    print(root)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
