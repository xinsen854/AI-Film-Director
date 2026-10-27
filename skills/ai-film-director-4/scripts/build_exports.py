#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
from pathlib import Path
from typing import Iterable

from render_asset_library import render_asset_library, validate_asset_library_payload
from render_storyboard import render_storyboard, validate_storyboard_payload
from story_coverage import story_coverage_enabled, validate_story_coverage
from render_story_coverage import render_story_coverage
from hard_delivery_qc import validate_hard_delivery
from validate_asset_files import validate_generated_asset_files
from validate_current_gu_only import validate_current_gu_only
from validate_continuity import validate_continuity
from qc_routing import write_qc_issues
from runtime_state import require_current_runtime_state
from validate_project_outputs import validate_project
from render_emotion_map import render_emotion_map as render_forge_emotion_map

DELIVERY_FILES = [
    '01_项目需求确认单.md',
    '02_剧本审查与修改结论.md',
    '03_正式编剧剧本.md',
    '04_整合导演剧本.md',
    '05_双层情绪规划图.html',
    '06_资产总表与详细生成提示词.md',
    '07_正式分镜与视频模型最终Prompt.md',
    '08_Story_Coverage_Ledger.html',
]
EPSILON = 0.01


class RoutedQCError(ValueError):
    pass


def _raise_qc_block(project_root: Path, label: str, errors: list[str]) -> None:
    write_qc_issues(project_root, errors)
    raise RoutedQCError(label + '：' + '; '.join(errors))


def _natural_key(path: Path):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r'(\d+)', str(path))]


def _required_file(path: Path, label: str) -> Path:
    if not path.is_file() or not path.read_text(encoding='utf-8', errors='replace').strip():
        raise FileNotFoundError(f'{label} missing or empty: {path}')
    return path


def _aggregate_required(files: Iterable[Path], target: Path, title: str) -> int:
    sources = [p for p in sorted(files, key=_natural_key) if p.is_file()]
    if not sources:
        raise FileNotFoundError(f'{title} source files missing')
    blocks = [f'# {title}', '']
    count = 0
    for source in sources:
        text = source.read_text(encoding='utf-8', errors='replace').strip()
        if not text:
            continue
        blocks.extend([text, '', '---', ''])
        count += 1
    if count == 0:
        raise FileNotFoundError(f'{title} source files are empty')
    target.write_text('\n'.join(blocks).rstrip(' \n-') + '\n', encoding='utf-8')
    return count


