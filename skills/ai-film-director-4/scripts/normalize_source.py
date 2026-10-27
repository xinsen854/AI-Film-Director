#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

PLAIN_TEXT_SUFFIXES = {'.md', '.txt', '.json', '.yaml', '.yml', '.csv', '.srt', '.fountain'}


def _decode_bytes(raw: bytes) -> str:
    for encoding in ('utf-8-sig', 'utf-8', 'gb18030', 'big5'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='replace')


def _clean_newlines(text: str) -> str:
    return text.replace('\r\n', '\n').replace('\r', '\n')


def _read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml_bytes = archive.read('word/document.xml')
    root = ET.fromstring(xml_bytes)
    ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    paragraphs: list[str] = []
    for paragraph in root.iter(f'{ns}p'):
        pieces: list[str] = []
        for node in paragraph.iter():
            if node.tag == f'{ns}t' and node.text:
                pieces.append(node.text)
            elif node.tag == f'{ns}tab':
                pieces.append('\t')
            elif node.tag in {f'{ns}br', f'{ns}cr'}:
                pieces.append('\n')
        paragraphs.append(''.join(pieces))
    return '\n'.join(paragraphs).rstrip() + '\n'


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError('读取PDF需要安装 pypdf') from exc
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or '')
    return '\n\n'.join(pages).rstrip() + '\n'


def _read_html(path: Path) -> str:
    source = _decode_bytes(path.read_bytes())
    source = re.sub(r'(?is)<(script|style).*?>.*?</\1>', ' ', source)
    source = re.sub(r'(?i)<br\s*/?>|</p\s*>|</div\s*>|</h[1-6]\s*>', '\n', source)
    source = re.sub(r'(?s)<[^>]+>', ' ', source)
    source = html.unescape(source)
    source = re.sub(r'[ \t]+', ' ', source)
    source = re.sub(r' *\n *', '\n', source)
    return source.strip() + '\n'


def read_source(path: str | Path) -> str:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    suffix = source.suffix.lower()
    if suffix in PLAIN_TEXT_SUFFIXES or not suffix:
        return _clean_newlines(_decode_bytes(source.read_bytes()))
    if suffix == '.docx':
        return _clean_newlines(_read_docx(source))
    if suffix == '.pdf':
        return _clean_newlines(_read_pdf(source))
    if suffix in {'.html', '.htm'}:
        return _clean_newlines(_read_html(source))
    raise ValueError(f'不支持的输入格式: {suffix or "<无扩展名>"}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Normalize a project source into UTF-8 text')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(read_source(args.input), encoding='utf-8')
    print(destination)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
