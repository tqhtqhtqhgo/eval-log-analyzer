from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .metrics import Metrics
from .parser import ReqTrace
from .static_template import BASE_CSS, BASE_JS, HTML_TEMPLATE


def render_html(
    output_html: str,
    metrics: Metrics,
    traces: list[ReqTrace] | None = None,
    enable_hash_repeat_chart: bool = False,
    max_attempt_columns: int = 5,
) -> str:
    """渲染单文件静态 HTML。"""
    del traces, enable_hash_repeat_chart, max_attempt_columns
    body = "\n".join(
        [
            "<main>",
            "<h1>评测日志分析报告</h1>",
            _render_basic_info(metrics.basic_info),
            _render_core_cards(metrics),
            _render_exception_summary(metrics.exception_summary),
            "</main>",
        ]
    )
    html_text = HTML_TEMPLATE.format(title="评测日志分析报告", css=BASE_CSS, body=body, js=BASE_JS)
    Path(output_html).write_text(html_text, encoding="utf-8")
    return output_html


def _render_basic_info(info: dict[str, Any]) -> str:
    items = [
        ("评测模型", info.get("model")),
        ("用例集", info.get("dataset")),
        ("创建时间", info.get("created_time")),
        ("总题数", info.get("total")),
        ("通过题数", info.get("passed")),
        ("通过率", _percent(info.get("pass_rate"))),
        ("裁判模型", info.get("judge_model")),
        ("log 文件名", info.get("log_name")),
        ("zip 文件名", info.get("zip_name")),
    ]
    return "<section><h2>基础信息</h2><div class=\"grid\">" + "".join(_card(k, v) for k, v in items) + "</div></section>"


def _render_core_cards(metrics: Metrics) -> str:
    export = metrics.export_summary
    trace = metrics.trace_summary
    items = [
        ("平均 complete tokens", export.get("avg_complete_tokens")),
        ("平均 reasoning tokens", export.get("avg_reasoning_token")),
        ("平均 content tokens", export.get("avg_content_token")),
        ("平均 used_time", export.get("avg_used_time")),
        ("平均 total_used_time", export.get("avg_total_used_time")),
        ("retry req_id 数量", trace.get("retry_req_id_count")),
        ("retry 最终成功数量", trace.get("retry_final_success_count")),
        ("最终失败数量", trace.get("final_failed_count")),
        ("empty 数量", export.get("empty_count")),
        ("overlength 数量", export.get("overlength_count")),
        ("timeout 数量", export.get("timeout_attempt_count")),
    ]
    return "<section><h2>核心指标</h2><div class=\"grid\">" + "".join(_card(k, v) for k, v in items) + "</div></section>"


def _render_exception_summary(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{_escape(row['type'])}</td><td>{_escape(row['count'])}</td><td>{_escape(row['description'])}</td></tr>"
        for row in rows
    )
    return (
        "<section><h2>异常摘要</h2><table><thead><tr><th>类型</th><th>数量</th><th>说明</th></tr></thead>"
        f"<tbody>{body}</tbody></table></section>"
    )


def _card(label: str, value: Any) -> str:
    display = "-" if value is None or value == "" else value
    return f"<div class=\"card\"><div class=\"label\">{_escape(label)}</div><div class=\"value\">{_escape(display)}</div></div>"


def _percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def to_json_script(value: Any) -> str:
    """生成可安全嵌入 script 的 JSON 字符串。"""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")
