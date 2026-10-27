from pathlib import Path
import json, hashlib, sys
ROOT=Path(__file__).resolve().parents[2]; SCRIPTS=ROOT/'scripts'; sys.path.insert(0,str(SCRIPTS))
from compile_forge_handoff import _validate_project_scope_against_forge


def test_forge_scope_rejects_story_or_handoff_shrink(tmp_path):
    scope={'scene_ids':['SC001','SC002'],'scope_manifest_sha256':'a'*64}
    story={'atoms':[{'atom_id':'A1','scene_id':'SC001'}]}
    handoffs=[{'scene_id':'SC001'}]
    errors=_validate_project_scope_against_forge(scope,story,handoffs)
    assert any('FORGE_PROJECT_SCOPE_INCOMPLETE' in e for e in errors)


def test_forge_scope_accepts_multiple_atoms_per_scene_and_complete_handoffs(tmp_path):
    scope={'scene_ids':['SC001','SC002'],'scope_manifest_sha256':'a'*64}
    story={'atoms':[{'atom_id':'A1','scene_id':'SC001'},{'atom_id':'A2','scene_id':'SC001'},{'atom_id':'A3','scene_id':'SC002'}]}
    handoffs=[{'scene_id':'SC002'},{'scene_id':'SC001'}]
    assert not _validate_project_scope_against_forge(scope,story,handoffs)
