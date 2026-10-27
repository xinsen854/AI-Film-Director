#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from typing import Any

REQ_KINDS={'character_base','character_state','location','prop','entity','voice'}
REQ_ALLOWED={'requirement_id','kind','canonical_name','state_label','parent_requirement_id','scene_ids','source_evidence'}
MANIFEST_ALLOWED={'requirements_contract','scope_manifest_sha256','locked_screenplay_sha256','requirements','scene_inventory','requirements_manifest_sha256'}
BASELINE_ALLOWED={'scope_manifest_sha256','requirements_manifest_sha256','requirement_bindings','existing_media_accounting'}
ALL_SCOPE_MARKERS={'PROJECT','ALL','*','全项目','全片'}


def _load(path:Path)->dict:
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict): raise ValueError(f'JSON root must be object: {path}')
    return value

def _dump(path:Path,value:object)->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def _sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _canonical(value:object)->bytes:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')

def requirements_manifest_sha256(payload:dict)->str:
    body={k:v for k,v in payload.items() if k!='requirements_manifest_sha256'}
    return hashlib.sha256(_canonical(body)).hexdigest()

def _asset_records(payload:dict)->tuple[dict[str,dict],dict[str,str]]:
    lib=payload.get('ASSET_LIBRARY') if isinstance(payload.get('ASSET_LIBRARY'),dict) else {}
    records={}; kinds={}
    for group,kind in [('character_assets','character_base'),('location_assets','location'),('prop_assets','prop'),('g_assets','entity'),('voice_assets','voice')]:
        for rec in lib.get(group,[]) if isinstance(lib.get(group),list) else []:
            if isinstance(rec,dict) and isinstance(rec.get('asset_id'),str): records[rec['asset_id']]=rec; kinds[rec['asset_id']]=kind
    for rec in lib.get('persistent_states',[]) if isinstance(lib.get('persistent_states'),list) else []:
        if isinstance(rec,dict) and isinstance(rec.get('state_id'),str):
            copy=dict(rec); copy['asset_id']=rec['state_id']; records[rec['state_id']]=copy; kinds[rec['state_id']]='character_state'
    return records,kinds