def _verify_delivery_gate(project_root: Path) -> None:
    brief_path = project_root / 'state' / 'project_brief.json'
    if brief_path.is_file():
        try:
            brief = json.loads(brief_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            raise ValueError('state/project_brief.json is not valid JSON') from exc
        execution_mode = str(brief.get('execution_mode') or 'FULL').upper()
        production_scope = str(brief.get('production_scope') or 'PROJECT').upper()
        if execution_mode == 'QUICK':
            raise ValueError(
                'QUICK_MODE_FORMAL_EXPORT_FORBIDDEN: QUICK validates only the requested scope; '
                'use FULL before claiming the formal eight-file delivery'
            )
        if production_scope != 'PROJECT':
            raise ValueError(
                'PRODUCTION_SCOPE_FORMAL_EXPORT_FORBIDDEN: formal eight-file delivery requires production_scope=PROJECT; '
                f'current production_scope={production_scope}'
            )
    qc_path = _required_file(project_root / 'FINAL_QC.md', 'FINAL_QC.md')
    qc_text = qc_path.read_text(encoding='utf-8', errors='replace')
    match = re.search(r'^##\s+Project Result\s*$\s*^(PASS|FAIL)\s*$', qc_text, flags=re.MULTILINE | re.IGNORECASE)
    if not match or match.group(1).upper() != 'PASS':
        raise ValueError('FINAL_QC.md Project Result must be PASS before final export')

    ledger_path = _required_file(project_root / 'PRODUCTION_LEDGER.json', 'PRODUCTION_LEDGER.json')
    try:
        ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise ValueError('PRODUCTION_LEDGER.json is not valid JSON') from exc
    if not isinstance(ledger, dict) or ledger.get('status') != 'COMPLETED':
        raise ValueError('PRODUCTION_LEDGER.json status must be COMPLETED before final export')

    scope = ledger.get('scope_type')
    coverage = ledger.get('coverage') if isinstance(ledger.get('coverage'), dict) else {}
    if scope == 'film_timeline':
        target = ledger.get('target_runtime_seconds')
        covered = coverage.get('covered_seconds')
        gaps = coverage.get('gaps')
        if not isinstance(target, (int, float)) or not isinstance(covered, (int, float)):
            raise ValueError('completed film ledger requires numeric target_runtime_seconds and coverage.covered_seconds')
        if abs(float(target) - float(covered)) > EPSILON:
            raise ValueError('completed film ledger coverage does not reach confirmed target runtime')
        if not isinstance(gaps, list) or gaps:
            raise ValueError('completed film ledger must have no coverage gaps')
    elif scope == 'episodes':
        target = ledger.get('target_episode_count')
        completed = coverage.get('completed_count')
        if not isinstance(target, int) or not isinstance(completed, int) or completed != target:
            raise ValueError('completed episode ledger coverage does not reach confirmed target episode count')
    else:
        raise ValueError(f'unsupported completed ledger scope_type: {scope}')

    if scope == 'film_timeline':
        expected_units = {str(x) for x in ledger.get('completed_units', [])}
        recorded_units = {str(item.get('unit_id')) for item in ledger.get('film_units', []) if isinstance(item, dict) and item.get('status') == 'COMPLETE'}
    else:
        expected_units = {str(x) for x in ledger.get('completed_episodes', [])}
        recorded_units = {str(item.get('episode_id')) for item in ledger.get('episodes', []) if isinstance(item, dict) and item.get('status') == 'COMPLETE'}
    if expected_units != recorded_units:
        raise ValueError(f'生产账本完成单元列表与账本明细不一致：列表={sorted(expected_units)} 明细={sorted(recorded_units)}')

    visible_specs = (
        ('screenplay', '*_LOCKED_SCREENPLAY.md', '_LOCKED_SCREENPLAY.md', '正式编剧剧本'),
        ('director', '*_INTEGRATED_DIRECTOR_SCREENPLAY.md', '_INTEGRATED_DIRECTOR_SCREENPLAY.md', '整合导演剧本'),
        ('storyboard', '*_STORYBOARD.md', '_STORYBOARD.md', '正式分镜'),
        ('storyboard', '*_STORYBOARD.json', '_STORYBOARD.json', '结构化分镜'),
    )
    for directory, pattern, suffix, label in visible_specs:
        base = project_root / directory
        actual_units = {path.name[:-len(suffix)] for path in base.glob(pattern)} if base.is_dir() else set()
        # 4.7 project-scoped films keep a project-level locked screenplay alongside PU files.
        # Only production-unit filenames participate in completed-unit equality.
        if directory == 'screenplay':
            actual_units = {uid for uid in actual_units if re.fullmatch(r'(?:PU|EP)\d+', uid, flags=re.IGNORECASE)}
        if actual_units != expected_units:
            raise ValueError(
                f'{label}与生产账本完成单元不一致：账本={sorted(expected_units)} 实际={sorted(actual_units)}'
            )

    if story_coverage_enabled(project_root):
        coverage_errors = validate_story_coverage(
            project_root, final_mode=True, require_persisted_match=True
        )
        if coverage_errors:
            _raise_qc_block(project_root, 'Story Coverage最终交付阻断', coverage_errors)

    hard_scope = 'project' if (project_root / 'state' / 'PROJECT_SCOPE.json').is_file() else 'legacy'
    hard_errors = validate_hard_delivery(project_root, scope=hard_scope)
    if hard_errors:
        _raise_qc_block(project_root, 'Final Hard QC阻断', hard_errors)

    gu_only_errors = validate_current_gu_only(project_root)
    if gu_only_errors:
        _raise_qc_block(project_root, 'CURRENT_GU_ONLY防污染阻断', gu_only_errors)

    continuity_errors = validate_continuity(project_root)
    if continuity_errors:
        _raise_qc_block(project_root, '连续性硬检查阻断', continuity_errors)

    asset_file_errors = validate_generated_asset_files(project_root)
    if asset_file_errors:
        _raise_qc_block(project_root, '真实资产文件校验阻断', asset_file_errors)


def _load_asset_payload(project_root: Path) -> dict:
    path = project_root / 'assets' / 'ASSET_LIBRARY.json'
    _required_file(path, 'ASSET_LIBRARY.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    lib = data.get('ASSET_LIBRARY') if isinstance(data, dict) else None
    if not isinstance(lib, dict):
        raise ValueError('ASSET_LIBRARY.json missing ASSET_LIBRARY object')
    return data


def _iter_visual_records(lib: dict):
    for group in ('character_assets', 'location_assets', 'prop_assets', 'g_assets'):
        for record in lib.get(group, []) or []:
            if isinstance(record, dict):
                yield record
    for record in lib.get('persistent_states', []) or []:
        if isinstance(record, dict):
            yield record


def _record_id(record: dict) -> str:
    return str(record.get('asset_id') or record.get('state_id') or '')


def _resolve_asset_file(project_root: Path, image_file: str) -> Path | None:
    if not image_file:
        return None
    raw = Path(image_file)
    candidates = [raw] if raw.is_absolute() else [project_root / raw, project_root / 'assets' / raw, project_root / 'assets' / 'generated' / raw.name]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _copy_generated_assets(project_root: Path, delivery_root: Path, lib: dict) -> dict[str, tuple[str, str]]:
    path_map: dict[str, tuple[str, str]] = {}
    target_dir = delivery_root / 'assets'
    used: set[str] = set()
    for record in _iter_visual_records(lib):
        if str(record.get('image_status') or '') != 'GENERATED':
            continue
        asset_id = _record_id(record)
        source_path = str(record.get('image_file') or '')
        source = _resolve_asset_file(project_root, source_path)
        if source is None:
            raise FileNotFoundError(f'asset {asset_id} marked GENERATED but image_file is missing')
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = source.name
        if filename in used or (target_dir / filename).exists():
            stem, suffix = source.stem, source.suffix
            n = 2
            while f'{stem}_{n}{suffix}' in used or (target_dir / f'{stem}_{n}{suffix}').exists():
                n += 1
            filename = f'{stem}_{n}{suffix}'
        used.add(filename)
        shutil.copy2(source, target_dir / filename)
        path_map[asset_id] = (source_path, f'assets/{filename}')
    if not path_map and target_dir.exists():
        shutil.rmtree(target_dir)
    return path_map


def _verify_renderer_locked_sources(project_root: Path, asset_md: Path, storyboard_files: list[Path]) -> None:
    asset_json = project_root / 'assets' / 'ASSET_LIBRARY.json'
    payload = json.loads(_required_file(asset_json, 'ASSET_LIBRARY.json').read_text(encoding='utf-8'))
    asset_errors = validate_asset_library_payload(payload)
    if asset_errors:
        raise ValueError('ASSET_LIBRARY.json validation failed: ' + '; '.join(asset_errors))
    if asset_md.read_text(encoding='utf-8') != render_asset_library(payload):
        raise ValueError('ASSET_LIBRARY.md is not the fixed Renderer output of ASSET_LIBRARY.json')

    for md_path in storyboard_files:
        json_path = md_path.with_suffix('.json')
        if not json_path.is_file():
            raise FileNotFoundError(f'structured storyboard JSON missing for {md_path.name}: {json_path}')
        data = json.loads(json_path.read_text(encoding='utf-8'))
        sb_errors = validate_storyboard_payload(data)
        if sb_errors:
            raise ValueError(f'{json_path.name} validation failed: ' + '; '.join(sb_errors))
        if md_path.read_text(encoding='utf-8') != render_storyboard(data):
            raise ValueError(f'{md_path.name} is not the fixed Renderer output of {json_path.name}')


def _delivery_asset_payload(payload: dict, path_map: dict[str, tuple[str, str]]) -> dict:
    out = copy.deepcopy(payload)
    lib = out['ASSET_LIBRARY']
    for record in _iter_visual_records(lib):
        asset_id = _record_id(record)
        if asset_id in path_map:
            record['image_file'] = path_map[asset_id][1]
    return out


def _rewrite_known_paths(value, replacements: dict[str, str]):
    if isinstance(value, str):
        result = value
        for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
            if old:
                result = result.replace(old, new)
        return result
    if isinstance(value, list):
        return [_rewrite_known_paths(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _rewrite_known_paths(item, replacements) for key, item in value.items()}
    return value


def _aggregate_delivery_storyboards(storyboard_files: list[Path], target: Path, path_map: dict[str, tuple[str, str]]) -> int:
    sources = [p for p in sorted(storyboard_files, key=_natural_key) if p.is_file()]
    if not sources:
        raise FileNotFoundError('正式分镜与视频生成Prompt source files missing')
    by_id = {asset_id: new for asset_id, (_, new) in path_map.items()}
    replacements = {old: new for old, new in path_map.values() if old}
    blocks = ['# 正式分镜与视频生成Prompt', '']
    count = 0
    for md_path in sources:
        json_path = md_path.with_suffix('.json')
        data = json.loads(json_path.read_text(encoding='utf-8'))
        delivery_data = _rewrite_known_paths(copy.deepcopy(data), replacements)
        for shot in delivery_data.get('edit_shots', []) if isinstance(delivery_data.get('edit_shots'), list) else []:
            if not isinstance(shot, dict):
                continue
            for call in shot.get('visual_asset_calls', []) if isinstance(shot.get('visual_asset_calls'), list) else []:
                if not isinstance(call, dict):
                    continue
                asset_id = str(call.get('asset_id') or '')
                if asset_id in by_id:
                    call['file'] = by_id[asset_id]
        errors = validate_storyboard_payload(delivery_data)
        if errors:
            raise ValueError(f'{json_path.name} delivery rewrite validation failed: ' + '; '.join(errors))
        rendered = render_storyboard(delivery_data).strip()
        document_title = '# 正式分镜与视频生成Prompt'
        if rendered.startswith(document_title):
            rendered = rendered[len(document_title):].lstrip('\n')
        blocks.extend([rendered, '', '---', ''])
        count += 1
    target.write_text('\n'.join(blocks).rstrip(' \n-') + '\n', encoding='utf-8')
    return count



def _verify_full_pipeline_dependencies(project_root: Path) -> None:
    ledger_path = project_root / 'PRODUCTION_LEDGER.json'
    if not ledger_path.is_file():
        raise ValueError('PIPELINE_DEPENDENCY：缺少PRODUCTION_LEDGER.json')
    ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
    if ledger.get('scope_type') == 'film_timeline':
        units = [str(x) for x in ledger.get('completed_units', []) if isinstance(x, str)]
    elif ledger.get('scope_type') == 'episodes':
        units = [str(x) for x in ledger.get('completed_episodes', []) if isinstance(x, str)]
    else:
        units = []
    project_errors = validate_project(project_root)
    if project_errors:
        raise ValueError('PIPELINE_DEPENDENCY：项目上游生产链未完成：' + '; '.join(project_errors))
    for unit_id in units:
        unit_errors = validate_project(project_root, unit_id)
        if unit_errors:
            raise ValueError(f'PIPELINE_DEPENDENCY：{unit_id}上游生产链未完成：' + '; '.join(unit_errors))

def _build_exports_impl(project_root: str | Path) -> dict:
    root = Path(project_root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)

    # Preserve AFD hard delivery gates first so Owner Layer routing still reports the
    # smallest responsible production layer (for example ASSET) instead of being
    # masked by a later emotion/export prerequisite.
    _verify_delivery_gate(root)

    forge_audit = root / 'state' / 'forge_locked_audit.json'
    if not forge_audit.is_file():
        raise ValueError(f'PIPELINE_DEPENDENCY：缺少Forge locked audit：{forge_audit}')
    # Formal 05 is always regenerated from the locked Forge audit immediately before
    # project consistency validation/export. A manually stale/tampered HTML therefore
    # cannot become the delivered authority.
    render_forge_emotion_map(root)

    _verify_full_pipeline_dependencies(root)

    brief = _required_file(root / 'PROJECT_BRIEF.md', '项目需求确认单')
    review = _required_file(root / 'SCRIPT_REVIEW.md', '剧本审查与修改结论')
    emotion = _required_file(root / 'AUDIENCE_EMOTION_MAP.html', '双层情绪规划图')
    coverage_html = render_story_coverage(root)
    _required_file(coverage_html, 'Story Coverage Ledger HTML')
    asset_md = _required_file(root / 'assets' / 'ASSET_LIBRARY.md', '资产总表与详细生成提示词')
    asset_payload = _load_asset_payload(root)
    lib = asset_payload['ASSET_LIBRARY']

    screenplay = list((root / 'screenplay').glob('*_LOCKED_SCREENPLAY.md')) if (root / 'screenplay').is_dir() else []
    director = list((root / 'director').glob('*_INTEGRATED_DIRECTOR_SCREENPLAY.md')) if (root / 'director').is_dir() else []
    storyboard = list((root / 'storyboard').glob('*_STORYBOARD.md')) if (root / 'storyboard').is_dir() else []
    if not screenplay:
        raise FileNotFoundError('正式编剧剧本 source files missing')
    if not director:
        raise FileNotFoundError('整合导演剧本 source files missing')
    if not storyboard:
        raise FileNotFoundError('正式分镜与视频生成Prompt source files missing')

    _verify_renderer_locked_sources(root, asset_md, storyboard)

    delivery = root / '交付包'
    if delivery.exists():
        shutil.rmtree(delivery)
    delivery.mkdir(parents=True)

    shutil.copy2(brief, delivery / DELIVERY_FILES[0])
    shutil.copy2(review, delivery / DELIVERY_FILES[1])
    screenplay_count = _aggregate_required(screenplay, delivery / DELIVERY_FILES[2], '正式编剧剧本')
    director_count = _aggregate_required(director, delivery / DELIVERY_FILES[3], '整合导演剧本')
    shutil.copy2(emotion, delivery / DELIVERY_FILES[4])

    path_map = _copy_generated_assets(root, delivery, lib)
    delivery_asset_payload = _delivery_asset_payload(asset_payload, path_map)
    (delivery / DELIVERY_FILES[5]).write_text(render_asset_library(delivery_asset_payload), encoding='utf-8')
    storyboard_count = _aggregate_delivery_storyboards(storyboard, delivery / DELIVERY_FILES[6], path_map)
    shutil.copy2(coverage_html, delivery / DELIVERY_FILES[7])

    top_files = sorted(p.name for p in delivery.iterdir() if p.is_file())
    if top_files != sorted(DELIVERY_FILES):
        raise RuntimeError(f'unexpected delivery file set: {top_files}')

    return {
        'delivery_dir': str(delivery),
        'delivery_files': len(top_files),
        'screenplay_units': screenplay_count,
        'director_units': director_count,
        'storyboard_units': storyboard_count,
        'generated_assets': len(path_map),
    }



def build_exports(project_root: str | Path) -> dict:
    root = Path(project_root).resolve()
    try:
        require_current_runtime_state(root)
        return _build_exports_impl(root)
    except RoutedQCError:
        raise
    except Exception as exc:
        if root.is_dir():
            write_qc_issues(root, [f'DELIVERY_GATE_ERROR：{exc}'])
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description='生成融合版用户交付包：八个正式文件 + 实际生成资产')
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()
    try:
        require_current_runtime_state(args.project_root)
        summary = build_exports(args.project_root)
    except Exception as exc:
        print(f'FAIL: {exc}')
        return 1
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
