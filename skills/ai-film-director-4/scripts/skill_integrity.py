#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

MANIFEST_NAME = 'MANIFEST.sha256'


def _excluded(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if rel.as_posix() == MANIFEST_NAME:
        return True
    if any(part in {'.git', '__pycache__', '.pytest_cache'} for part in rel.parts):
        return True
    if path.name == '.DS_Store' or path.suffix == '.pyc':
        return True
    return False


def _runtime_files(root: Path) -> list[Path]:
    root = root.resolve()
    return sorted(
        (p for p in root.rglob('*') if p.is_file() and not _excluded(p, root)),
        key=lambda p: p.relative_to(root).as_posix(),
    )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(skill_root: str | Path) -> Path:
    root = Path(skill_root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f'skill root not found: {root}')
    lines = [f'{_sha256(path)}  {path.relative_to(root).as_posix()}' for path in _runtime_files(root)]
    target = root / MANIFEST_NAME
    target.write_text('\n'.join(lines) + ('\n' if lines else ''), encoding='utf-8')
    return target


def _read_manifest(path: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if '  ' not in line:
            raise ValueError(f'invalid manifest line {lineno}: {raw}')
        digest, rel = line.split('  ', 1)
        digest, rel = digest.strip(), rel.strip()
        if len(digest) != 64 or any(ch not in '0123456789abcdefABCDEF' for ch in digest):
            raise ValueError(f'invalid sha256 at line {lineno}: {digest}')
        if not rel or rel in records:
            raise ValueError(f'invalid/duplicate path at line {lineno}: {rel}')
        records[rel] = digest.lower()
    return records


def verify_manifest(skill_root: str | Path) -> tuple[bool, list[str]]:
    root = Path(skill_root).resolve()
    manifest = root / MANIFEST_NAME
    if not manifest.is_file():
        return False, [f'missing {MANIFEST_NAME}']
    try:
        expected = _read_manifest(manifest)
    except (OSError, ValueError) as exc:
        return False, [str(exc)]

    actual_paths = {p.relative_to(root).as_posix(): p for p in _runtime_files(root)}
    problems: list[str] = []
    for rel in sorted(expected.keys() - actual_paths.keys()):
        problems.append(f'missing file: {rel}')
    for rel in sorted(actual_paths.keys() - expected.keys()):
        problems.append(f'untracked extra file: {rel}')
    for rel in sorted(expected.keys() & actual_paths.keys()):
        actual = _sha256(actual_paths[rel])
        if actual != expected[rel]:
            problems.append(f'hash mismatch: {rel}')
    return not problems, problems


def main() -> int:
    parser = argparse.ArgumentParser(description='Write or verify AI Film Director Skill SHA256 integrity manifest')
    parser.add_argument('action', choices=['write', 'verify'])
    parser.add_argument('--skill-root', default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    if args.action == 'write':
        target = write_manifest(args.skill_root)
        print(f'WROTE {target}')
        return 0
    ok, problems = verify_manifest(args.skill_root)
    if ok:
        print('PASS: Skill integrity verified')
        return 0
    print('FAIL: Skill integrity mismatch')
    for item in problems:
        print('-', item)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