def validate_project_asset_requirements(project_root:str|Path,payload:dict|None=None)->list[str]:
    root=Path(project_root).resolve(); errors=[]
    try:
        payload=payload or _load(root/'state/project_asset_requirements.json'); scope=_load(root/'state/PROJECT_SCOPE.json')
    except Exception as exc: return [f'ASSET_REQUIREMENTS_INVALID: {exc}']
    extra=set(payload)-MANIFEST_ALLOWED
    if extra: errors.append('ASSET_REQUIREMENTS_UNSUPPORTED_FIELD: '+','.join(sorted(extra)))
    if payload.get('requirements_contract')!='AFD_PROJECT_ASSET_REQUIREMENTS_V1': errors.append('ASSET_REQUIREMENTS_CONTRACT_INVALID')
    if payload.get('scope_manifest_sha256')!=scope.get('scope_manifest_sha256'): errors.append('ASSET_REQUIREMENTS_SCOPE_HASH_MISMATCH')
    if payload.get('locked_screenplay_sha256')!=scope.get('locked_screenplay_sha256'): errors.append('ASSET_REQUIREMENTS_SCREENPLAY_HASH_MISMATCH')
    lock_rel=str(scope.get('locked_screenplay_path') or '')
    lock_path=(root/lock_rel).resolve() if lock_rel else None
    if lock_path is None or not lock_path.is_file() or _sha(lock_path)!=payload.get('locked_screenplay_sha256'):
        errors.append('ASSET_REQUIREMENTS_SCREENPLAY_HASH_STALE')
    expected_scenes=list(scope.get('scene_ids') or []); expected_scene_set=set(expected_scenes)
    reqs=payload.get('requirements'); req_by_id={}
    if not isinstance(reqs,list): errors.append('ASSET_REQUIREMENTS_LIST_REQUIRED'); reqs=[]
    for i,req in enumerate(reqs):
        where=f'requirements[{i}]'
        if not isinstance(req,dict): errors.append(f'{where} must be object'); continue
        extra_req=set(req)-REQ_ALLOWED
        if extra_req: errors.append(f'ASSET_REQUIREMENTS_UNSUPPORTED_FIELD: {where} '+','.join(sorted(extra_req)))
        rid=str(req.get('requirement_id') or '')
        if not re.fullmatch(r'AR\d{3,}',rid): errors.append(f'ASSET_REQUIREMENT_ID_INVALID:{rid}')
        if rid in req_by_id: errors.append(f'ASSET_REQUIREMENT_DUPLICATE:{rid}')
        req_by_id[rid]=req
        kind=req.get('kind')
        if kind not in REQ_KINDS: errors.append(f'ASSET_REQUIREMENT_KIND_INVALID:{rid}')
        if not isinstance(req.get('canonical_name'),str) or not req['canonical_name'].strip(): errors.append(f'ASSET_REQUIREMENT_NAME_MISSING:{rid}')
        scenes=req.get('scene_ids')
        if not isinstance(scenes,list) or not scenes or any(s not in expected_scene_set for s in scenes): errors.append(f'ASSET_REQUIREMENT_SCENE_INVALID:{rid}')
        evidence=req.get('source_evidence')
        if not isinstance(evidence,list) or not evidence or any(not isinstance(x,str) or not x.strip() for x in evidence): errors.append(f'ASSET_REQUIREMENT_EVIDENCE_MISSING:{rid}')
        if kind=='character_state':
            if not isinstance(req.get('state_label'),str) or not req['state_label'].strip(): errors.append(f'ASSET_REQUIREMENT_STATE_LABEL_MISSING:{rid}')
            parent=str(req.get('parent_requirement_id') or '')
            if not parent: errors.append(f'ASSET_REQUIREMENT_PARENT_MISSING:{rid}')
    inventory=payload.get('scene_inventory')
    inv_by_scene={}
    if not isinstance(inventory,list): errors.append('ASSET_REQUIREMENTS_SCENE_INVENTORY_REQUIRED'); inventory=[]
    for row in inventory:
        if not isinstance(row,dict) or set(row)-{'scene_id','requirement_ids'}: errors.append('ASSET_REQUIREMENTS_SCENE_INVENTORY_INVALID'); continue
        sid=str(row.get('scene_id') or '')
        if sid in inv_by_scene: errors.append(f'ASSET_REQUIREMENTS_SCENE_INVENTORY_DUPLICATE:{sid}')
        ids=row.get('requirement_ids') if isinstance(row.get('requirement_ids'),list) else []
        if len(ids)!=len(set(ids)) or any(r not in req_by_id for r in ids): errors.append(f'ASSET_REQUIREMENTS_SCENE_INVENTORY_INVALID:{sid}')
        inv_by_scene[sid]=ids
    if set(inv_by_scene)!=expected_scene_set: errors.append(f'ASSET_REQUIREMENTS_SCENE_INVENTORY_MISMATCH: missing={sorted(expected_scene_set-set(inv_by_scene))} extra={sorted(set(inv_by_scene)-expected_scene_set)}')
    for rid,req in req_by_id.items():
        parent=req.get('parent_requirement_id')
        if req.get('kind')=='character_state' and parent:
            p=req_by_id.get(str(parent))
            if not p or p.get('kind')!='character_base' or p.get('canonical_name')!=req.get('canonical_name'):
                errors.append(f'ASSET_REQUIREMENT_PARENT_INVALID:{rid}')
        actual={sid for sid,ids in inv_by_scene.items() if rid in ids}
        expected=set(req.get('scene_ids') or [])
        if actual!=expected: errors.append(f'ASSET_REQUIREMENT_SCENE_INVENTORY_DISAGREES:{rid}')
    if payload.get('requirements_manifest_sha256')!=requirements_manifest_sha256(payload): errors.append('ASSET_REQUIREMENTS_HASH_MISMATCH')
    return errors

def _scope_covers(record:dict, scenes:list[str])->bool:
    raw=record.get('use_scope')
    if not isinstance(raw,list): return False
    vals={str(x).strip() for x in raw}
    if vals & ALL_SCOPE_MARKERS: return True
    return set(scenes).issubset(vals)

def _existing_media(root:Path)->list[dict]:
    p=root/'state/project_brief.json'
    if not p.is_file(): return []
    try: brief=_load(p)
    except Exception: return []
    items=brief.get('existing_media')
    return [x if isinstance(x,dict) else {'value':x} for x in items] if isinstance(items,list) else []

