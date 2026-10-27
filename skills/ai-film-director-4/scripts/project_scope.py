#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ALLOWED_FIELDS={
    'scope_contract','project_id','work_format','locked_screenplay_path','locked_screenplay_sha256',
    'project_brief_sha256','target_runtime_seconds','scene_count','scene_ids','production_units','scope_manifest_sha256'
}
SCENE_RE=re.compile(r'^\s*(?:SCENE\s*|SC\s*|第\s*)(\d{1,4})(?:\s*场)?\s*(?:[｜|:：\-—].*)?$',re.I)


def _load(path:Path)->dict:
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict): raise ValueError(f'JSON root must be object: {path}')
    return value

def _sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _canonical(value:object)->bytes:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')

def scope_manifest_sha256(scope:dict)->str:
    body={k:v for k,v in scope.items() if k!='scope_manifest_sha256'}
    return hashlib.sha256(_canonical(body)).hexdigest()

def extract_scene_ids(text:str)->list[str]:
    ids=[]
    for line in text.splitlines():
        m=SCENE_RE.fullmatch(line)
        if not m: continue
        sid=f'SC{int(m.group(1)):03d}'
        if sid in ids: raise ValueError(f'DUPLICATE_SCENE_ID: {sid}')
        ids.append(sid)
    if not ids: raise ValueError('SCENE_HEADINGS_REQUIRED: locked screenplay must expose explicit scene headings before PROJECT_SCOPE can be built')
    return ids

def _brief_runtime(brief:dict)->float:
    for key in ('target_total_runtime_seconds','target_runtime_seconds'):
        value=brief.get(key)
        if isinstance(value,(int,float)) and not isinstance(value,bool) and float(value)>0: return float(value)
    raise ValueError('PROJECT_RUNTIME_REQUIRED: confirmed project brief must define target runtime seconds')

def build_project_scope(project_root:str|Path, grouping:list[list[str]]|None=None)->dict:
    root=Path(project_root).resolve(); master=_load(root/'state/master_orchestrator.json'); brief=_load(root/'state/project_brief.json')
    if master.get('lock_status')!='LOCKED': raise ValueError('PROJECT_SCOPE_LOCK_REQUIRED')
    rel=str(master.get('locked_screenplay_path') or '').strip(); lock=(root/rel).resolve()
    if not lock.is_file(): raise ValueError('PROJECT_SCOPE_LOCKED_SCREENPLAY_MISSING')
    current_sha=_sha(lock)
    if current_sha!=master.get('locked_screenplay_sha256'): raise ValueError('PROJECT_SCOPE_LOCK_HASH_MISMATCH')
    if brief.get('work_format')!='film': raise ValueError('PROJECT_SCOPE_V1_FILM_ONLY')
    scene_ids=extract_scene_ids(lock.read_text(encoding='utf-8'))
    groups=grouping or [[sid] for sid in scene_ids]
    units=[{'unit_id':f'PU{i:03d}','scene_ids':list(g)} for i,g in enumerate(groups,1)]
    scope={
      'scope_contract':'AFD_PROJECT_SCOPE_V1','project_id':str(brief.get('project_id') or 'FILM01'), 'work_format':'film',
      'locked_screenplay_path':rel,'locked_screenplay_sha256':current_sha,'project_brief_sha256':_sha(root/'state/project_brief.json'),
      'target_runtime_seconds':_brief_runtime(brief),'scene_count':len(scene_ids),'scene_ids':scene_ids,'production_units':units,
    }
    scope['scope_manifest_sha256']=scope_manifest_sha256(scope)
    return scope

