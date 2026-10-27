from pathlib import Path
import json, hashlib, sys
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'scripts'))
import hard_delivery_qc as hq
import master_orchestrator as mo
from project_scope import write_project_scope


def dump(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def setup_scope(root, scenes=2, target=100):
    dump(root/'state/project_brief.json',{'project_id':'FILM01','work_format':'film','target_total_runtime_seconds':target,'execution_mode':'FULL','confirmed_brief':True})
    lock=root/'screenplay/FILM01_LOCKED_SCREENPLAY.md'; lock.parent.mkdir(parents=True,exist_ok=True)
    lock.write_text('\n\n'.join(f'SCENE {i}\n正文{i}' for i in range(1,scenes+1))+'\n',encoding='utf-8')
    st=mo.init_state(root); st.update({'lock_status':'LOCKED','locked_screenplay_path':'screenplay/FILM01_LOCKED_SCREENPLAY.md','locked_screenplay_sha256':hashlib.sha256(lock.read_bytes()).hexdigest()}); mo._write(root,st)
    scope=write_project_scope(root)
    return scope

def ledger(root, completed, target=100, covered=0, status='IN_PROGRESS', gaps=None):
    rows=[]; start=0
    if completed:
        span=covered/len(completed) if completed else 0
        for u in completed:
            rows.append({'unit_id':u,'start_seconds':start,'end_seconds':start+span,'status':'COMPLETE'}); start+=span
    data={'scope_type':'film_timeline','status':status,'target_runtime_seconds':target,'completed_units':list(completed),'film_units':rows,'coverage':{'covered_seconds':covered,'gaps':[] if gaps is None else gaps},'next_resume':{'start_seconds':covered}}
    dump(root/'PRODUCTION_LEDGER.json',data); return data


def test_project_qc_empty_completed_units_must_fail(tmp_path):
    setup_scope(tmp_path,2,100); ledger(tmp_path,[],100,0)
    errors=hq.validate_hard_delivery(tmp_path,scope='project')
    assert any('HARD_PROJECT_NO_COMPLETED_UNITS' in e for e in errors)
    assert any('HARD_PROJECT_UNIT_COVERAGE_INCOMPLETE' in e for e in errors)


def test_project_qc_target_100_actual_10_must_fail(tmp_path):
    setup_scope(tmp_path,2,100); ledger(tmp_path,['PU001'],100,10)
    errors=hq.validate_hard_delivery(tmp_path,scope='project')
    assert any('HARD_PROJECT_RUNTIME_INCOMPLETE' in e for e in errors)
    assert any('HARD_PROJECT_UNIT_COVERAGE_INCOMPLETE' in e for e in errors)


def test_project_qc_completed_runtime_with_gap_must_fail(tmp_path, monkeypatch):
    setup_scope(tmp_path,1,100); ledger(tmp_path,['PU001'],100,100,'COMPLETED',[{'start_seconds':40,'end_seconds':50}])
    monkeypatch.setattr(hq,'validate_project_consistency',lambda root,unit: [])
    errors=hq.validate_hard_delivery(tmp_path,scope='project')
    assert any('HARD_PROJECT_RUNTIME_GAPS' in e for e in errors)


def test_unit_scope_does_not_require_whole_project_complete(tmp_path, monkeypatch):
    setup_scope(tmp_path,2,100); ledger(tmp_path,['PU001'],100,10)
    monkeypatch.setattr(hq,'validate_project_consistency',lambda root,unit: [])
    monkeypatch.setattr(hq,'_validate_sh_gu_prompt',lambda root,ledger,errors: None)
    assert hq.validate_hard_delivery(tmp_path,scope='unit',unit_id='PU001')==[]


def test_project_qc_rejects_completed_list_without_film_rows(tmp_path, monkeypatch):
    scope=setup_scope(tmp_path,1,100); data=ledger(tmp_path,['PU001'],100,100,'COMPLETED'); data['film_units']=[]; dump(tmp_path/'PRODUCTION_LEDGER.json',data)
    monkeypatch.setattr(hq,'validate_project_consistency',lambda root,unit: [])
    errors=hq.validate_hard_delivery(tmp_path,scope='project')
    assert any('HARD_PROJECT_LEDGER_UNIT_SHAPE_INVALID' in e for e in errors)


def test_master_project_final_qc_rejects_dummy_artifact_even_if_nonempty(tmp_path, monkeypatch):
    scope=setup_scope(tmp_path,1,100)
    st=mo.load_state(tmp_path); st.update({'project_scope_active':True,'scope_manifest_sha256':scope['scope_manifest_sha256'],'planned_units':['PU001'],'completed_units':['PU001'],'current_unit_id':None,'current_stage':'PROJECT_FINAL_HARD_QC','stage_status':'PENDING'}); mo._write(tmp_path,st)
    ledger(tmp_path,['PU001'],100,100,'COMPLETED')
    (tmp_path/'dummy.txt').write_text('PASS',encoding='utf-8')
    try: mo.pass_stage(tmp_path,'PROJECT_FINAL_HARD_QC',artifact='dummy.txt')
    except ValueError as exc: assert 'MASTER_PROJECT_QC_ARTIFACT_REQUIRED' in str(exc)
    else: raise AssertionError

def test_project_qc_recomputes_scene_coverage_from_actual_storyboards(tmp_path, monkeypatch):
    setup_scope(tmp_path,2,100); ledger(tmp_path,['PU001','PU002'],100,100,'COMPLETED')
    monkeypatch.setattr(hq,'validate_project_consistency',lambda root,unit: [])
    monkeypatch.setattr(hq,'_validate_sh_gu_prompt',lambda root,ledger,errors: None)
    dump(tmp_path/'storyboard/PU001_STORYBOARD.json',{'edit_shots':[{'edit_shot_id':'SH001','scene_id':'SC001','coverage':{'story_atom_ids':[]}}]})
    dump(tmp_path/'state/story_authority.json',{'atoms':[]})
    errors=hq.validate_hard_delivery(tmp_path,scope='project')
    assert any('HARD_PROJECT_SCENE_COVERAGE_INCOMPLETE' in e and 'SC002' in e for e in errors)


def test_project_qc_recomputes_story_atom_coverage_from_actual_shots(tmp_path, monkeypatch):
    setup_scope(tmp_path,1,100); ledger(tmp_path,['PU001'],100,100,'COMPLETED')
    monkeypatch.setattr(hq,'validate_project_consistency',lambda root,unit: [])
    monkeypatch.setattr(hq,'_validate_sh_gu_prompt',lambda root,ledger,errors: None)
    dump(tmp_path/'state/story_authority.json',{'atoms':[{'atom_id':'A001','scene_id':'SC001'}]})
    dump(tmp_path/'storyboard/PU001_STORYBOARD.json',{'edit_shots':[{'edit_shot_id':'SH001','scene_id':'SC001','coverage':{'story_atom_ids':[]}}]})
    errors=hq.validate_hard_delivery(tmp_path,scope='project')
    assert any('HARD_PROJECT_STORY_ATOM_COVERAGE_INCOMPLETE' in e and 'A001' in e for e in errors)


def test_master_final_qc_pass_text_cannot_override_failed_project_qc(tmp_path):
    scope=setup_scope(tmp_path,2,100)
    st=mo.load_state(tmp_path); st.update({'project_scope_active':True,'scope_manifest_sha256':scope['scope_manifest_sha256'],'planned_units':['PU001','PU002'],'completed_units':['PU001'],'current_unit_id':None,'current_stage':'PROJECT_FINAL_HARD_QC','stage_status':'PENDING'}); mo._write(tmp_path,st)
    ledger(tmp_path,['PU001'],100,10,'IN_PROGRESS')
    (tmp_path/'FINAL_QC.md').write_text('## Project Result\nPASS\n',encoding='utf-8')
    try: mo.pass_stage(tmp_path,'PROJECT_FINAL_HARD_QC',artifact='FINAL_QC.md')
    except ValueError as exc: assert 'MASTER_PROJECT_QC_FAILED' in str(exc)
    else: raise AssertionError


def test_build_exports_project_scope_invokes_project_hard_gate(tmp_path, monkeypatch):
    import build_exports as be
    setup_scope(tmp_path,1,100)
    (tmp_path/'FINAL_QC.md').write_text('## Project Result\nPASS\n',encoding='utf-8')
    ledger(tmp_path,['PU001'],100,100,'COMPLETED')
    for rel in ['screenplay/PU001_LOCKED_SCREENPLAY.md','director/PU001_INTEGRATED_DIRECTOR_SCREENPLAY.md','storyboard/PU001_STORYBOARD.md']:
        p=tmp_path/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('x',encoding='utf-8')
    dump(tmp_path/'storyboard/PU001_STORYBOARD.json',{'edit_shots':[{'edit_shot_id':'SH001','scene_id':'SC001'}]})
    seen=[]
    def fake(root,*,scope='legacy',unit_id=None): seen.append(scope); return ['intentional project block']
    monkeypatch.setattr(be,'validate_hard_delivery',fake)
    try: be._verify_delivery_gate(tmp_path)
    except be.RoutedQCError: pass
    else: raise AssertionError
    assert seen==['project']
