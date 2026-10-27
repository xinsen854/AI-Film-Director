from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from verify_master_fusion import validate_master_fusion


def test_reverse_audit_accepts_the_real_fusion_tree():
    assert validate_master_fusion(ROOT) == []


def test_reverse_audit_detects_reactivated_afd_emotion_authority(tmp_path):
    clone = tmp_path / 'skill'
    shutil.copytree(ROOT, clone, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    module = clone / 'references/modules/audience-emotion-architecture/module.md'
    module.write_text('# active old emotion authority\n', encoding='utf-8')
    errors = validate_master_fusion(clone)
    assert any('COMPATIBILITY_PROJECTION_ONLY' in item for item in errors)


def test_reverse_audit_detects_forge_source_hash_drift(tmp_path):
    clone = tmp_path / 'skill'
    shutil.copytree(ROOT, clone, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    renderer = clone / 'references/forge/source/emotion-story-forge/scripts/render_emotion_map.py'
    renderer.write_text(renderer.read_text(encoding='utf-8') + '\n# drift\n', encoding='utf-8')
    errors = validate_master_fusion(clone)
    assert any('Forge source hash mismatch' in item for item in errors)
