#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

COVERAGE_NAME = 'STORY_COVERAGE_LEDGER.json'


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def story_coverage_enabled(project_root: str | Path) -> bool:
    root = Path(project_root).resolve()
    if (root / 'state' / 'story_authority.json').is_file():
        return True
    state = _load(root / 'state' / 'pipeline_state.json')
    return state.get('story_authority_ready') is True


def _natural_key(value: str) -> list[Any]:
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r'(\d+)', value)]


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)


def _flatten_text(value: Any) -> str:
    return '\n'.join(text for text in _walk_strings(value) if text)


def _normalize_dialogue(value: Any) -> str:
    text = _flatten_text(value).lower()
    return re.sub(r'[\s\u3000，。！？；：、“”‘’「」『』（）()\[\]【】,.!?;:\-—_]+', '', text)


def _coverage_refs(shot: dict) -> tuple[set[str], set[str]]:
    coverage = shot.get('coverage') if isinstance(shot.get('coverage'), dict) else {}
    source = shot.get('source') if isinstance(shot.get('source'), dict) else {}

    atom_values = (
        coverage.get('story_atom_ids'),
        coverage.get('source_atoms'),
        source.get('story_atom_ids'),
        source.get('source_atoms'),
        shot.get('source_atoms'),
    )
    info_values = (
        coverage.get('revealed_info_ids'),
        coverage.get('information_ids'),
        source.get('revealed_info_ids'),
        source.get('information_ids'),
    )

    atoms: set[str] = set()
    infos: set[str] = set()
    for values in atom_values:
        if isinstance(values, list):
            atoms.update(str(x).strip() for x in values if isinstance(x, str) and x.strip())
    for values in info_values:
        if isinstance(values, list):
            infos.update(str(x).strip() for x in values if isinstance(x, str) and x.strip())
    return atoms, infos


def _storyboards(root: Path) -> list[tuple[str, dict]]:
    base = root / 'storyboard'
    if not base.is_dir():
        return []
    out: list[tuple[str, dict]] = []
    paths = sorted(base.glob('*_STORYBOARD.json'), key=lambda p: _natural_key(p.name))
    suffix = '_STORYBOARD.json'
    for path in paths:
        data = _load(path)
        if data:
            out.append((path.name[:-len(suffix)], data))
    return out


def _unit_scene_key(unit_id: str, scene_id: str) -> tuple[str, int, int] | None:
    unit_match = re.fullmatch(r'(EP|PU)(\d+)', str(unit_id).strip(), re.I)
    scene_match = re.fullmatch(r'SC(\d+)', str(scene_id).strip(), re.I)
    if not unit_match or not scene_match:
        return None
    return (unit_match.group(1).upper(), int(unit_match.group(2)), int(scene_match.group(1)))


def _marker_key(marker: Any, default_unit: str | None = None) -> tuple[str, int, int] | None:
    if not isinstance(marker, str) or not marker.strip():
        return None
    text = marker.upper()
    unit_match = re.search(r'\b(EP|PU)\s*(\d+)\b', text)
    scene_match = re.search(r'\bSC\s*(\d+)\b', text)
    unit_id = f'{unit_match.group(1)}{unit_match.group(2)}' if unit_match else default_unit
    scene_id = f'SC{scene_match.group(1)}' if scene_match else None
    if unit_id and scene_id:
        return _unit_scene_key(unit_id, scene_id)
    return None


def _marker_unit_id(marker: Any) -> str:
    if not isinstance(marker, str) or not marker.strip():
        return ''
    match = re.search(r'\b(EP|PU)\s*(\d+)\b', marker.upper())
    return f'{match.group(1)}{match.group(2)}' if match else ''


def _timeline(root: Path) -> tuple[list[dict], dict[str, dict]]:
    entries: list[dict] = []
    gu_map: dict[str, dict] = {}
    for unit_id, payload in _storyboards(root):
        for gu in payload.get('generation_units', []) if isinstance(payload.get('generation_units'), list) else []:
            if isinstance(gu, dict) and gu.get('generation_unit_id'):
                gu_map[f'{unit_id}:{gu["generation_unit_id"]}'] = gu
        for index, shot in enumerate(payload.get('edit_shots', []) if isinstance(payload.get('edit_shots'), list) else []):
            if not isinstance(shot, dict):
                continue
            atom_ids, info_ids = _coverage_refs(shot)
            scene_id = str(shot.get('scene_id') or '')
            gu_id = str(shot.get('generation_unit_id') or '')
            gu = gu_map.get(f'{unit_id}:{gu_id}', {})
            entries.append({
                'unit_id': unit_id,
                'scene_id': scene_id,
                'shot_id': str(shot.get('edit_shot_id') or ''),
                'generation_unit_id': gu_id,
                'atom_ids': atom_ids,
                'revealed_info_ids': info_ids,
                'shot': shot,
                'gu': gu,
                'text': _flatten_text({'shot': shot, 'gu': gu}),
                'location_key': _unit_scene_key(unit_id, scene_id),
                'ordinal': len(entries),
                'shot_index': index,
            })
    return entries, gu_map


