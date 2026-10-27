#!/usr/bin/env python3
"""Resolve DOCX revision structure into active screenplay text plus an audit map.

This resolver is deliberately project-agnostic. It handles OOXML tracked changes and
strikethrough deterministically. Run colors are reported, not interpreted, unless a
caller supplies an explicit color policy derived from the document's own legend or
from the user.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
Q = lambda name: f"{{{W}}}{name}"


def _truthy_on_off(el: ET.Element | None) -> bool:
    if el is None:
        return False
    val = el.get(Q("val"))
    return val is None or str(val).lower() not in {"0", "false", "off", "none"}


def _run_style(run: ET.Element) -> dict:
    rpr = run.find("w:rPr", NS)
    color = None
    strike = False
    dstrike = False
    if rpr is not None:
        color_el = rpr.find("w:color", NS)
        if color_el is not None:
            color = (color_el.get(Q("val")) or "").upper() or None
        strike = _truthy_on_off(rpr.find("w:strike", NS))
        dstrike = _truthy_on_off(rpr.find("w:dstrike", NS))
    return {"color": color, "strike": strike or dstrike}


def _run_text(run: ET.Element, deleted: bool = False) -> str:
    parts: list[str] = []
    tags = ["delText"] if deleted else ["t"]
    for tag in tags:
        for node in run.findall(f".//w:{tag}", NS):
            parts.append(node.text or "")
    # Some malformed/converted files keep w:t inside w:del; preserve it for audit.
    if deleted and not parts:
        for node in run.findall(".//w:t", NS):
            parts.append(node.text or "")
    for br in run.findall(".//w:br", NS):
        parts.append("\n")
    for tab in run.findall(".//w:tab", NS):
        parts.append("\t")
    return "".join(parts)


def _normalize_policy(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    out = {}
    for key, value in raw.items():
        k = str(key).replace("#", "").upper().strip()
        v = str(value).upper().strip()
        if re.fullmatch(r"[0-9A-F]{6}", k) and v in {"ACTIVE", "EXCLUDED", "HIGH_PRIORITY", "COMMENT"}:
            out[k] = v
    return out


def resolve_docx(input_path: Path, color_policy: dict[str, str] | None = None) -> tuple[str, dict]:
    color_policy = color_policy or {}
    with zipfile.ZipFile(input_path) as zf:
        xml = zf.read("word/document.xml")
        names = set(zf.namelist())
    root = ET.fromstring(xml)

    paragraphs: list[str] = []
    run_records: list[dict] = []
    color_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    comment_refs = 0

    body = root.find("w:body", NS)
    if body is None:
        return "", {"error": "word/document.xml has no w:body"}

    for p_index, para in enumerate(body.findall(".//w:p", NS), start=1):
        active_parts: list[str] = []

        def walk(node: ET.Element, tracked: str | None = None) -> None:
            nonlocal comment_refs
            local_tracked = tracked
            if node.tag == Q("del"):
                local_tracked = "deleted"
            elif node.tag == Q("ins"):
                local_tracked = "inserted"
            if node.tag == Q("commentReference"):
                comment_refs += 1
            if node.tag == Q("r"):
                style = _run_style(node)
                deleted = local_tracked == "deleted"
                text = _run_text(node, deleted=deleted)
                if not text:
                    return
                color = style["color"]
                if color:
                    color_counts[color] += 1
                policy_status = color_policy.get(color or "")
                if deleted:
                    status = "EXCLUDED_TRACKED_DELETE"
                elif style["strike"]:
                    status = "EXCLUDED_STRIKETHROUGH"
                elif policy_status == "EXCLUDED":
                    status = "EXCLUDED_COLOR_POLICY"
                elif policy_status == "HIGH_PRIORITY":
                    status = "ACTIVE_HIGH_PRIORITY"
                elif policy_status == "COMMENT":
                    status = "ACTIVE_COMMENT_STYLE"
                elif local_tracked == "inserted":
                    status = "ACTIVE_TRACKED_INSERT"
                else:
                    status = "ACTIVE"
                status_counts[status] += 1
                run_records.append({
                    "paragraph": p_index,
                    "text": text,
                    "status": status,
                    "color": color,
                    "strike": bool(style["strike"]),
                    "tracked": local_tracked,
                })
                if status.startswith("ACTIVE"):
                    active_parts.append(text)
                return
            for child in list(node):
                walk(child, local_tracked)

        walk(para)
        text = "".join(active_parts).strip()
        if text:
            paragraphs.append(text)

    report = {
        "source": input_path.name,
        "policy": {
            "tracked_deletions": "EXCLUDED",
            "strikethrough": "EXCLUDED",
            "tracked_insertions": "ACTIVE",
            "run_colors": "REPORT_ONLY unless explicit color policy supplied",
            "color_policy": color_policy,
        },
        "counts": {
            "paragraphs_active": len(paragraphs),
            "runs": len(run_records),
            "comment_references": comment_refs,
            "status": dict(status_counts),
            "colors": dict(color_counts),
        },
        "has_comments_part": "word/comments.xml" in names,
        "runs": run_records,
    }
    return "\n\n".join(paragraphs).strip() + "\n", report


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve DOCX tracked revisions/strikethrough before story analysis")
    parser.add_argument("input_docx", type=Path)
    parser.add_argument("output_text", type=Path, help="clean active-text output (.md or .txt)")
    parser.add_argument("--report", type=Path, help="write revision audit JSON")
    parser.add_argument("--color-policy", type=Path, help='optional JSON mapping, e.g. {"FF0000":"EXCLUDED","7030A0":"HIGH_PRIORITY"}')
    args = parser.parse_args()

    policy = {}
    if args.color_policy:
        policy = _normalize_policy(json.loads(args.color_policy.read_text(encoding="utf-8")))
    text, report = resolve_docx(args.input_docx, policy)
    args.output_text.parent.mkdir(parents=True, exist_ok=True)
    args.output_text.write_text(text, encoding="utf-8")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
