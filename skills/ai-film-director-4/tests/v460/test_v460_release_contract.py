import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_v460_public_version_is_consistent():
    skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
    package = json.loads((ROOT / 'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    agent = (ROOT / 'agents/openai.yaml').read_text(encoding='utf-8')
    assert 'version: "4.7.1-fusion"' in skill
    assert '# AI Film Director 4.7.1 Fusion' in skill
    assert package['edition'] == 'AI-Film-Director-4.7.1-Fusion'
    assert package['package_version'] == '4.7.1-fusion'
    assert 'AI Film Director 4.7.1 Fusion' in agent


def test_v460_release_contract_names_the_real_delta_not_runtime_api():
    text = (ROOT / 'references/contracts/release-validation-contract.md').read_text(encoding='utf-8').lower()
    for token in ('size-ref', 'scene geo', 'reference role', 'acting', 'facs', 'ai-vfx', 'off-screen', 'monotony'):
        assert token in text
    assert 'video api' in text
    assert 'not active' in text or '未启用' in text