def validate_project_asset_library_coverage(project_root:str|Path,library_payload:dict|None=None,requirements:dict|None=None)->list[str]:
    root=Path(project_root).resolve(); errors=[]
    try:
        library_payload=library_payload or _load(root/'assets/ASSET_LIBRARY.json')
        requirements=requirements or _load(root/'state/project_asset_requirements.json')
        scope=_load(root/'state/PROJECT_SCOPE.json')
    except Exception as exc: return [f'ASSET_PROJECT_BASELINE_INVALID: {exc}']
    from render_asset_library import validate_asset_library_payload
    errors.extend(f'ASSET_LIBRARY:{e}' for e in validate_asset_library_payload(library_payload))
    errors.extend(validate_project_asset_requirements(root,requirements))
    lib=library_payload.get('ASSET_LIBRARY') if isinstance(library_payload.get('ASSET_LIBRARY'),dict) else {}
    source=lib.get('source') if isinstance(lib.get('source'),dict) else {}
    if source.get('production_range')!='PROJECT': errors.append('ASSET_PROJECT_BASELINE_RANGE_INVALID: ASSET_LIBRARY.source.production_range must be PROJECT')
    baseline=lib.get('project_baseline') if isinstance(lib.get('project_baseline'),dict) else None
    if baseline is None: return errors+['ASSET_PROJECT_BASELINE_MISSING']
    extra=set(baseline)-BASELINE_ALLOWED
    if extra: errors.append('ASSET_PROJECT_BASELINE_UNSUPPORTED_FIELD: '+','.join(sorted(extra)))
    if baseline.get('scope_manifest_sha256')!=scope.get('scope_manifest_sha256'): errors.append('ASSET_PROJECT_BASELINE_SCOPE_HASH_MISMATCH')
    if baseline.get('requirements_manifest_sha256')!=requirements.get('requirements_manifest_sha256'): errors.append('ASSET_PROJECT_BASELINE_REQUIREMENTS_HASH_MISMATCH')
    bindings=baseline.get('requirement_bindings') if isinstance(baseline.get('requirement_bindings'),dict) else {}
    req_by_id={str(r.get('requirement_id')):r for r in requirements.get('requirements',[]) if isinstance(r,dict)}
    if set(bindings)!=set(req_by_id): errors.append(f'ASSET_REQUIREMENT_BINDING_SET_MISMATCH: missing={sorted(set(req_by_id)-set(bindings))} extra={sorted(set(bindings)-set(req_by_id))}')
    records,kinds=_asset_records(library_payload)
    for rid,req in req_by_id.items():
        aid=str(bindings.get(rid) or '')
        record=records.get(aid)
        if record is None:
            errors.append(f'ASSET_REQUIREMENT_UNSATISFIED:{rid}->{aid or "<missing>"}')
            continue
        if kinds.get(aid)!=req.get('kind'):
            errors.append(f'ASSET_REQUIREMENT_KIND_MISMATCH:{rid} expected={req.get("kind")} actual={kinds.get(aid)} asset={aid}')
            continue
        if not _scope_covers(record,list(req.get('scene_ids') or [])):
            errors.append(f'ASSET_REQUIREMENT_SCOPE_MISMATCH:{rid} asset={aid} scenes={req.get("scene_ids")} use_scope={record.get("use_scope")}')
        if req.get('kind')=='character_state':
            parent_req=req_by_id.get(str(req.get('parent_requirement_id') or ''))
            parent_asset=str(bindings.get(str(req.get('parent_requirement_id') or '')) or '')
            if not parent_req or str(record.get('inherits_from') or '')!=parent_asset:
                errors.append(f'ASSET_REQUIREMENT_STATE_PARENT_MISMATCH:{rid} asset={aid}')
    media=_existing_media(root)
    accounting=baseline.get('existing_media_accounting') if isinstance(baseline.get('existing_media_accounting'),list) else []
    seen=set()
    for row in accounting:
        if not isinstance(row,dict) or set(row)-{'brief_index','disposition','asset_id','canonical_file','reason'}:
            errors.append('EXISTING_MEDIA_ACCOUNTING_INVALID'); continue
        idx=row.get('brief_index')
        if not isinstance(idx,int) or idx<0 or idx>=len(media) or idx in seen:
            errors.append(f'EXISTING_MEDIA_ACCOUNTING_INVALID_INDEX:{idx}'); continue
        seen.add(idx)
        disposition=row.get('disposition')
        if disposition=='ASSET_BOUND':
            aid=str(row.get('asset_id') or ''); canonical=str(row.get('canonical_file') or '')
            rec=records.get(aid)
            if rec is None or not canonical:
                errors.append(f'EXISTING_MEDIA_BINDING_INVALID:{idx}'); continue
            try:
                path=(root/canonical).resolve(); path.relative_to((root/'assets/generated').resolve())
            except Exception:
                errors.append(f'EXISTING_MEDIA_CANONICAL_PATH_INVALID:{idx}'); continue
            if not path.is_file() or path.stat().st_size<=0:
                errors.append(f'EXISTING_MEDIA_CANONICAL_FILE_MISSING:{idx}')
            refs=rec.get('reference_media') if isinstance(rec.get('reference_media'),list) else []
            if canonical not in refs: errors.append(f'EXISTING_MEDIA_NOT_BOUND_TO_ASSET:{idx}->{aid}')
        elif disposition=='NON_ASSET_MEDIA':
            if row.get('asset_id') or row.get('canonical_file'): errors.append(f'EXISTING_MEDIA_NON_ASSET_HAS_BINDING:{idx}')
            if not isinstance(row.get('reason'),str) or not row.get('reason').strip(): errors.append(f'EXISTING_MEDIA_NON_ASSET_REASON_REQUIRED:{idx}')
        else: errors.append(f'EXISTING_MEDIA_DISPOSITION_INVALID:{idx}')
    if seen!=set(range(len(media))): errors.append(f'EXISTING_MEDIA_UNACCOUNTED: missing_brief_indexes={sorted(set(range(len(media)))-seen)}')
    return errors

