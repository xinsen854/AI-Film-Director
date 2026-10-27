from __future__ import annotations
from pathlib import Path
import json, hashlib, sys, copy
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'scripts'))
from render_asset_library import validate_asset_library_payload
from project_asset_baseline import (
    requirements_manifest_sha256, validate_project_asset_requirements,
    validate_project_asset_library_coverage, lock_project_asset_baseline,
    validate_asset_baseline_lock,
)


def dump(p:Path,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()

def make_scope(root:Path):
    lock=root/'screenplay/FILM01_LOCKED_SCREENPLAY.md'; lock.parent.mkdir(parents=True,exist_ok=True); lock.write_text('SCENE 1\n成年鸿森在医院。\n\nSCENE 2\n童年鸿森在老家院落。\n',encoding='utf-8')
    scope={
      'scope_contract':'AFD_PROJECT_SCOPE_V1','project_id':'FILM01','work_format':'film','locked_screenplay_path':'screenplay/FILM01_LOCKED_SCREENPLAY.md',
      'locked_screenplay_sha256':sha(lock),'project_brief_sha256':'b'*64,'target_runtime_seconds':5400.0,'scene_count':2,
      'scene_ids':['SC001','SC002'],'production_units':[{'unit_id':'PU001','scene_ids':['SC001']},{'unit_id':'PU002','scene_ids':['SC002']}],
      'scope_manifest_sha256':'a'*64,
    }
    dump(root/'state/PROJECT_SCOPE.json',scope)
    return scope

def make_requirements(root:Path):
    scope=make_scope(root)
    req={
      'requirements_contract':'AFD_PROJECT_ASSET_REQUIREMENTS_V1',
      'scope_manifest_sha256':scope['scope_manifest_sha256'],
      'locked_screenplay_sha256':scope['locked_screenplay_sha256'],
      'requirements':[
        {'requirement_id':'AR001','kind':'character_base','canonical_name':'鸿森','scene_ids':['SC001','SC002'],'source_evidence':['SC001: 成年鸿森','SC002: 童年鸿森']},
        {'requirement_id':'AR002','kind':'character_state','canonical_name':'鸿森','state_label':'2017成年','parent_requirement_id':'AR001','scene_ids':['SC001'],'source_evidence':['SC001: 成年鸿森']},
        {'requirement_id':'AR003','kind':'character_state','canonical_name':'鸿森','state_label':'1996童年','parent_requirement_id':'AR001','scene_ids':['SC002'],'source_evidence':['SC002: 童年鸿森']},
        {'requirement_id':'AR004','kind':'location','canonical_name':'医院','scene_ids':['SC001'],'source_evidence':['SC001: 医院']},
        {'requirement_id':'AR005','kind':'location','canonical_name':'老家院落','scene_ids':['SC002'],'source_evidence':['SC002: 老家院落']},
      ],
      'scene_inventory':[
        {'scene_id':'SC001','requirement_ids':['AR001','AR002','AR004']},
        {'scene_id':'SC002','requirement_ids':['AR001','AR003','AR005']},
      ],
    }
    req['requirements_manifest_sha256']=requirements_manifest_sha256(req)
    dump(root/'state/project_asset_requirements.json',req)
    return req

def base_library():
    return {'ASSET_LIBRARY':{
      'contract_version':'4.3',
      'source':{'production_range':'PROJECT'},
      'project_asset_policy':{'world_and_visual_style':'写实','character_face_policy':'身份稳定','image_prompt_policy':'最少必要资产','voice_asset_policy':'V系列仅文字'},
      'quick_index':[],
      'character_assets':[{
        'asset_id':'A001','name':'鸿森','image_prompt':'鸿森人物母板','image_status':'PROMPT_ONLY','image_file':'','reference_media':[],
        'use_scope':['SC001','SC002'],'dependencies':[],'voice_asset_id':'V001'
      }],
      'persistent_states':[
        {'state_id':'A001-ST001','inherits_from':'A001','state_category':'age_state','visible_change':'2017成年状态','image_prompt':'继承A001，2017成年','image_status':'PROMPT_ONLY','image_file':'','reference_media':[],'use_scope':['SC001'],'dependencies':['A001']},
        {'state_id':'A001-ST002','inherits_from':'A001','state_category':'age_state','visible_change':'1996童年状态','image_prompt':'继承A001，1996童年','image_status':'PROMPT_ONLY','image_file':'','reference_media':[],'use_scope':['SC002'],'dependencies':['A001']},
      ],
      'location_assets':[
        {'asset_id':'S001','name':'医院','image_prompt':'医院','image_status':'PROMPT_ONLY','image_file':'','reference_media':[],'use_scope':['SC001'],'dependencies':[]},
        {'asset_id':'S002','name':'老家院落','image_prompt':'老家院落','image_status':'PROMPT_ONLY','image_file':'','reference_media':[],'use_scope':['SC002'],'dependencies':[]},
      ],
      'prop_assets':[],'g_assets':[],
      'voice_assets':[{
        'asset_id':'V001','name':'鸿森声线','asset_class':'TEXT_VOICE_ASSET','media_asset':False,'visual_cost_units':0,'seedance_reference_slot_cost':0,
        'character_asset_id':'A001','image_file':None,'audio_file':None,'video_file':None,'use_scope':['SC001','SC002'],'dependencies':['A001'],
        'voice_profile':{'perceived_age':'随状态','gender_presentation':'男性','accent_or_regional_quality':'普通话','register':'中低','timbre':'自然','texture':'自然','resonance':'胸腔','pace':'自然','rhythm':'自然','volume_tendency':'中','emotional_leakage':'克制','pressure_behavior':'变慢','prohibitions':['不播音腔']}
      }],
      'project_baseline':{
        'scope_manifest_sha256':'a'*64,
        'requirements_manifest_sha256':'',
        'requirement_bindings':{
          'AR001':'A001','AR002':'A001-ST001','AR003':'A001-ST002','AR004':'S001','AR005':'S002'
        },
        'existing_media_accounting':[]
      }
    }}

def bind_requirements(lib, req):
    lib=copy.deepcopy(lib)
    lib['ASSET_LIBRARY']['project_baseline']['requirements_manifest_sha256']=req['requirements_manifest_sha256']
    return lib


def test_root_contract_version_missing_or_wrong_must_fail():
    lib=base_library(); del lib['ASSET_LIBRARY']['contract_version']
    assert any('contract_version' in e for e in validate_asset_library_payload(lib))
    lib=base_library(); lib['ASSET_LIBRARY']['contract_version']='4.2'
    assert any('contract_version' in e for e in validate_asset_library_payload(lib))


def test_requirements_manifest_covers_every_project_scene_and_cannot_become_second_asset_library(tmp_path):
    req=make_requirements(tmp_path)
    assert validate_project_asset_requirements(tmp_path,req)==[]
    bad=copy.deepcopy(req); bad['scene_inventory']=bad['scene_inventory'][:1]; bad['requirements_manifest_sha256']=requirements_manifest_sha256(bad)
    assert any('SCENE_INVENTORY' in e for e in validate_project_asset_requirements(tmp_path,bad))
    bad=copy.deepcopy(req); bad['requirements'][0]['image_prompt']='不该在requirements里'; bad['requirements_manifest_sha256']=requirements_manifest_sha256(bad)
    assert any('UNSUPPORTED_FIELD' in e for e in validate_project_asset_requirements(tmp_path,bad))


def test_adult_state_missing_from_library_fails_even_when_child_and_base_exist(tmp_path):
    req=make_requirements(tmp_path); lib=bind_requirements(base_library(),req)
    lib['ASSET_LIBRARY']['persistent_states']=[lib['ASSET_LIBRARY']['persistent_states'][1]]
    lib['ASSET_LIBRARY']['project_baseline']['requirement_bindings']['AR002']='A001'
    errors=validate_project_asset_library_coverage(tmp_path,lib,req)
    assert any('ASSET_REQUIREMENT_KIND_MISMATCH' in e or 'ASSET_REQUIREMENT_UNSATISFIED' in e for e in errors)


def test_project_baseline_covers_all_requirements_and_scene_use_scope(tmp_path):
    req=make_requirements(tmp_path); lib=bind_requirements(base_library(),req)
    assert validate_project_asset_library_coverage(tmp_path,lib,req)==[]
    lib['ASSET_LIBRARY']['location_assets'][0]['use_scope']=[]
    assert any('ASSET_REQUIREMENT_SCOPE_MISMATCH' in e for e in validate_project_asset_library_coverage(tmp_path,lib,req))


def test_existing_media_must_be_explicitly_accounted_but_non_asset_media_is_allowed(tmp_path):
    req=make_requirements(tmp_path)
    dump(tmp_path/'state/project_brief.json',{'existing_media':[{'path':'media/hongsen.png'},{'path':'media/source.mov'}]})
    lib=bind_requirements(base_library(),req)
    errors=validate_project_asset_library_coverage(tmp_path,lib,req)
    assert any('EXISTING_MEDIA_UNACCOUNTED' in e for e in errors)
    lib['ASSET_LIBRARY']['project_baseline']['existing_media_accounting']=[
      {'brief_index':0,'disposition':'ASSET_BOUND','asset_id':'A001','canonical_file':'assets/generated/A001_existing.png'},
      {'brief_index':1,'disposition':'NON_ASSET_MEDIA','reason':'source footage, not a canonical asset'}
    ]
    lib['ASSET_LIBRARY']['character_assets'][0]['reference_media']=['assets/generated/A001_existing.png']
    media=tmp_path/'assets/generated/A001_existing.png'; media.parent.mkdir(parents=True,exist_ok=True); media.write_bytes(b'real-existing-media')
    assert validate_project_asset_library_coverage(tmp_path,lib,req)==[]


def test_baseline_lock_prevents_unit_slice_deletion_but_allows_additive_assets_and_status_updates(tmp_path):
    req=make_requirements(tmp_path); lib=bind_requirements(base_library(),req)
    dump(tmp_path/'assets/ASSET_LIBRARY.json',lib)
    receipt=lock_project_asset_baseline(tmp_path)
    assert validate_asset_baseline_lock(tmp_path)==[]
    current=json.loads((tmp_path/'assets/ASSET_LIBRARY.json').read_text(encoding='utf-8'))
    current['ASSET_LIBRARY']['persistent_states']=current['ASSET_LIBRARY']['persistent_states'][1:]
    dump(tmp_path/'assets/ASSET_LIBRARY.json',current)
    assert any('BASELINE_ASSET_REMOVED' in e for e in validate_asset_baseline_lock(tmp_path))
    dump(tmp_path/'assets/ASSET_LIBRARY.json',lib)
    current=copy.deepcopy(lib)
    current['ASSET_LIBRARY']['character_assets'][0]['image_status']='FAILED'
    current['ASSET_LIBRARY']['prop_assets'].append({'asset_id':'P099','name':'新增单元道具','image_prompt':'道具','image_status':'PROMPT_ONLY','image_file':'','reference_media':[],'use_scope':['SC002'],'dependencies':[]})
    dump(tmp_path/'assets/ASSET_LIBRARY.json',current)
    assert validate_asset_baseline_lock(tmp_path)==[]

def test_requirements_scene_review_is_bound_to_exact_locked_scene_bytes(tmp_path):
    req=make_requirements(tmp_path)
    # compiler-level scene review receipt: each scene must carry its exact scene hash and COMPLETE marker
    assert validate_project_asset_requirements(tmp_path,req)==[]
    lock=tmp_path/'screenplay/FILM01_LOCKED_SCREENPLAY.md'
    lock.write_text(lock.read_text(encoding='utf-8').replace('成年鸿森在医院。','成年鸿森在医院，手里拿着检查单。'),encoding='utf-8')
    assert any('SCREENPLAY_HASH' in e or 'SCENE_REVIEW' in e for e in validate_project_asset_requirements(tmp_path,req))


def test_relocking_smaller_requirements_cannot_redefine_baseline_when_master_is_bound(tmp_path):
    req=make_requirements(tmp_path); lib=bind_requirements(base_library(),req)
    dump(tmp_path/'assets/ASSET_LIBRARY.json',lib)
    dump(tmp_path/'state/master_orchestrator.json',{'orchestrator_contract':'AFD_MASTER_ORCHESTRATOR_V1'})
    first=lock_project_asset_baseline(tmp_path)
    master=json.loads((tmp_path/'state/master_orchestrator.json').read_text(encoding='utf-8'))
    assert master['project_asset_requirements_sha256']==req['requirements_manifest_sha256']
    # Attacker drops adult requirement and remaps library, while retaining scene inventory rows.
    req2=copy.deepcopy(req)
    req2['requirements']=[r for r in req2['requirements'] if r['requirement_id']!='AR002']
    for row in req2['scene_inventory']:
        row['requirement_ids']=[x for x in row['requirement_ids'] if x!='AR002']
    req2['requirements_manifest_sha256']=requirements_manifest_sha256(req2)
    dump(tmp_path/'state/project_asset_requirements.json',req2)
    lib2=copy.deepcopy(lib); lib2['ASSET_LIBRARY']['persistent_states']=lib2['ASSET_LIBRARY']['persistent_states'][1:]
    del lib2['ASSET_LIBRARY']['project_baseline']['requirement_bindings']['AR002']
    lib2['ASSET_LIBRARY']['project_baseline']['requirements_manifest_sha256']=req2['requirements_manifest_sha256']
    dump(tmp_path/'assets/ASSET_LIBRARY.json',lib2)
    try:
        lock_project_asset_baseline(tmp_path)
    except ValueError as exc:
        assert 'MASTER_ASSET_REQUIREMENTS_BINDING_STALE' in str(exc) or 'BASELINE' in str(exc)
    else:
        raise AssertionError('a bound project cannot redefine its asset requirements by relocking')


def test_non_asset_existing_media_requires_explicit_reason(tmp_path):
    req=make_requirements(tmp_path); dump(tmp_path/'state/project_brief.json',{'existing_media':[{'path':'media/source.mov'}]})
    lib=bind_requirements(base_library(),req)
    lib['ASSET_LIBRARY']['project_baseline']['existing_media_accounting']=[{'brief_index':0,'disposition':'NON_ASSET_MEDIA'}]
    assert any('NON_ASSET_REASON' in e for e in validate_project_asset_library_coverage(tmp_path,lib,req))

def test_failed_relock_does_not_overwrite_original_baseline_receipt(tmp_path):
    req=make_requirements(tmp_path); lib=bind_requirements(base_library(),req)
    dump(tmp_path/'assets/ASSET_LIBRARY.json',lib)
    dump(tmp_path/'state/master_orchestrator.json',{'orchestrator_contract':'AFD_MASTER_ORCHESTRATOR_V1'})
    lock_project_asset_baseline(tmp_path)
    receipt_path=tmp_path/'state/project_asset_baseline.json'
    original=receipt_path.read_text(encoding='utf-8')
    # keep requirements hash stable but remap one requirement to a new additive asset
    tampered=copy.deepcopy(lib)
    tampered['ASSET_LIBRARY']['location_assets'].append({'asset_id':'S099','name':'替换医院','image_prompt':'替换医院','image_status':'PROMPT_ONLY','image_file':'','reference_media':[],'use_scope':['SC001'],'dependencies':[]})
    tampered['ASSET_LIBRARY']['project_baseline']['requirement_bindings']['AR004']='S099'
    dump(tmp_path/'assets/ASSET_LIBRARY.json',tampered)
    try:
        lock_project_asset_baseline(tmp_path)
    except ValueError:
        pass
    else:
        raise AssertionError('relocking a changed baseline must fail')
    assert receipt_path.read_text(encoding='utf-8')==original
