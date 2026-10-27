from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_public_release_identity_is_471():
    skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
    manifest = json.loads((ROOT / 'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    agent = (ROOT / 'agents' / 'openai.yaml').read_text(encoding='utf-8')
    assert 'version: "4.7.1-fusion"' in skill
    assert '# AI Film Director 4.7.1 Fusion' in skill
    assert manifest['edition'] == 'AI-Film-Director-4.7.1-Fusion'
    assert manifest['package_version'] == '4.7.1-fusion'
    assert 'AI Film Director 4.7.1 Fusion' in agent