def _identity_snapshot(payload:dict)->dict[str,dict]:
    lib=payload['ASSET_LIBRARY']; out={}
    for group in ('character_assets','location_assets','prop_assets','g_assets','voice_assets'):
        for rec in lib.get(group,[]) or []:
            if not isinstance(rec,dict): continue
            aid=str(rec.get('asset_id') or '')
            if aid: out[aid]={'group':group,'name':rec.get('name'),'character_asset_id':rec.get('character_asset_id')}
    for rec in lib.get('persistent_states',[]) or []:
        if not isinstance(rec,dict): continue
        aid=str(rec.get('state_id') or '')
        if aid: out[aid]={'group':'persistent_states','inherits_from':rec.get('inherits_from'),'state_category':rec.get('state_category')}
    return out

def lock_project_asset_baseline(project_root:str|Path)->dict:
    root=Path(project_root).resolve(); lib=_load(root/'assets/ASSET_LIBRARY.json'); req=_load(root/'state/project_asset_requirements.json')
    errors=validate_project_asset_library_coverage(root,lib,req)
    if errors: raise ValueError('ASSET_BASELINE_LOCK_FAILED: '+'; '.join(errors))
    master_path=root/'state/master_orchestrator.json'
    master=_load(master_path) if master_path.is_file() else None
    req_hash=str(req.get('requirements_manifest_sha256') or '')
    if isinstance(master,dict):
        bound=str(master.get('project_asset_requirements_sha256') or '')
        if bound and bound!=req_hash:
            raise ValueError('MASTER_ASSET_REQUIREMENTS_BINDING_STALE: current requirements differ from the requirements first bound by Master')
    baseline=lib['ASSET_LIBRARY']['project_baseline']; snapshot=_identity_snapshot(lib)
    receipt={
      'baseline_contract':'AFD_PROJECT_ASSET_BASELINE_LOCK_V1','scope_manifest_sha256':baseline['scope_manifest_sha256'],
      'requirements_manifest_sha256':baseline['requirements_manifest_sha256'],'baseline_asset_ids':sorted(snapshot),
      'baseline_requirement_bindings':dict(baseline['requirement_bindings']),'asset_identity_snapshot':snapshot,
    }
    receipt_sha=hashlib.sha256(_canonical(receipt)).hexdigest()
    receipt['baseline_lock_sha256']=receipt_sha
    if isinstance(master,dict):
        previous_lock=str(master.get('project_asset_baseline_lock_sha256') or '')
        if previous_lock and previous_lock!=receipt_sha:
            raise ValueError('MASTER_ASSET_BASELINE_BINDING_STALE: cannot redefine an already-bound project asset baseline')
    _dump(root/'state/project_asset_baseline.json',receipt)
    if isinstance(master,dict):
        master['project_asset_requirements_sha256']=req_hash
        master['project_asset_baseline_lock_sha256']=receipt_sha
        _dump(master_path,master)
    return receipt

