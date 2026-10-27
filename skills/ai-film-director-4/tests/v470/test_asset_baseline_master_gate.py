from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'scripts'))
import master_orchestrator as mo


def dump(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def test_project_flow_after_forge_emotion_must_stop_at_asset_baseline(tmp_path):
    st=mo.init_state(tmp_path)
    st.update({'project_scope_active':True,'planned_units':['PU001'],'completed_units':[],'current_unit_id':'PU001','scope_manifest_sha256':'a'*64,
               'current_stage':'FORGE_EMOTION_RENDER','stage_status':'PENDING','next_stage':'SCENE_INTELLIGENCE','lock_status':'LOCKED'})
    mo._write(tmp_path,st)
    p=tmp_path/'AUDIENCE_EMOTION_MAP.html'; p.write_text('<html>x</html>',encoding='utf-8')
    st=mo.pass_stage(tmp_path,'FORGE_EMOTION_RENDER',artifact='AUDIENCE_EMOTION_MAP.html')
    assert st['current_stage']=='PROJECT_ASSET_BASELINE'


def test_project_asset_baseline_stage_rejects_dummy_receipt(tmp_path, monkeypatch):
    st=mo.init_state(tmp_path); st.update({'project_scope_active':True,'planned_units':['PU001'],'current_unit_id':'PU001','current_stage':'PROJECT_ASSET_BASELINE'}); mo._write(tmp_path,st)
    p=tmp_path/'dummy.json'; p.write_text('{}',encoding='utf-8')
    try: mo.pass_stage(tmp_path,'PROJECT_ASSET_BASELINE',artifact='dummy.json')
    except ValueError as exc: assert 'MASTER_PROJECT_ASSET_BASELINE_ARTIFACT_REQUIRED' in str(exc)
    else: raise AssertionError


def test_valid_project_asset_baseline_gate_enters_first_pu(tmp_path, monkeypatch):
    st=mo.init_state(tmp_path); st.update({'project_scope_active':True,'planned_units':['PU001','PU002'],'completed_units':[],'current_unit_id':'PU001','current_stage':'PROJECT_ASSET_BASELINE'}); mo._write(tmp_path,st)
    dump(tmp_path/'state/project_asset_baseline.json',{'baseline_contract':'AFD_PROJECT_ASSET_BASELINE_LOCK_V1','requirements_manifest_sha256':'a'*64,'baseline_lock_sha256':'b'*64})
    monkeypatch.setattr(mo,'_project_asset_baseline_errors',lambda root: [])
    st=mo.pass_stage(tmp_path,'PROJECT_ASSET_BASELINE',artifact='state/project_asset_baseline.json')
    assert st['current_stage']=='SCENE_INTELLIGENCE'
    assert st['current_unit_id']=='PU001'
    assert st['project_stage']=='UNIT_PRODUCTION'


def test_project_hard_qc_rechecks_asset_baseline_lock(tmp_path, monkeypatch):
    import hard_delivery_qc as hq
    dump(tmp_path/'state/project_brief.json', {'project_id':'FILM01','work_format':'film','target_total_runtime_seconds':100,'execution_mode':'FULL','confirmed_brief':True})
    dump(tmp_path/'PRODUCTION_LEDGER.json', {'scope_type':'film_timeline','status':'COMPLETED','target_runtime_seconds':100,'completed_units':['PU001'],'film_units':[{'unit_id':'PU001','start_seconds':0,'end_seconds':100,'status':'COMPLETE'}],'coverage':{'covered_seconds':100,'gaps':[]},'next_resume':{'start_seconds':100}})
    monkeypatch.setattr(hq, '_project_scope_qc', lambda root, brief, ledger, errors: None)
    monkeypatch.setattr(hq, '_validate_required_asset_status', lambda root, brief, errors: None)
    monkeypatch.setattr(hq, '_validate_sh_gu_prompt', lambda root, ledger, errors: None)
    monkeypatch.setattr(hq, '_validate_clear_axis_breaks', lambda root, ledger, errors: None)
    monkeypatch.setattr(hq, 'validate_asset_baseline_lock', lambda root: ['BASELINE_ASSET_REMOVED:[A001]'], raising=False)
    errors = hq.validate_hard_delivery(tmp_path, scope='project')
    assert any('HARD_PROJECT_ASSET_BASELINE_INVALID' in e and 'BASELINE_ASSET_REMOVED' in e for e in errors)