def validate_project_scope(project_root:str|Path, scope:dict|None=None)->list[str]:
    root=Path(project_root).resolve(); errors=[]
    try:
        scope=scope or _load(root/'state/PROJECT_SCOPE.json')
        master=_load(root/'state/master_orchestrator.json'); brief=_load(root/'state/project_brief.json')
    except Exception as exc: return [f'PROJECT_SCOPE_INVALID: {exc}']
    extra=set(scope)-ALLOWED_FIELDS
    if extra: errors.append('PROJECT_SCOPE_UNSUPPORTED_FIELD: '+','.join(sorted(extra)))
    if scope.get('scope_contract')!='AFD_PROJECT_SCOPE_V1': errors.append('PROJECT_SCOPE_CONTRACT_INVALID')
    rel=str(master.get('locked_screenplay_path') or '')
    lock=(root/rel).resolve()
    if not lock.is_file(): return errors+['PROJECT_SCOPE_LOCKED_SCREENPLAY_MISSING']
    try: actual=extract_scene_ids(lock.read_text(encoding='utf-8'))
    except ValueError as exc: return errors+[str(exc)]
    if _sha(lock)!=master.get('locked_screenplay_sha256') or scope.get('locked_screenplay_sha256')!=_sha(lock): errors.append('PROJECT_SCOPE_LOCK_HASH_MISMATCH')
    if scope.get('locked_screenplay_path')!=rel: errors.append('PROJECT_SCOPE_LOCK_PATH_MISMATCH')
    if scope.get('project_brief_sha256')!=_sha(root/'state/project_brief.json'): errors.append('PROJECT_SCOPE_BRIEF_HASH_MISMATCH')
    if scope.get('project_id')!=str(brief.get('project_id') or 'FILM01'): errors.append('PROJECT_SCOPE_PROJECT_ID_MISMATCH')
    if scope.get('work_format')!=brief.get('work_format'): errors.append('PROJECT_SCOPE_FORMAT_MISMATCH')
    try:
        if float(scope.get('target_runtime_seconds'))!=_brief_runtime(brief): errors.append('PROJECT_SCOPE_RUNTIME_MISMATCH')
    except Exception: errors.append('PROJECT_SCOPE_RUNTIME_MISMATCH')
    if scope.get('scene_ids')!=actual or scope.get('scene_count')!=len(actual): errors.append('PROJECT_SCOPE_SCENE_SET_MISMATCH')
    units=scope.get('production_units')
    if not isinstance(units,list) or not units: errors.append('PROJECT_SCOPE_UNITS_REQUIRED')
    else:
        flat=[]; expected_index=0
        for i,u in enumerate(units,1):
            if not isinstance(u,dict) or set(u)-{'unit_id','scene_ids'}: errors.append(f'PROJECT_SCOPE_UNIT_INVALID:{i}'); continue
            if u.get('unit_id')!=f'PU{i:03d}': errors.append('PROJECT_SCOPE_UNIT_ID_ORDER_INVALID')
            scenes=u.get('scene_ids')
            if not isinstance(scenes,list) or not scenes: errors.append('PROJECT_SCOPE_UNIT_EMPTY'); continue
            positions=[]
            for sid in scenes:
                if sid not in actual: errors.append(f'PROJECT_SCOPE_UNKNOWN_SCENE:{sid}')
                else: positions.append(actual.index(sid))
            if positions and positions!=list(range(min(positions),min(positions)+len(positions))): errors.append('PROJECT_SCOPE_UNIT_SCENE_ORDER_INVALID')
            if positions and min(positions)!=expected_index: errors.append('PROJECT_SCOPE_UNIT_SCENE_ORDER_INVALID')
            expected_index += len(positions)
            flat.extend(scenes)
        if flat!=actual: errors.append('PROJECT_SCOPE_UNIT_ASSIGNMENT_MISMATCH')
        if len(flat)!=len(set(flat)): errors.append('PROJECT_SCOPE_DUPLICATE_SCENE_ASSIGNMENT')
    if scope.get('scope_manifest_sha256')!=scope_manifest_sha256(scope): errors.append('PROJECT_SCOPE_HASH_MISMATCH')
    return errors

def write_project_scope(project_root:str|Path, grouping:list[list[str]]|None=None)->dict:
    root=Path(project_root).resolve(); scope=build_project_scope(root,grouping); errors=validate_project_scope(root,scope)
    if errors: raise ValueError('; '.join(errors))
    path=root/'state/PROJECT_SCOPE.json'; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); return scope

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root',required=True); ap.add_argument('action',choices=['build','validate']); args=ap.parse_args()
    if args.action=='build': print(json.dumps(write_project_scope(args.project_root),ensure_ascii=False,indent=2))
    else:
        e=validate_project_scope(args.project_root); print('PASS' if not e else 'FAIL\n- '+'\n- '.join(e)); raise SystemExit(1 if e else 0)