def validate_asset_baseline_lock(project_root:str|Path)->list[str]:
    root=Path(project_root).resolve(); errors=[]
    try:
        receipt=_load(root/'state/project_asset_baseline.json'); lib=_load(root/'assets/ASSET_LIBRARY.json'); req=_load(root/'state/project_asset_requirements.json')
    except Exception as exc: return [f'ASSET_BASELINE_LOCK_INVALID:{exc}']
    if receipt.get('baseline_contract')!='AFD_PROJECT_ASSET_BASELINE_LOCK_V1': errors.append('ASSET_BASELINE_LOCK_CONTRACT_INVALID')
    errors.extend(validate_project_asset_library_coverage(root,lib,req))
    current=_identity_snapshot(lib); baseline_ids=set(receipt.get('baseline_asset_ids') or [])
    missing=baseline_ids-set(current)
    if missing: errors.append(f'BASELINE_ASSET_REMOVED:{sorted(missing)}')
    expected_snapshot=receipt.get('asset_identity_snapshot') if isinstance(receipt.get('asset_identity_snapshot'),dict) else {}
    for aid in baseline_ids & set(current):
        if current[aid]!=expected_snapshot.get(aid): errors.append(f'BASELINE_ASSET_IDENTITY_CHANGED:{aid}')
    baseline=lib.get('ASSET_LIBRARY',{}).get('project_baseline',{})
    master_path=root/'state/master_orchestrator.json'
    if master_path.is_file():
        try:
            master=_load(master_path)
            if master.get('project_asset_requirements_sha256') not in (None,'',receipt.get('requirements_manifest_sha256')):
                errors.append('MASTER_ASSET_REQUIREMENTS_BINDING_STALE')
            expected_lock=hashlib.sha256(_canonical({k:v for k,v in receipt.items() if k!='baseline_lock_sha256'})).hexdigest()
            if receipt.get('baseline_lock_sha256')!=expected_lock:
                errors.append('BASELINE_LOCK_HASH_MISMATCH')
            if master.get('project_asset_baseline_lock_sha256') not in (None,'',receipt.get('baseline_lock_sha256')):
                errors.append('MASTER_ASSET_BASELINE_BINDING_STALE')
        except Exception as exc:
            errors.append(f'MASTER_ASSET_BASELINE_INVALID:{exc}')
    if baseline.get('scope_manifest_sha256')!=receipt.get('scope_manifest_sha256'): errors.append('BASELINE_SCOPE_BINDING_CHANGED')
    if baseline.get('requirements_manifest_sha256')!=receipt.get('requirements_manifest_sha256'): errors.append('BASELINE_REQUIREMENTS_BINDING_CHANGED')
    if baseline.get('requirement_bindings')!=receipt.get('baseline_requirement_bindings'): errors.append('BASELINE_REQUIREMENT_BINDING_CHANGED')
    return errors

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root',required=True); ap.add_argument('action',choices=['validate-requirements','validate-library','lock','validate-lock']); a=ap.parse_args()
    if a.action=='validate-requirements': errors=validate_project_asset_requirements(a.project_root)
    elif a.action=='validate-library': errors=validate_project_asset_library_coverage(a.project_root)
    elif a.action=='lock': print(json.dumps(lock_project_asset_baseline(a.project_root),ensure_ascii=False,indent=2)); raise SystemExit(0)
    else: errors=validate_asset_baseline_lock(a.project_root)
    print('PASS' if not errors else 'FAIL\n- '+'\n- '.join(errors)); raise SystemExit(1 if errors else 0)
