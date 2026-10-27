#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

ALLOWED={
 'packet_contract','unit_id','scene_scope','scope_manifest_sha256','expected_story_atom_ids','information_ids',
 'project_refs','inherited_state','generation_profile'
}

def _load(path:Path)->dict:
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict): raise ValueError(f'JSON root must be object: {path}')
    return value

def _sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()

def _unit(scope:dict, unit_id:str)->dict:
    for u in scope.get('production_units') or []:
        if isinstance(u,dict) and u.get('unit_id')==unit_id: return u
    raise ValueError(f'UNIT_NOT_PLANNED: {unit_id}')

def build_unit_packet(project_root:str|Path, unit_id:str)->dict:
    root=Path(project_root).resolve(); scope_p=root/'state/PROJECT_SCOPE.json'; story_p=root/'state/story_authority.json'; info_p=root/'state/information_ledger.json'
    scope=_load(scope_p); story=_load(story_p); info=_load(info_p); unit=_unit(scope,unit_id)
    scenes=list(unit.get('scene_ids') or []); atom_ids=[]
    for atom in story.get('atoms') or []:
        if isinstance(atom,dict) and atom.get('scene_id') in scenes:
            aid=str(atom.get('atom_id') or '').strip()
            if aid: atom_ids.append(aid)
    info_ids=[str(i.get('info_id')) for i in info.get('items') or [] if isinstance(i,dict) and str(i.get('info_id') or '').strip()]
    tail_path=root/'state/units'/f'{unit_id}_PREV_TAIL_STATE.json'
    inherited=_load(tail_path) if tail_path.is_file() else None
    return {
      'packet_contract':'AFD_PRODUCTION_UNIT_PACKET_V1','unit_id':unit_id,'scene_scope':scenes,
      'scope_manifest_sha256':scope.get('scope_manifest_sha256'),'expected_story_atom_ids':atom_ids,'information_ids':info_ids,
      'project_refs':{
        'project_scope':{'path':'state/PROJECT_SCOPE.json','sha256':_sha(scope_p)},
        'story_authority':{'path':'state/story_authority.json','sha256':_sha(story_p)},
        'information_ledger':{'path':'state/information_ledger.json','sha256':_sha(info_p)},
      },
      'inherited_state':inherited,
      'generation_profile':{},
    }

def validate_unit_packet(project_root:str|Path, packet:dict|None=None, unit_id:str|None=None)->list[str]:
    root=Path(project_root).resolve(); errors=[]
    try:
        if packet is None:
            if not unit_id: return ['PACKET_UNIT_ID_REQUIRED']
            packet=_load(root/'state/units'/f'{unit_id}_PACKET.json')
        scope=_load(root/'state/PROJECT_SCOPE.json'); story=_load(root/'state/story_authority.json'); info=_load(root/'state/information_ledger.json')
    except Exception as exc: return [f'PACKET_INVALID: {exc}']
    extra=set(packet)-ALLOWED
    if extra: errors.append('PACKET_UNSUPPORTED_FIELD: '+','.join(sorted(extra)))
    if packet.get('packet_contract')!='AFD_PRODUCTION_UNIT_PACKET_V1': errors.append('PACKET_CONTRACT_INVALID')
    uid=str(packet.get('unit_id') or unit_id or '')
    try: unit=_unit(scope,uid)
    except ValueError as exc: return errors+[str(exc)]
    if packet.get('scene_scope')!=unit.get('scene_ids'): errors.append('PACKET_SCENE_SCOPE_MISMATCH')
    if packet.get('scope_manifest_sha256')!=scope.get('scope_manifest_sha256'): errors.append('PACKET_SCOPE_HASH_MISMATCH')
    expected_atoms=[str(a.get('atom_id')) for a in story.get('atoms') or [] if isinstance(a,dict) and a.get('scene_id') in (unit.get('scene_ids') or [])]
    if packet.get('expected_story_atom_ids')!=expected_atoms: errors.append('PACKET_STORY_ATOMS_MISMATCH')
    valid_infos=[str(i.get('info_id')) for i in info.get('items') or [] if isinstance(i,dict) and str(i.get('info_id') or '').strip()]
    if any(x not in valid_infos for x in (packet.get('information_ids') or [])): errors.append('PACKET_INFORMATION_ID_UNKNOWN')
    refs=packet.get('project_refs') if isinstance(packet.get('project_refs'),dict) else {}
    for name,path in [('project_scope','state/PROJECT_SCOPE.json'),('story_authority','state/story_authority.json'),('information_ledger','state/information_ledger.json')]:
        ref=refs.get(name) if isinstance(refs.get(name),dict) else {}
        target=root/path
        if ref.get('path')!=path or not target.is_file() or ref.get('sha256')!=_sha(target): errors.append(f'PACKET_{name.upper()}_HASH_MISMATCH')
    if packet.get('inherited_state') is not None:
        tail=root/'state/units'/f'{uid}_PREV_TAIL_STATE.json'
        if not tail.is_file() or packet.get('inherited_state')!=_load(tail): errors.append('PACKET_INHERITED_STATE_UNPROVEN')
    return errors

def write_unit_packet(project_root:str|Path, unit_id:str)->dict:
    root=Path(project_root).resolve(); packet=build_unit_packet(root,unit_id); errors=validate_unit_packet(root,packet,unit_id)
    if errors: raise ValueError('; '.join(errors))
    p=root/'state/units'/f'{unit_id}_PACKET.json'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); return packet

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root',required=True); ap.add_argument('--unit-id',required=True); ap.add_argument('action',choices=['build','validate']); a=ap.parse_args()
    if a.action=='build': print(json.dumps(write_unit_packet(a.project_root,a.unit_id),ensure_ascii=False,indent=2))
    else:
        e=validate_unit_packet(a.project_root,unit_id=a.unit_id); print('PASS' if not e else 'FAIL\n- '+'\n- '.join(e)); raise SystemExit(1 if e else 0)
