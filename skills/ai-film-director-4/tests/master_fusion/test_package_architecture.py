from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_only_one_public_skill_file_and_no_forge_agents():
    skills = list(ROOT.rglob('SKILL.md'))
    assert skills == [ROOT / 'SKILL.md']
    assert not list((ROOT/'references/forge').rglob('openai.yaml'))


def test_root_skill_declares_forge_emotion_authority_and_exact_order():
    text = (ROOT/'SKILL.md').read_text(encoding='utf-8')
    assert 'AFD MASTER ORCHESTRATOR' in text
    assert 'Forge AUDIT' in text
    assert 'Forge Renderer' in text
    assert '总控 = 状态机 + 路由器 + 闸门' in text
    order = [
        '01 项目接入','02 Forge DESIGN','03 设计桥接','04 项目创作圣经',
        '05 Human-Truth Screenwriter','06 Forge Gate / QC / De-AI','07 剧本锁定控制器',
        '08 Forge AUDIT','09 锁稿审计桥接','10 Forge Emotion Renderer',
        '11 Scene Intelligence','12 Capability Router','13 Director Craft','14 AFD Scene Direction',
        '15 Asset Engine','16 Spatial','17 Shot / Segment','18 Final Hard QC','19 Production Ledger','20 八件套导出'
    ]
    positions = [text.index(token) for token in order]
    assert positions == sorted(positions)


def test_afd_upstream_modules_are_adapters_not_second_authorities():
    story = (ROOT/'references/modules/story-development/module.md').read_text(encoding='utf-8')
    screenplay = (ROOT/'references/modules/screenplay-authority/module.md').read_text(encoding='utf-8')
    emotion = (ROOT/'references/modules/audience-emotion-architecture/module.md').read_text(encoding='utf-8')
    causal = (ROOT/'references/modules/audience-emotion-causality/module.md').read_text(encoding='utf-8')
    assert 'ADAPTER_ONLY' in story
    assert 'PROJECTION_ONLY' in screenplay
    assert 'COMPATIBILITY_PROJECTION_ONLY' in emotion
    assert 'HANDOFF_PROJECTION_ONLY' in causal


def test_embedded_forge_sources_are_archival_not_competing_skill_entries():
    forge = ROOT / 'references' / 'forge'
    for path in forge.glob('source/*/source_skill.md'):
        text = path.read_text(encoding='utf-8')
        assert 'ARCHIVAL_SOURCE_ONLY' in text[:1000]
        assert '非执行入口' in text[:1000]
    assert not (ROOT / 'scripts' / 'render_legacy_afd_emotion_map.py').exists()


def test_formal_emotion_html_is_delivery_analysis_not_story_source():
    text = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
    assert '情绪 HTML 是分析/交付物，不是剧情素材' in text
    assert '不得把情绪图谱、诊断标签、模块名、Renderer UI 或 Skill 品牌自动写进锁定剧本、导演稿、SH/GU/Prompt' in text


def test_downstream_contract_blocks_analysis_artifact_pollution():
    scene = (ROOT/'references/modules/scene-direction/module.md').read_text(encoding='utf-8')
    shot = (ROOT/'references/cineweaver/Shot_Segment_Engine_V1.3/module.md').read_text(encoding='utf-8')
    qc = (ROOT/'references/cineweaver/Final_QC_Engine_V1.3/module.md').read_text(encoding='utf-8')
    assert '非剧情分析边界' in scene
    assert 'Non-diegetic analysis artifacts are not storyboard inputs' in shot
    assert 'ANALYSIS_ARTIFACT_LEAK' in qc
