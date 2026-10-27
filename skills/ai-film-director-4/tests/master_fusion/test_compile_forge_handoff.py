from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
TESTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from compile_forge_handoff import compile_design, compile_locked_audit
from master_orchestrator import init_state, pass_stage
from test_hardening_regressions import _payload




def _artifact(root: Path, stage: str) -> str:
    path = root / 'stage-artifacts' / f'{stage}.txt'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stage, encoding='utf-8')
    return path.relative_to(root).as_posix()


def _at_design_handoff(root: Path) -> None:
    init_state(root, 'REVIEW_BEFORE_LOCK')
    pass_stage(root, 'PROJECT_INTAKE', artifact=_artifact(root, 'PROJECT_INTAKE'))
    pass_stage(root, 'FORGE_DESIGN', artifact=_artifact(root, 'FORGE_DESIGN'))


def _at_locked_audit_handoff(root: Path) -> None:
    candidate = root / 'lock_candidates' / 'EP01.md'
    candidate.parent.mkdir(parents=True, exist_ok=True)
    if not candidate.exists():
        candidate.write_text('locked candidate', encoding='utf-8')
    init_state(root, 'AUTO_ACCEPT_AFTER_QC')
    for stage in ('PROJECT_INTAKE','FORGE_DESIGN','DESIGN_HANDOFF','CREATIVE_BIBLE','SCREENWRITER'):
        pass_stage(root, stage, artifact=_artifact(root, stage))
    pass_stage(root, 'FORGE_GATE_QC_DEAI', artifact='lock_candidates/EP01.md')
    pass_stage(root, 'FORGE_AUDIT', artifact=_artifact(root, 'FORGE_AUDIT'))

def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_design_compiler_only_combines_authored_story_and_afd_visual(tmp_path):
    design = tmp_path / 'forge_design.json'
    design.write_text(json.dumps({
        'meta': {'workflow_stage': 'design', 'blueprint_version': 'B7'},
        'integration': {'afd': {'creative_bible_story_markdown': '## 故事\nForge故事事实'}}
    }, ensure_ascii=False), encoding='utf-8')
    visual = tmp_path / 'state' / 'afd_visual_production.md'
    visual.parent.mkdir(parents=True)
    visual.write_text('## 视觉制作\nAFD视觉规范', encoding='utf-8')

    _at_design_handoff(tmp_path)
    result = compile_design(tmp_path, design, visual)
    bible = (tmp_path / 'PROJECT_CREATIVE_BIBLE.md').read_text(encoding='utf-8')
    assert 'Forge故事事实' in bible
    assert 'AFD视觉规范' in bible
    assert result['design_sha256'] == _sha(tmp_path / 'state' / 'forge_design.json')


def test_locked_audit_compiler_copies_only_explicit_afd_namespace(tmp_path):
    candidate = tmp_path / 'lock_candidates' / 'EP01.md'
    candidate.parent.mkdir(parents=True)
    candidate.write_text('# EP01\n锁定正文', encoding='utf-8')
    audit = tmp_path / 'audit.json'
    payload = _payload()
    payload['meta']['blueprint_version'] = 'B7'
    payload['integration']['afd']['script_version'] = 'S3'
    expected_story = payload['integration']['afd']['story_authority']
    expected_information = payload['integration']['afd']['information_ledger']
    audit.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')

    _at_locked_audit_handoff(tmp_path)
    result = compile_locked_audit(tmp_path, audit)
    out_script = tmp_path / 'screenplay' / 'EP01_LOCKED_SCREENPLAY.md'
    assert out_script.read_text(encoding='utf-8') == candidate.read_text(encoding='utf-8')
    assert json.loads((tmp_path/'state/story_authority.json').read_text(encoding='utf-8')) == expected_story
    assert json.loads((tmp_path/'state/information_ledger.json').read_text(encoding='utf-8')) == expected_information
    causal = json.loads((tmp_path/'state/audience_causal/EP01_SC01.json').read_text(encoding='utf-8'))
    assert causal['must_not_be_revealed'] == ['钥匙在抽屉']
    alignment = json.loads((tmp_path/'state/forge_alignment.json').read_text(encoding='utf-8'))
    assert alignment['screenplay_sha256'] == _sha(out_script)
    assert alignment['forge_audit_sha256'] == _sha(tmp_path/'state/forge_locked_audit.json')
    assert alignment['lock_status'] == 'LOCKED'
    assert alignment['units']['EP01']['screenplay_sha256'] == alignment['screenplay_sha256']
    assert alignment['units']['EP01']['forge_audit_sha256'] == alignment['forge_audit_sha256']
    assert result['unit_id'] == 'EP01'


def test_locked_audit_compiler_refuses_to_infer_missing_scene_handoffs(tmp_path):
    audit = tmp_path / 'audit.json'
    payload = _payload()
    del payload['integration']['afd']['scene_handoffs']
    audit.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    _at_locked_audit_handoff(tmp_path)
    try:
        compile_locked_audit(tmp_path, audit)
    except ValueError as exc:
        assert 'integration.afd' in str(exc)
    else:
        raise AssertionError('compiler must not invent missing integration data')


def test_design_bridge_cannot_run_outside_master_design_handoff_stage(tmp_path):
    design = tmp_path / 'forge_design.json'
    design.write_text(json.dumps({
        'meta': {'workflow_stage': 'design'},
        'integration': {'afd': {'creative_bible_story_markdown': '故事'}}
    }, ensure_ascii=False), encoding='utf-8')
    visual = tmp_path / 'visual.md'
    visual.write_text('视觉', encoding='utf-8')
    try:
        compile_design(tmp_path, design, visual)
    except ValueError as exc:
        assert 'MASTER_STAGE_REQUIRED' in str(exc)
    else:
        raise AssertionError('bridge must be controlled by master stage state')


def test_locked_audit_bridge_rejects_script_changed_after_master_lock(tmp_path):
    candidate = tmp_path / 'lock_candidates' / 'EP01.md'
    candidate.parent.mkdir(parents=True)
    candidate.write_text('locked v1', encoding='utf-8')
    _at_locked_audit_handoff(tmp_path)
    candidate.write_text('changed after lock', encoding='utf-8')
    audit = tmp_path / 'audit.json'
    audit.write_text(json.dumps(_payload(), ensure_ascii=False), encoding='utf-8')
    try:
        compile_locked_audit(tmp_path, audit)
    except ValueError as exc:
        assert 'MASTER_LOCK_MISMATCH' in str(exc)
    else:
        raise AssertionError('locked-audit bridge must reject changed screenplay bytes')
