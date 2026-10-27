from pathlib import Path
import json, hashlib, sys
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'scripts'))
from production_unit_packet import build_unit_packet, validate_unit_packet


def dump(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def setup(root):
    scope={'scope_contract':'AFD_PROJECT_SCOPE_V1','scope_manifest_sha256':'a'*64,'production_units':[{'unit_id':'PU001','scene_ids':['SC001','SC002']}], 'scene_ids':['SC001','SC002']}
    dump(root/'state/PROJECT_SCOPE.json',scope)
    story={'atoms':[{'atom_id':'A1','scene_id':'SC001'},{'atom_id':'A2','scene_id':'SC002'}]}; dump(root/'state/story_authority.json',story)
    info={'items':[{'info_id':'I1'},{'info_id':'I2'}]}; dump(root/'state/information_ledger.json',info)
    return scope

def test_packet_derives_scene_and_atom_scope_without_inventing_story(tmp_path):
    setup(tmp_path)
    p=build_unit_packet(tmp_path,'PU001')
    assert p['scene_scope']==['SC001','SC002']
    assert p['expected_story_atom_ids']==['A1','A2']
    assert 'story_atoms' not in p and 'character_motives' not in p
    assert not validate_unit_packet(tmp_path,p)

def test_packet_rejects_unknown_unit_and_stale_story_hash(tmp_path):
    setup(tmp_path)
    try: build_unit_packet(tmp_path,'PU999')
    except ValueError as exc: assert 'UNIT_NOT_PLANNED' in str(exc)
    else: raise AssertionError
    p=build_unit_packet(tmp_path,'PU001')
    dump(tmp_path/'state/story_authority.json',{'atoms':[{'atom_id':'A1','scene_id':'SC001'}]})
    assert any('HASH_MISMATCH' in e for e in validate_unit_packet(tmp_path,p))

def test_packet_rejects_hidden_authority_fields_or_fake_information(tmp_path):
    setup(tmp_path); p=build_unit_packet(tmp_path,'PU001')
    p['story_atoms']=[]
    assert any('UNSUPPORTED_FIELD' in e for e in validate_unit_packet(tmp_path,p))
