from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'scripts'))
from validate_unit_consistency import _validate_storyboard_against_packet


def test_packet_six_scenes_storyboard_one_scene_fails():
    packet={'scene_scope':['SC001','SC002','SC003','SC004','SC005','SC006'],'expected_story_atom_ids':['A1','A2']}
    story={'atoms':[{'atom_id':'A1','scene_id':'SC001'},{'atom_id':'A2','scene_id':'SC002'}]}
    sb={'edit_shots':[{'scene_id':'SC001','coverage':{'story_atom_ids':['A1']}}]}
    e=[]; _validate_storyboard_against_packet(sb,packet,story,e)
    assert any('UNIT_STORYBOARD_SCENE_SCOPE_INCOMPLETE' in x for x in e)
    assert any('UNIT_STORYBOARD_STORY_ATOM_SCOPE_INCOMPLETE' in x for x in e)


def test_atom_cannot_be_attached_to_wrong_scene_even_when_global_set_complete():
    packet={'scene_scope':['SC001','SC002'],'expected_story_atom_ids':['A1','A2']}
    story={'atoms':[{'atom_id':'A1','scene_id':'SC001'},{'atom_id':'A2','scene_id':'SC002'}]}
    sb={'edit_shots':[{'scene_id':'SC001','coverage':{'story_atom_ids':['A2']}},{'scene_id':'SC002','coverage':{'story_atom_ids':['A1']}}]}
    e=[]; _validate_storyboard_against_packet(sb,packet,story,e)
    assert any('UNIT_STORYBOARD_STORY_ATOM_SCENE_MISMATCH' in x for x in e)


def test_complete_scope_accepts_any_shot_order():
    packet={'scene_scope':['SC001','SC002'],'expected_story_atom_ids':['A1','A2']}
    story={'atoms':[{'atom_id':'A1','scene_id':'SC001'},{'atom_id':'A2','scene_id':'SC002'}]}
    sb={'edit_shots':[{'scene_id':'SC002','coverage':{'story_atom_ids':['A2']}},{'scene_id':'SC001','coverage':{'story_atom_ids':['A1']}}]}
    e=[]; _validate_storyboard_against_packet(sb,packet,story,e)
    assert e==[]