def _dialogue_is_executed(atom_content: str, entries: list[dict]) -> bool:
    wanted = _normalize_dialogue(atom_content)
    if not entries:
        return False
    for entry in entries:
        shot_dialogue = _normalize_dialogue(entry['shot'].get('dialogue_execution'))
        gu_dialogue = _normalize_dialogue([
            phase.get('dialogue_execution')
            for phase in entry['gu'].get('phases', [])
            if isinstance(phase, dict)
        ]) if isinstance(entry.get('gu'), dict) else ''
        if wanted:
            if wanted in shot_dialogue and wanted in gu_dialogue:
                return True
        elif shot_dialogue and gu_dialogue:
            return True
    return False


def _matches_marker(entry: dict, marker: Any) -> bool:
    if not isinstance(marker, str) or not marker.strip():
        return False
    text = marker.upper()
    unit_match = re.search(r'\b(EP|PU)\s*(\d+)\b', text)
    scene_match = re.search(r'\bSC\s*(\d+)\b', text)
    if unit_match:
        expected_unit = f'{unit_match.group(1)}{unit_match.group(2)}'
        if str(entry.get('unit_id')).upper() != expected_unit:
            return False
    if scene_match:
        expected_scene = f'SC{scene_match.group(1)}'
        if str(entry.get('scene_id')).upper() != expected_scene:
            return False
    return bool(unit_match or scene_match)


def _completed_units(root: Path) -> set[str]:
    ledger = _load(root / 'PRODUCTION_LEDGER.json')
    return {
        str(item)
        for key in ('completed_units', 'completed_episodes')
        for item in ledger.get(key, []) if isinstance(ledger.get(key), list) and str(item)
    }


def _production_status(*, covered: bool, unit_id: str, completed: set[str], confirmed: set[str], coverage_id: str, confirm_unit: str | None) -> str:
    if not covered:
        return 'UNCOVERED'
    if coverage_id in confirmed or (confirm_unit and unit_id == confirm_unit):
        return 'CONFIRMED'
    if unit_id and unit_id in completed:
        return 'PRODUCED'
    return 'PLANNED'


