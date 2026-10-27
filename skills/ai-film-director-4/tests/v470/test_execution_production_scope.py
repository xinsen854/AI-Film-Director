from pathlib import Path
import json, sys
import pytest
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'scripts'))
import master_orchestrator as mo
import build_exports as be
import run_pipeline as rp


def dump(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def test_project_brief_separates_execution_mode_from_production_scope():
    schema=json.loads((ROOT/'schemas/project_brief.schema.json').read_text(encoding='utf-8'))
    assert schema['properties']['execution_mode']['enum']==['FULL','QUICK']
    assert schema['properties']['production_scope']['enum']==['PROJECT','UNIT','PILOT']
    assert 'production_scope' in schema['required']


def test_master_requires_project_scope_plan_only_for_project_scoped_films(tmp_path):
    for production_scope,expected in [('PROJECT',True),('UNIT',False),('PILOT',False)]:
        dump(tmp_path/'state/project_brief.json',{'work_format':'film','execution_mode':'FULL','production_scope':production_scope})
        assert mo._film_project_scope_required(tmp_path) is expected


def test_legacy_missing_production_scope_preserves_existing_film_behavior(tmp_path):
    dump(tmp_path/'state/project_brief.json',{'work_format':'film','execution_mode':'FULL'})
    assert mo._film_project_scope_required(tmp_path) is True


def test_formal_export_requires_full_project_not_full_unit(tmp_path):
    dump(tmp_path/'state/project_brief.json',{'execution_mode':'FULL','production_scope':'UNIT'})
    with pytest.raises(ValueError,match='PRODUCTION_SCOPE_FORMAL_EXPORT_FORBIDDEN'):
        be._verify_delivery_gate(tmp_path)


def test_quick_project_still_cannot_claim_formal_export(tmp_path):
    dump(tmp_path/'state/project_brief.json',{'execution_mode':'QUICK','production_scope':'PROJECT'})
    with pytest.raises(ValueError,match='QUICK_MODE_FORMAL_EXPORT_FORBIDDEN'):
        be._verify_delivery_gate(tmp_path)


def test_run_pipeline_full_unit_does_not_call_build_exports(tmp_path,monkeypatch):
    dump(tmp_path/'state/project_brief.json',{'execution_mode':'FULL','production_scope':'UNIT'})
    dump(tmp_path/'state/forge_locked_audit.json',{})
    dump(tmp_path/'assets/ASSET_LIBRARY.json',{})
    sb=tmp_path/'storyboard/PU001_STORYBOARD.json'; dump(sb,{})
    seen=[]
    monkeypatch.setattr(rp,'_run',lambda script,*args,cwd: seen.append((script,args)))
    result=rp.run_pipeline(tmp_path)
    assert result=='FULL'
    assert not any(script=='build_exports.py' for script,args in seen)
    assert any(script=='hard_delivery_qc.py' for script,args in seen)


def test_invalid_production_scope_cannot_bypass_master_project_scope(tmp_path):
    dump(tmp_path/'state/project_brief.json',{'work_format':'film','execution_mode':'FULL','production_scope':'NOT_A_SCOPE'})
    with pytest.raises(ValueError,match='unsupported production_scope'):
        mo._film_project_scope_required(tmp_path)
