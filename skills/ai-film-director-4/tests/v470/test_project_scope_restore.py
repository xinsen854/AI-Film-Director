from pathlib import Path
import json
import hashlib
import pytest
import sys
ROOT=Path(__file__).resolve().parents[2]
SCRIPTS=ROOT/"scripts"
if str(SCRIPTS) not in sys.path: sys.path.insert(0,str(SCRIPTS))

from project_scope import build_project_scope, validate_project_scope, scope_manifest_sha256


def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def make_project(root: Path, scene_count=3, runtime=5400):
    lock = root/'screenplay'/'FILM01_LOCKED_SCREENPLAY.md'
    lock.parent.mkdir(parents=True)
    lines=[]
    for i in range(1, scene_count+1):
        lines += [f'SCENE {i}', f'场景正文 {i}', '']
    lock.write_text('\n'.join(lines), encoding='utf-8')
    h=hashlib.sha256(lock.read_bytes()).hexdigest()
    dump(root/'state'/'master_orchestrator.json', {
        'lock_status':'LOCKED','locked_screenplay_path':'screenplay/FILM01_LOCKED_SCREENPLAY.md','locked_screenplay_sha256':h
    })
    dump(root/'state'/'project_brief.json', {
        'project_id':'FILM01','work_format':'film','target_total_runtime_seconds':runtime,
        'confirmation_status':'confirmed','confirmed_brief':True
    })
    return lock


def test_build_scope_locks_full_scene_set_and_default_one_scene_per_pu(tmp_path):
    make_project(tmp_path, 3)
    scope=build_project_scope(tmp_path)
    assert scope['scene_ids']==['SC001','SC002','SC003']
    assert [u['unit_id'] for u in scope['production_units']]==['PU001','PU002','PU003']
    assert [u['scene_ids'] for u in scope['production_units']]==[['SC001'],['SC002'],['SC003']]
    assert not validate_project_scope(tmp_path, scope)


def test_scope_cannot_shrink_scene_set_even_if_hash_recomputed(tmp_path):
    make_project(tmp_path, 3)
    scope=build_project_scope(tmp_path)
    scope['scene_ids']=['SC001']
    scope['scene_count']=1
    scope['production_units']=[{'unit_id':'PU001','scene_ids':['SC001']}]
    scope['scope_manifest_sha256']=scope_manifest_sha256(scope)
    errors=validate_project_scope(tmp_path, scope)
    assert any('SCENE_SET_MISMATCH' in x for x in errors)


def test_scope_rejects_non_contiguous_or_duplicate_unit_assignment(tmp_path):
    make_project(tmp_path, 3)
    scope=build_project_scope(tmp_path, grouping=[['SC001','SC003'],['SC002']])
    errors=validate_project_scope(tmp_path, scope)
    assert any('UNIT_SCENE_ORDER_INVALID' in x for x in errors)


def test_scope_rejects_hidden_story_authority_fields(tmp_path):
    make_project(tmp_path, 2)
    scope=build_project_scope(tmp_path)
    scope['story_atoms']=[{'atom_id':'A1'}]
    scope['scope_manifest_sha256']=scope_manifest_sha256(scope)
    assert any('UNSUPPORTED_FIELD' in x for x in validate_project_scope(tmp_path, scope))