def build_story_coverage(project_root: str | Path, *, confirm_unit: str | None = None) -> dict:
    root = Path(project_root).resolve()
    authority = _load(root / 'state' / 'story_authority.json')
    information = _load(root / 'state' / 'information_ledger.json')
    brief = _load(root / 'state' / 'project_brief.json')
    entries, _ = _timeline(root)
    completed = _completed_units(root)
    previous = _load(root / 'state' / COVERAGE_NAME)
    confirmed = {
        str(item.get('coverage_id')) for item in previous.get('items', [])
        if isinstance(item, dict) and item.get('status') == 'CONFIRMED' and item.get('coverage_id')
    }

    atoms = [
        item for item in authority.get('atoms', [])
        if isinstance(item, dict) and item.get('locked') is True and isinstance(item.get('atom_id'), str) and item.get('atom_id').strip()
    ]
    atom_records: list[dict] = []
    covered_atom_ids: list[str] = []
    uncovered_atom_ids: list[str] = []
    dialogue_records: list[dict] = []

    for atom in atoms:
        atom_id = str(atom['atom_id']).strip()
        unit_id = str(atom.get('unit_id') or '')
        scene_id = str(atom.get('scene_id') or '')
        atom_type = str(atom.get('type') or '')
        required = atom_type == 'dialogue' or atom.get('visual_coverage_required') is not False
        matched = [entry for entry in entries if atom_id in entry['atom_ids']]
        shot_ids = list(dict.fromkeys(entry['shot_id'] for entry in matched if entry['shot_id']))
        gu_ids = list(dict.fromkeys(entry['generation_unit_id'] for entry in matched if entry['generation_unit_id']))
        scene_match = any(entry['scene_id'] == scene_id and (not unit_id or entry['unit_id'] == unit_id) for entry in entries)
        dialogue_ok = True
        if atom_type == 'dialogue':
            dialogue_ok = _dialogue_is_executed(str(atom.get('content') or ''), matched)
        covered = (not required) or (bool(matched) and scene_match and dialogue_ok)
        status = 'NOT_REQUIRED' if not required else ('COVERED' if covered else 'UNCOVERED')
        production_status = _production_status(
            covered=covered, unit_id=unit_id, completed=completed, confirmed=confirmed,
            coverage_id=atom_id, confirm_unit=confirm_unit,
        )
        record = {
            'atom_id': atom_id,
            'unit_id': unit_id or None,
            'scene_id': scene_id or None,
            'type': atom_type or None,
            'required': required,
            'shot_ids': shot_ids,
            'generation_unit_ids': gu_ids,
            'status': status,
            'production_status': production_status,
            'content': str(atom.get('content') or ''),
        }
        atom_records.append(record)
        if required:
            (covered_atom_ids if covered else uncovered_atom_ids).append(atom_id)
        if atom_type == 'dialogue':
            dialogue_records.append({
                'atom_id': atom_id,
                'unit_id': unit_id or None,
                'scene_id': scene_id or None,
                'shot_ids': shot_ids,
                'generation_unit_ids': gu_ids,
                'status': 'COVERED' if covered else 'UNCOVERED',
            })

    scene_ids = sorted({str(atom.get('scene_id')) for atom in atoms if atom.get('scene_id')}, key=_natural_key)
    covered_scene_ids = [
        scene_id for scene_id in scene_ids
        if any(entry['scene_id'] == scene_id for entry in entries)
    ]
    missing_scene_ids = [scene_id for scene_id in scene_ids if scene_id not in covered_scene_ids]

    info_records: list[dict] = []
    early_info_ids: list[str] = []
    uncovered_reveal_ids: list[str] = []
    for item in information.get('items', []) if isinstance(information.get('items'), list) else []:
        if not isinstance(item, dict) or not item.get('info_id'):
            continue
        info_id = str(item['info_id'])
        status = str(item.get('status') or '')
        planned = item.get('planned_reveal') or item.get('earliest_fair_reveal')
        actual = item.get('actual_reveal')
        planned_key = _marker_key(planned)
        actual_key = _marker_key(actual)
        reveal_entries = [entry for entry in entries if info_id in entry['revealed_info_ids']]
        reveal_shot_ids = [entry['shot_id'] for entry in reveal_entries if entry['shot_id']]

        early_evidence: list[str] = []
        for entry in entries:
            entry_key = entry.get('location_key')
            before_planned = planned_key is not None and entry_key is not None and entry_key < planned_key
            if not before_planned:
                continue
            if info_id in entry['revealed_info_ids']:
                early_evidence.append(f'{entry["unit_id"]}/{entry["scene_id"]}/{entry["shot_id"]}:revealed_info_ids')
            for literal in item.get('protected_literals', []) if isinstance(item.get('protected_literals'), list) else []:
                if isinstance(literal, str) and literal and literal in entry['text']:
                    early_evidence.append(f'{entry["unit_id"]}/{entry["scene_id"]}/{entry["shot_id"]}:protected_literal={literal}')

        if actual_key is not None and planned_key is not None and actual_key < planned_key:
            early_evidence.append(f'actual_reveal={actual} earlier_than_planned={planned}')
        earliest_key = _marker_key(item.get('earliest_fair_reveal'))
        if actual_key is not None and earliest_key is not None and actual_key < earliest_key:
            early_evidence.append(f'actual_reveal={actual} earlier_than_earliest_fair={item.get("earliest_fair_reveal")}')

        reveal_required = status in {'REVEALED', 'REINTERPRETED'} and bool(actual)
        actual_location_entries = [entry for entry in entries if _matches_marker(entry, actual)] if actual else []
        reveal_covered = (not reveal_required) or any(entry in actual_location_entries for entry in reveal_entries)
        if early_evidence:
            early_info_ids.append(info_id)
        if reveal_required and not reveal_covered:
            uncovered_reveal_ids.append(info_id)
        info_records.append({
            'info_id': info_id,
            'status': status,
            'planned_reveal': planned,
            'actual_reveal': actual,
            'reveal_shot_ids': reveal_shot_ids,
            'reveal_covered': reveal_covered,
            'early_reveal_evidence': list(dict.fromkeys(early_evidence)),
        })

    required_atoms = [record for record in atom_records if record['required']]
    dialogue_missing = [record['atom_id'] for record in dialogue_records if record['status'] != 'COVERED']
    result = {
        'schema_version': '1.0',
        'project_id': str(brief.get('project_id') or root.name),
        'enabled': story_coverage_enabled(root),
        'story_atoms': {
            'required_atom_count': len(required_atoms),
            'covered_atom_count': len(covered_atom_ids),
            'coverage_percentage': 100.0 if not required_atoms else round(len(covered_atom_ids) / len(required_atoms) * 100.0, 4),
            'covered_atom_ids': covered_atom_ids,
            'uncovered_atom_ids': uncovered_atom_ids,
            'items': atom_records,
        },
        'scenes': {
            'required_scene_ids': scene_ids,
            'covered_scene_ids': covered_scene_ids,
            'missing_scene_ids': missing_scene_ids,
        },
        'dialogues': {
            'required_dialogue_atom_ids': [record['atom_id'] for record in dialogue_records],
            'covered_dialogue_atom_ids': [record['atom_id'] for record in dialogue_records if record['status'] == 'COVERED'],
            'missing_dialogue_atom_ids': dialogue_missing,
            'items': dialogue_records,
        },
        'information': {
            'early_reveal_info_ids': list(dict.fromkeys(early_info_ids)),
            'uncovered_reveal_info_ids': list(dict.fromkeys(uncovered_reveal_ids)),
            'items': info_records,
        },
    }
    flat_items: list[dict] = []
    type_to_category = {
        'dialogue': 'dialogue', 'action': 'action', 'reveal': 'reveal', 'setup': 'setup',
        'foreshadowing': 'setup', 'payoff': 'payoff', 'information': 'information',
    }
    for record in atom_records:
        flat_items.append({
            'coverage_id': record['atom_id'],
            'category': type_to_category.get(str(record.get('type') or '').lower(), 'story_atom'),
            'content': record.get('content') or record['atom_id'],
            'unit_id': record.get('unit_id'), 'scene_id': record.get('scene_id'),
            'status': record['production_status'],
            'evidence': [*record.get('shot_ids', []), *record.get('generation_unit_ids', [])],
        })
    for scene_id in scene_ids:
        covered = scene_id in covered_scene_ids
        scene_entries = [entry for entry in entries if entry.get('scene_id') == scene_id]
        unit_id = str(scene_entries[0].get('unit_id') or '') if scene_entries else ''
        coverage_id = f'SCENE:{scene_id}'
        flat_items.append({
            'coverage_id': coverage_id, 'category': 'scene', 'content': scene_id,
            'unit_id': unit_id or None, 'scene_id': scene_id,
            'status': _production_status(covered=covered, unit_id=unit_id, completed=completed, confirmed=confirmed, coverage_id=coverage_id, confirm_unit=confirm_unit),
            'evidence': [str(entry.get('shot_id')) for entry in scene_entries if entry.get('shot_id')],
        })
    atom_coverage_ids = {str(item.get('coverage_id') or '') for item in flat_items}
    for info in info_records:
        info_id = str(info.get('info_id') or '')
        if not info_id or info_id in atom_coverage_ids:
            continue
        marker = info.get('actual_reveal') or info.get('planned_reveal')
        unit_id = _marker_unit_id(marker)
        covered = bool(info.get('reveal_covered')) and not bool(info.get('early_reveal_evidence'))
        category = 'reveal' if info.get('actual_reveal') or str(info.get('status') or '').upper() in {'REVEALED', 'REINTERPRETED'} else 'information'
        flat_items.append({
            'coverage_id': info_id,
            'category': category,
            'content': f'{info_id}｜{info.get("status") or "INFORMATION"}',
            'unit_id': unit_id or None,
            'scene_id': None,
            'status': _production_status(
                covered=covered, unit_id=unit_id, completed=completed, confirmed=confirmed,
                coverage_id=info_id, confirm_unit=confirm_unit,
            ),
            'evidence': list(info.get('reveal_shot_ids') or []),
        })
    risks: list[dict] = []
    for info in info_records:
        info_id = str(info.get('info_id') or '')
        if info.get('early_reveal_evidence'):
            risks.append({'code': 'EARLY_REVEAL', 'coverage_id': info_id, 'detail': '；'.join(info['early_reveal_evidence'])})
        if not info.get('reveal_covered'):
            risks.append({'code': 'UNCOVERED_REVEAL', 'coverage_id': info_id, 'detail': '已计划/记录的Reveal尚未在正确位置核销'})
    result['items'] = flat_items
    result['risks'] = risks
    result['summary'] = {
        'total': len(flat_items),
        'confirmed': sum(1 for item in flat_items if item['status'] == 'CONFIRMED'),
        'blocking': sum(1 for item in flat_items if item['status'] == 'UNCOVERED') + len(risks),
    }
    return result


