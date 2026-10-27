#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import os
import py_compile
import subprocess
import sys
import tempfile
import zipfile
from hashlib import sha256
from pathlib import Path

# The release gate must not create the cache artifacts it is designed to
# reject. This must be set before importing local validation modules.
sys.dont_write_bytecode = True

from validate_skill_package import validate_skill_root
from verify_master_fusion import validate_master_fusion

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DIRS = {'__pycache__', '.pytest_cache'}
REGRESSION_DEPENDENCIES = {'pytest': 'pytest', 'PIL': 'Pillow'}


def _forbidden_artifacts(root: Path) -> list[str]:
    problems: list[str] = []
    for path in root.rglob('*'):
        rel = path.relative_to(root)
        if any(part in FORBIDDEN_DIRS for part in rel.parts):
            problems.append(f'forbidden cache artifact: {rel.as_posix()}')
        elif path.is_file() and path.suffix == '.pyc':
            problems.append(f'forbidden cache artifact: {rel.as_posix()}')
    return sorted(set(problems))


def _compile_python(root: Path) -> list[str]:
    problems: list[str] = []
    sources = sorted(
        [p for p in (root / 'scripts').rglob('*.py') if p.is_file()]
        + [p for p in (root / 'tests').rglob('*.py') if p.is_file()]
    )
    with tempfile.TemporaryDirectory(prefix='afd_compile_') as tmp:
        tmp_root = Path(tmp)
        for source in sources:
            rel = source.relative_to(root).as_posix()
            cfile = tmp_root / f'{sha256(rel.encode("utf-8")).hexdigest()}.pyc'
            try:
                py_compile.compile(str(source), cfile=str(cfile), doraise=True)
            except py_compile.PyCompileError as exc:
                problems.append(f'python compile failed: {rel}: {exc.msg}')
    return problems


def _run_regression(root: Path) -> list[str]:
    tests = root / 'tests'
    if not tests.is_dir():
        return ['regression suite missing: tests/']
    missing = [package for module, package in REGRESSION_DEPENDENCIES.items() if importlib.util.find_spec(module) is None]
    if missing:
        return [
            'regression dependencies missing: ' + ', '.join(missing)
            + '; install with: python -m pip install -r requirements-test.txt'
        ]
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    # Always give pytest a private base directory. On Windows an old or
    # permission-broken ``pytest-of-<user>`` directory can otherwise make an
    # otherwise clean release fail before a single test runs.
    with tempfile.TemporaryDirectory(prefix='afd_regression_') as tmp:
        basetemp = Path(tmp) / 'pytest'
        result = subprocess.run(
            [
                sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
                '--basetemp', str(basetemp), str(tests),
            ],
            cwd=str(root), env=env, text=True, capture_output=True, check=False,
        )
    if result.returncode == 0:
        tail = result.stdout.strip().splitlines()
        summary = tail[-1] if tail else 'pytest passed'
        print(f'REGRESSION: {summary}')
        return []
    output = '\n'.join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    return [f'regression suite failed:\n{output}']


def validate_release_root(root: str | Path, *, run_regression: bool = True) -> list[str]:
    root = Path(root).resolve()
    if not root.is_dir():
        return [f'skill root not found: {root}']

    problems = _forbidden_artifacts(root)
    if problems:
        return problems

    package_errors = validate_skill_root(root, verify_integrity=True)
    if package_errors:
        problems.extend(f'package/integrity: {item}' for item in package_errors)
        return problems

    fusion_errors = validate_master_fusion(root, smoke_render=True)
    if fusion_errors:
        problems.extend(f'master-fusion: {item}' for item in fusion_errors)
        return problems

    compile_errors = _compile_python(root)
    if compile_errors:
        problems.extend(compile_errors)
        return problems

    if run_regression:
        problems.extend(_run_regression(root))
    return problems


def _safe_extract_zip(zip_path: Path, destination: Path) -> Path:
    with zipfile.ZipFile(zip_path, 'r') as zf:
        base = destination.resolve()
        for member in zf.infolist():
            target = (destination / member.filename).resolve()
            try:
                target.relative_to(base)
            except ValueError as exc:
                raise ValueError(f'unsafe zip path: {member.filename}') from exc
        zf.extractall(destination)

    skill_files = list(destination.rglob('SKILL.md'))
    if len(skill_files) != 1:
        raise ValueError(f'expected exactly one SKILL.md after re-extract, found {len(skill_files)}')
    return skill_files[0].parent


def main() -> int:
    parser = argparse.ArgumentParser(description='Final release gate for AI Film Director 4.7.1 Fusion')
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--skill-root', default=None)
    source.add_argument('--zip-file', default=None)
    parser.add_argument('--skip-regression', action='store_true', help='Use only for focused release-gate tests')
    args = parser.parse_args()

    if args.zip_file:
        zip_path = Path(args.zip_file).resolve()
        if not zip_path.is_file():
            print(f'FAIL: zip not found: {zip_path}')
            return 1
        try:
            with tempfile.TemporaryDirectory(prefix='afd_release_zip_') as tmp:
                root = _safe_extract_zip(zip_path, Path(tmp))
                print(f'ZIP_REEXTRACTED: {zip_path.name}')
                problems = validate_release_root(root, run_regression=not args.skip_regression)
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            print(f'FAIL: {exc}')
            return 1
    else:
        root = Path(args.skill_root).resolve() if args.skill_root else DEFAULT_ROOT
        problems = validate_release_root(root, run_regression=not args.skip_regression)

    if problems:
        print('FAIL: release validation')
        for problem in problems:
            print('-', problem)
        return 1
    print('PASS: release validation')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
