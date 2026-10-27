#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


STATUS_LABELS = {
    'UNCOVERED': '未覆盖',
    'PLANNED': '已规划',
    'PRODUCED': '已生产',
    'CONFIRMED': '已确认',
}
CATEGORY_LABELS = {
    'story_atom': '剧情原子', 'scene': '场景', 'action': '关键动作', 'dialogue': '关键对白',
    'information': '信息揭示', 'reveal': 'Reveal', 'setup': '伏笔', 'payoff': '回收',
}


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ''))


def validate_story_coverage_html_payload(data: object) -> list[str]:
    if not isinstance(data, dict):
        return ['Story Coverage payload must be an object']
    errors: list[str] = []
    if not str(data.get('project_id') or '').strip():
        errors.append('project_id missing')
    items = data.get('items')
    if not isinstance(items, list):
        errors.append('items must be a list')
        return errors
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f'items[{index}] must be an object')
            continue
        for key in ('coverage_id', 'category', 'content', 'status', 'evidence'):
            if key not in item or (key != 'evidence' and not str(item.get(key) or '').strip()):
                errors.append(f'items[{index}].{key} missing')
        coverage_id = str(item.get('coverage_id') or '')
        if coverage_id in seen:
            errors.append(f'duplicate coverage_id {coverage_id}')
        seen.add(coverage_id)
        if item.get('status') not in STATUS_LABELS:
            errors.append(f'items[{index}].status invalid: {item.get("status")}')
        if not isinstance(item.get('evidence'), list):
            errors.append(f'items[{index}].evidence must be a list')
    if not isinstance(data.get('risks', []), list):
        errors.append('risks must be a list')
    return errors


def render_story_coverage_html(data: dict) -> str:
    errors = validate_story_coverage_html_payload(data)
    if errors:
        raise ValueError('Story Coverage HTML validation failed: ' + '; '.join(errors))
    items = data.get('items', [])
    counts = {status: sum(1 for item in items if item.get('status') == status) for status in STATUS_LABELS}
    cards = ''.join(
        f'<div class="metric {status.lower()}"><span>{label}</span><strong>{counts[status]}</strong></div>'
        for status, label in STATUS_LABELS.items()
    )
    rows = ''.join(
        '<tr>'
        f'<td>{_esc(item.get("coverage_id"))}</td>'
        f'<td>{_esc(CATEGORY_LABELS.get(str(item.get("category")), item.get("category")))}</td>'
        f'<td class="content">{_esc(item.get("content"))}</td>'
        f'<td>{_esc(item.get("unit_id") or "—")} / {_esc(item.get("scene_id") or "—")}</td>'
        f'<td><span class="badge {str(item.get("status")).lower()}">{_esc(STATUS_LABELS[str(item.get("status"))])}</span></td>'
        f'<td>{_esc("、".join(str(x) for x in item.get("evidence", [])) or "—")}</td>'
        '</tr>' for item in items
    )
    risks = ''.join(
        f'<li><b>{_esc(item.get("code"))}</b>｜{_esc(item.get("coverage_id"))}｜{_esc(item.get("detail"))}</li>'
        for item in data.get('risks', [])
    ) or '<li class="ok">未发现提前Reveal、漏对白、漏场景或重复核销风险。</li>'
    category_legend = '｜'.join(CATEGORY_LABELS.values())
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(data.get('project_id'))}｜Story Coverage Ledger</title>
<style>
:root{{--bg:#0b1018;--panel:#151e2d;--line:#2e3b52;--text:#ecf2ff;--muted:#9eabc0}}*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(145deg,#09111c,#151b2a);color:var(--text);font-family:"Microsoft YaHei",sans-serif}}main{{max-width:1500px;margin:auto;padding:38px 24px 64px}}h1{{margin:0;font-size:36px}}p{{color:var(--muted)}}.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}}.metric{{padding:16px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}}.metric span{{color:var(--muted)}}.metric strong{{display:block;font-size:28px;margin-top:4px}}.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:16px}}table{{width:100%;border-collapse:collapse;min-width:1050px;background:rgba(19,27,41,.9)}}th,td{{padding:13px 14px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{position:sticky;top:0;background:#202b40;color:#bcd2ff}}td.content{{min-width:280px}}.badge{{padding:4px 9px;border-radius:999px;font-weight:700;font-size:12px}}.uncovered{{color:#ff8893}}.badge.uncovered{{background:#4c2029}}.planned{{color:#f7c765}}.badge.planned{{background:#493b1d}}.produced{{color:#76b4ff}}.badge.produced{{background:#213c61}}.confirmed{{color:#63d6aa}}.badge.confirmed{{background:#19483b}}section{{margin-top:24px;padding:20px;border:1px solid var(--line);border-radius:16px;background:var(--panel)}}li{{margin:8px 0;color:#ffd0d4}}li.ok{{color:#82d8b8}}@media(max-width:800px){{.metrics{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body><main>
<p>PRODUCTION CONTROL</p><h1>Story Coverage Ledger</h1><p>项目：{_esc(data.get('project_id'))}｜跟踪范围：{_esc(category_legend)}。状态按未覆盖 → 已规划 → 已生产 → 已确认推进，防止漏剧情、漏对白、提前Reveal和重复剧情。</p>
<div class="metrics">{cards}</div><div class="table-wrap"><table><thead><tr><th>ID</th><th>类别</th><th>内容</th><th>单元 / 场景</th><th>状态</th><th>证据</th></tr></thead><tbody>{rows}</tbody></table></div>
<section><h2>风险与阻断</h2><ul>{risks}</ul></section>
</main></body></html>'''


def render_story_coverage(project_root: str | Path) -> Path:
    root = Path(project_root).resolve()
    source = root / 'state' / 'STORY_COVERAGE_LEDGER.json'
    if not source.is_file():
        raise FileNotFoundError(f'缺少Story Coverage JSON：{source}')
    data = json.loads(source.read_text(encoding='utf-8'))
    out = root / 'STORY_COVERAGE_LEDGER.html'
    out.write_text(render_story_coverage_html(data), encoding='utf-8')
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description='Render formal Story Coverage Ledger HTML')
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()
    print(render_story_coverage(args.project_root))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