def write_story_coverage(project_root: str | Path, *, confirm_unit: str | None = None) -> Path:
    root = Path(project_root).resolve()
    data = build_story_coverage(root, confirm_unit=confirm_unit)
    target = root / 'state' / COVERAGE_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return target


def _unit_scoped_items(items: list[dict], unit_id: str | None) -> list[dict]:
    if not unit_id:
        return items
    return [item for item in items if str(item.get('unit_id') or '') == unit_id]


def validate_story_coverage(
    project_root: str | Path,
    *,
    unit_id: str | None = None,
    final_mode: bool = False,
    require_persisted_match: bool = False,
) -> list[str]:
    root = Path(project_root).resolve()
    if not story_coverage_enabled(root):
        return []
    authority_path = root / 'state' / 'story_authority.json'
    if not authority_path.is_file():
        return ['STORY_COVERAGE：pipeline已声明story_authority_ready，但缺少state/story_authority.json']

    data = build_story_coverage(root)
    errors: list[str] = []

    atom_items = _unit_scoped_items(data['story_atoms']['items'], unit_id)
    uncovered = [item['atom_id'] for item in atom_items if item.get('required') and item.get('status') != 'COVERED']
    if uncovered:
        errors.append(f'STORY_COVERAGE：未覆盖锁定剧情原子：{uncovered}')

    if unit_id:
        authority = _load(authority_path)
        unit_scene_ids = sorted({
            str(atom.get('scene_id')) for atom in authority.get('atoms', [])
            if isinstance(atom, dict) and atom.get('locked') is True and str(atom.get('unit_id') or '') == unit_id and atom.get('scene_id')
        }, key=_natural_key)
        timeline, _ = _timeline(root)
        covered = {entry['scene_id'] for entry in timeline if entry['unit_id'] == unit_id}
        missing_scenes = [scene for scene in unit_scene_ids if scene not in covered]
    else:
        missing_scenes = list(data['scenes']['missing_scene_ids'])
    if missing_scenes:
        errors.append(f'STORY_COVERAGE：缺失锁定场景：{missing_scenes}')

    dialogue_items = _unit_scoped_items(data['dialogues']['items'], unit_id)
    missing_dialogues = [item['atom_id'] for item in dialogue_items if item.get('status') != 'COVERED']
    if missing_dialogues:
        errors.append(f'STORY_COVERAGE：重要对白未进入SH与GU执行：{missing_dialogues}')

    info_items = data['information']['items']
    if unit_id:
        early = [item['info_id'] for item in info_items if any(str(ev).startswith(f'{unit_id}/') for ev in item.get('early_reveal_evidence', []))]
        uncovered_reveals = [
            item['info_id'] for item in info_items
            if item.get('actual_reveal') and re.search(rf'\b{re.escape(unit_id)}\b', str(item.get('actual_reveal')), re.I) and not item.get('reveal_covered')
        ]
    else:
        early = list(data['information']['early_reveal_info_ids'])
        uncovered_reveals = list(data['information']['uncovered_reveal_info_ids'])
    if early:
        errors.append(f'STORY_COVERAGE：信息提前Reveal：{early}')
    if uncovered_reveals:
        errors.append(f'STORY_COVERAGE：计划/实际Reveal未被正式分镜覆盖：{uncovered_reveals}')

    if final_mode:
        if data['story_atoms']['required_atom_count'] > 0 and data['story_atoms']['coverage_percentage'] < 100.0:
            errors.append('STORY_COVERAGE：最终剧情原子覆盖率不足100%')
        final_items = _unit_scoped_items(data.get('items', []), unit_id)
        unconfirmed = [item.get('coverage_id') for item in final_items if item.get('status') != 'CONFIRMED']
        if unconfirmed:
            errors.append(f'STORY_COVERAGE：最终交付前仍有条目未确认：{unconfirmed}')
        if require_persisted_match:
            persisted_path = root / 'state' / COVERAGE_NAME
            persisted = _load(persisted_path)
            if not persisted:
                errors.append(f'STORY_COVERAGE：缺少{COVERAGE_NAME}')
            elif persisted != data:
                errors.append(f'STORY_COVERAGE：{COVERAGE_NAME}与当前Story Authority/Storyboard不一致，必须刷新后再交付')
    return list(dict.fromkeys(errors))
