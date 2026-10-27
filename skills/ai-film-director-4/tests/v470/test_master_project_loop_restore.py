from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'scripts'))
import master_orchestrator as mo


def dump(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def artifact(root,name='x.txt'): p=root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('x',encoding='utf-8'); return p

def project_state(root, planned=('PU001','PU002')):
    import hashlib
    from project_scope import write_project_scope
    dump(root/'state/project_brief.json',{'project_id':'FILM01','work_format':'film','target_total_runtime_seconds':100,'confirmation_status':'confirmed','confirmed_brief':True})
    lock=root/'screenplay/FILM01_LOCKED_SCREENPLAY.md'; lock.parent.mkdir(parents=True,exist_ok=True)
    lock.write_text('\n\n'.join(f'SCENE {i}\n正文{i}' for i in range(1,len(planned)+1))+'\n',encoding='utf-8')
    state=mo.init_state(root)
    state.update({'lock_status':'LOCKED','locked_screenplay_path':'screenplay/FILM01_LOCKED_SCREENPLAY.md','locked_screenplay_sha256':hashlib.sha256(lock.read_bytes()).hexdigest()})
    mo._write(root,state)
    scope=write_project_scope(root)
    state=mo.load_state(root)
    state.update({'project_scope_active':True,'planned_units':list(planned),'completed_units':[],'current_unit_id':planned[0],
                  'scope_manifest_sha256':scope['scope_manifest_sha256'],'current_stage':'PRODUCTION_LEDGER','stage_status':'PENDING','next_stage':None,'lock_status':'LOCKED'})
    mo._write(root,state)
    return state

def ledger(root, completed, rows=None):
    if rows is None:
        rows=[]; start=0
        for i,u in enumerate(completed): rows.append({'unit_id':u,'start_seconds':start,'end_seconds':start+10,'status':'COMPLETE'}); start+=10
    data={'scope_type':'film_timeline','status':'IN_PROGRESS','target_runtime_seconds':100,'completed_units':list(completed),'film_units':rows,
          'coverage':{'covered_seconds':rows[-1]['end_seconds'] if rows else 0,'gaps':[]},'next_resume':{'start_seconds':rows[-1]['end_seconds'] if rows else 0}}
    dump(root/'PRODUCTION_LEDGER.json',data); return data

def test_completed_current_pu_advances_to_next_not_exports(tmp_path, monkeypatch):
    project_state(tmp_path); ledger(tmp_path,['PU001'])
    monkeypatch.setattr(mo,'_unit_semantic_errors',lambda root,uid: [])
    st=mo.pass_stage(tmp_path,'PRODUCTION_LEDGER',artifact='PRODUCTION_LEDGER.json')
    assert st['current_unit_id']=='PU002' and st['current_stage']=='SCENE_INTELLIGENCE'
    assert st['completed_units']==['PU001']

def test_fake_completed_units_without_formal_film_rows_cannot_advance(tmp_path, monkeypatch):
    project_state(tmp_path); ledger(tmp_path,['PU001'],rows=[])
    monkeypatch.setattr(mo,'_unit_semantic_errors',lambda root,uid: [])
    try: mo.pass_stage(tmp_path,'PRODUCTION_LEDGER',artifact='PRODUCTION_LEDGER.json')
    except ValueError as exc: assert 'MASTER_LEDGER' in str(exc)
    else: raise AssertionError

def test_semantically_invalid_unit_cannot_be_advanced_by_manual_ledger(tmp_path, monkeypatch):
    project_state(tmp_path); ledger(tmp_path,['PU001'])
    monkeypatch.setattr(mo,'_unit_semantic_errors',lambda root,uid: ['missing storyboard'])
    try: mo.pass_stage(tmp_path,'PRODUCTION_LEDGER',artifact='PRODUCTION_LEDGER.json')
    except ValueError as exc: assert 'MASTER_CURRENT_UNIT_SEMANTIC_QC_FAILED' in str(exc)
    else: raise AssertionError

def test_all_planned_units_route_to_project_final_qc(tmp_path, monkeypatch):
    project_state(tmp_path,('PU001',)); ledger(tmp_path,['PU001'])
    monkeypatch.setattr(mo,'_unit_semantic_errors',lambda root,uid: [])
    st=mo.pass_stage(tmp_path,'PRODUCTION_LEDGER',artifact='PRODUCTION_LEDGER.json')
    assert st['current_stage']=='PROJECT_FINAL_HARD_QC'


def test_rerun_of_completed_unit_restores_current_unit_pointer(tmp_path):
    project_state(tmp_path, ('PU001',))
    st = mo.load_state(tmp_path)
    st.update({
        'completed_units': ['PU001'],
        'current_unit_id': None,
        'current_stage': 'EXPORTS',
        'stage_status': 'PENDING',
    })
    mo._write(tmp_path, st)

    st = mo.fail_stage(
        tmp_path,
        'EXPORTS',
        owner_stage='FORGE_AUDIT',
        affected_ids=['PU001'],
        reason='rebuild completed unit',
    )

    assert st['current_stage'] == 'FORGE_AUDIT'
    assert st['current_unit_id'] == 'PU001'

def _film_brief(root):
    dump(root/'state/project_brief.json',{
        'project_id':'FILM01','work_format':'film','target_total_runtime_seconds':100,
        'confirmation_status':'confirmed','confirmed_brief':True,
    })

def test_film_lock_must_route_through_project_scope_plan_before_forge_audit(tmp_path):
    _film_brief(tmp_path)
    candidate=tmp_path/'screenplay/FILM01_LOCKED_SCREENPLAY.md'; candidate.parent.mkdir(parents=True,exist_ok=True)
    candidate.write_text('SCENE 1\n正文1\n\nSCENE 2\n正文2\n',encoding='utf-8')
    mo.init_state(tmp_path,'AUTO_ACCEPT_AFTER_QC')
    st=mo.load_state(tmp_path)
    st.update({'current_stage':'FORGE_GATE_QC_DEAI','stage_status':'PENDING'})
    mo._write(tmp_path,st)
    st=mo.pass_stage(tmp_path,'FORGE_GATE_QC_DEAI',artifact='screenplay/FILM01_LOCKED_SCREENPLAY.md')
    assert st['current_stage']=='PROJECT_SCOPE_PLAN'


def test_project_scope_plan_binds_planned_units_before_forge_audit(tmp_path):
    from project_scope import write_project_scope
    _film_brief(tmp_path)
    candidate=tmp_path/'screenplay/FILM01_LOCKED_SCREENPLAY.md'; candidate.parent.mkdir(parents=True,exist_ok=True)
    candidate.write_text('SCENE 1\n正文1\n\nSCENE 2\n正文2\n',encoding='utf-8')
    mo.init_state(tmp_path,'AUTO_ACCEPT_AFTER_QC')
    st=mo.load_state(tmp_path); st.update({'current_stage':'FORGE_GATE_QC_DEAI','stage_status':'PENDING'}); mo._write(tmp_path,st)
    mo.pass_stage(tmp_path,'FORGE_GATE_QC_DEAI',artifact='screenplay/FILM01_LOCKED_SCREENPLAY.md')
    write_project_scope(tmp_path)
    st=mo.pass_stage(tmp_path,'PROJECT_SCOPE_PLAN',artifact='state/PROJECT_SCOPE.json')
    assert st['project_scope_active'] is True
    assert st['planned_units']==['PU001','PU002']
    assert st['current_unit_id']=='PU001'
    assert st['scope_manifest_sha256']
    assert st['current_stage']=='FORGE_AUDIT'

def test_review_lock_film_also_routes_through_project_scope_plan(tmp_path):
    _film_brief(tmp_path)
    candidate=tmp_path/'screenplay/FILM01_LOCKED_SCREENPLAY.md'; candidate.parent.mkdir(parents=True,exist_ok=True)
    candidate.write_text('SCENE 1\n正文1\n',encoding='utf-8')
    mo.init_state(tmp_path,'REVIEW_BEFORE_LOCK')
    st=mo.load_state(tmp_path); st.update({'current_stage':'FORGE_GATE_QC_DEAI','stage_status':'PENDING'}); mo._write(tmp_path,st)
    mo.pass_stage(tmp_path,'FORGE_GATE_QC_DEAI',artifact='screenplay/FILM01_LOCKED_SCREENPLAY.md')
    st=mo.resolve_script_lock(tmp_path,approved=True)
    assert st['current_stage']=='PROJECT_SCOPE_PLAN'


def test_scope_change_after_binding_cannot_be_consumed_by_master(tmp_path, monkeypatch):
    from project_scope import scope_manifest_sha256
    project_state(tmp_path,('PU001','PU002'))
    ledger(tmp_path,['PU001'])
    monkeypatch.setattr(mo,'_unit_semantic_errors',lambda root,uid: [])
    scope=json.loads((tmp_path/'state/PROJECT_SCOPE.json').read_text(encoding='utf-8'))
    scope['production_units']=[{'unit_id':'PU001','scene_ids':['SC001','SC002']}]
    scope['scope_manifest_sha256']=scope_manifest_sha256(scope)
    dump(tmp_path/'state/PROJECT_SCOPE.json',scope)
    try: mo.pass_stage(tmp_path,'PRODUCTION_LEDGER',artifact='PRODUCTION_LEDGER.json')
    except ValueError as exc: assert 'MASTER_SCOPE_BINDING_STALE' in str(exc)
    else: raise AssertionError


def test_ledger_timeline_gap_cannot_advance(tmp_path, monkeypatch):
    project_state(tmp_path); ledger(tmp_path,['PU001'],rows=[{'unit_id':'PU001','start_seconds':5,'end_seconds':15,'status':'COMPLETE'}])
    monkeypatch.setattr(mo,'_unit_semantic_errors',lambda root,uid: [])
    try: mo.pass_stage(tmp_path,'PRODUCTION_LEDGER',artifact='PRODUCTION_LEDGER.json')
    except ValueError as exc: assert 'MASTER_LEDGER_TIMELINE_GAP' in str(exc)
    else: raise AssertionError


def test_project_scope_plan_rejects_dummy_artifact(tmp_path):
    project_state(tmp_path,('PU001',))
    st=mo.load_state(tmp_path); st['current_stage']='PROJECT_SCOPE_PLAN'; mo._write(tmp_path,st)
    artifact(tmp_path,'dummy.json')
    try: mo.pass_stage(tmp_path,'PROJECT_SCOPE_PLAN',artifact='dummy.json')
    except ValueError as exc: assert 'MASTER_PROJECT_SCOPE_ARTIFACT_REQUIRED' in str(exc)
    else: raise AssertionError


def test_rerun_mixed_affected_ids_restores_only_planned_unit(tmp_path):
    project_state(tmp_path, ('PU001','PU002'))
    st = mo.load_state(tmp_path)
    st.update({
        'completed_units': ['PU001'],
        'current_unit_id': None,
        'current_stage': 'EXPORTS',
        'stage_status': 'PENDING',
    })
    mo._write(tmp_path, st)

    st = mo.fail_stage(
        tmp_path,
        'EXPORTS',
        owner_stage='FORGE_AUDIT',
        affected_ids=['SC001', 'A001', 'PU001'],
        reason='mixed downstream impact',
    )

    assert st['current_unit_id'] == 'PU001'


def test_rerun_multiple_affected_units_restores_earliest_planned_unit(tmp_path):
    project_state(tmp_path, ('PU001','PU002','PU003'))
    st = mo.load_state(tmp_path)
    st.update({
        'completed_units': ['PU001','PU002','PU003'],
        'current_unit_id': None,
        'current_stage': 'EXPORTS',
        'stage_status': 'PENDING',
    })
    mo._write(tmp_path, st)

    st = mo.fail_stage(
        tmp_path,
        'EXPORTS',
        owner_stage='FORGE_AUDIT',
        affected_ids=['PU003', 'SC002', 'PU001'],
        reason='multiple affected production units',
    )

    assert st['current_unit_id'] == 'PU001'
