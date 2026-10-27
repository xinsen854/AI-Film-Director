from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts'


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return subprocess.run(
        [sys.executable, str(SCRIPTS / 'verify_release.py'), *args],
        text=True, capture_output=True, check=False, cwd=str(cwd or ROOT), env=env,
    )


def clone_skill(tmp_path: Path) -> Path:
    target = tmp_path / 'skill'
    shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', '*.pyc'))
    return target


def test_release_gate_exists_and_clean_root_passes(tmp_path: Path):
    root = clone_skill(tmp_path)
    # 复制出来后路径不变，manifest内容仍应合法。
    result = run('--skill-root', str(root), '--skip-regression')
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS: release validation' in result.stdout


def test_release_gate_rejects_cache_artifacts(tmp_path: Path):
    root = clone_skill(tmp_path)
    cache = root / '.pytest_cache'
    cache.mkdir()
    (cache / 'README.md').write_text('cache', encoding='utf-8')
    result = run('--skill-root', str(root), '--skip-regression')
    assert result.returncode != 0
    assert 'forbidden cache artifact' in (result.stdout + result.stderr)


def test_release_gate_rejects_python_syntax_error_even_if_integrity_is_refreshed(tmp_path: Path):
    root = clone_skill(tmp_path)
    broken = root / 'scripts' / 'broken_release_probe.py'
    broken.write_text('def broken(:\n    pass\n', encoding='utf-8')
    subprocess.run(
        [sys.executable, str(root / 'scripts' / 'skill_integrity.py'), 'write', '--skill-root', str(root)],
        check=True, text=True, capture_output=True,
    )
    result = run('--skill-root', str(root), '--skip-regression')
    assert result.returncode != 0
    assert 'python compile failed' in (result.stdout + result.stderr)


def test_release_gate_rejects_integrity_mismatch(tmp_path: Path):
    root = clone_skill(tmp_path)
    skill = root / 'SKILL.md'
    skill.write_text(skill.read_text(encoding='utf-8') + '\nTAMPERED\n', encoding='utf-8')
    result = run('--skill-root', str(root), '--skip-regression')
    assert result.returncode != 0
    assert 'integrity' in (result.stdout + result.stderr).lower()


def test_zip_mode_reextracts_and_validates_package(tmp_path: Path):
    root = clone_skill(tmp_path)
    # root复制过程中会包含本测试，先刷新manifest。
    subprocess.run(
        [sys.executable, str(root / 'scripts' / 'skill_integrity.py'), 'write', '--skill-root', str(root)],
        check=True, text=True, capture_output=True,
    )
    archive = tmp_path / 'release.zip'
    shutil.make_archive(str(archive.with_suffix('')), 'zip', root.parent, root.name)
    result = run('--zip-file', str(archive), '--skip-regression')
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'ZIP_REEXTRACTED' in result.stdout
    assert 'PASS: release validation' in result.stdout


def test_regression_runner_does_not_leave_pytest_bytecode_cache(tmp_path: Path):
    sys.path.insert(0, str(SCRIPTS))
    from verify_release import _run_regression

    root = tmp_path / 'mini'
    tests = root / 'tests'
    tests.mkdir(parents=True)
    (tests / 'test_smoke.py').write_text('def test_smoke():\n    assert 1 + 1 == 2\n', encoding='utf-8')
    problems = _run_regression(root)
    assert problems == []
    leftovers = [
        p for p in root.rglob('*')
        if '__pycache__' in p.parts or '.pytest_cache' in p.parts or (p.is_file() and p.suffix == '.pyc')
    ]
    assert leftovers == []


def test_regression_runner_uses_private_basetemp():
    source = (ROOT / 'scripts' / 'verify_release.py').read_text(encoding='utf-8')
    assert "TemporaryDirectory(prefix='afd_regression_')" in source
    assert "'--basetemp', str(basetemp)" in source


def test_release_gate_does_not_self_pollute_the_validated_skill(tmp_path: Path):
    root = clone_skill(tmp_path)
    subprocess.run(
        [sys.executable, str(root / 'scripts' / 'skill_integrity.py'), 'write', '--skill-root', str(root)],
        check=True, text=True, capture_output=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
    )
    env = os.environ.copy()
    env.pop('PYTHONDONTWRITEBYTECODE', None)
    result = subprocess.run(
        [sys.executable, str(root / 'scripts' / 'verify_release.py'), '--skill-root', str(root), '--skip-regression'],
        text=True, capture_output=True, check=False, cwd=str(root), env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    leftovers = [p for p in root.rglob('*') if '__pycache__' in p.parts or p.suffix == '.pyc']
    assert leftovers == []


def test_integrity_writer_ignores_pytest_cache(tmp_path: Path):
    root = clone_skill(tmp_path)
    cache = root / '.pytest_cache' / 'v' / 'cache'
    cache.mkdir(parents=True)
    (root / '.pytest_cache' / 'README.md').write_text('cache', encoding='utf-8')
    (cache / 'nodeids').write_text('[]', encoding='utf-8')
    subprocess.run(
        [sys.executable, str(root / 'scripts' / 'skill_integrity.py'), 'write', '--skill-root', str(root)],
        check=True, text=True, capture_output=True,
    )
    manifest = (root / 'MANIFEST.sha256').read_text(encoding='utf-8')
    assert '.pytest_cache' not in manifest
