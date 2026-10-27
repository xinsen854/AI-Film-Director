from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))

from qc_routing import affected_ids, build_issue


def test_extracts_all_required_affected_id_families_in_message_order():
    message = (
        'SOME_NEW_ERROR：EP03/PU02/SC08/ST014/DB023/I007/'
        'SH018/GU009/A001/S003/P004/V002'
    )
    assert affected_ids(message) == [
        'EP03', 'PU02', 'SC08', 'ST014', 'DB023', 'I007',
        'SH018', 'GU009', 'A001', 'S003', 'P004', 'V002',
    ]


def test_asset_state_id_is_single_asset_token_while_story_atom_stays_distinct():
    message = 'ASSET_FILE_INVALID：A002-ST001 与剧情原子 ST014 相关'
    assert affected_ids(message) == ['A002-ST001', 'ST014']


def test_duplicate_ids_are_deduplicated_without_reordering():
    message = 'STORY_COVERAGE：SC08/DB023/SC08/I007/DB023/GU018'
    assert affected_ids(message) == ['SC08', 'DB023', 'I007', 'GU018']


def test_existing_unit_fallback_is_preserved_when_message_has_no_explicit_id():
    assert affected_ids('DELIVERY_GATE_ERROR：没有显式编号', 'PU09') == ['PU09']


def test_item8_changes_only_localization_not_owner_or_rerun_route():
    issue = build_issue('CURRENT_GU_ONLY_DIALOGUE：EP03/SC08/DB023/GU018')
    assert issue['owner_layer'] == 'SHOT_SEGMENT'
    assert issue['affected_ids'] == ['EP03', 'SC08', 'DB023', 'GU018']
    assert issue['rerun_path'][:2] == ['SHOT_SEGMENT', 'QUALITY']
