from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .metrics import Metrics, stable_trace_hash
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
    traces = traces or []
    display_traces = _sorted_traces(traces)
    attempt_payload = _attempt_payload(display_traces)
    hash_payload = _hash_group_payload(metrics, traces)
    js = (
        "window.__evalLogAnalyzer = "
        f"{{attempts: {to_json_script(attempt_payload)}, hashGroups: {to_json_script(hash_payload)}}};\n{BASE_JS}"
    )
    body = "\n".join(
        [
            "<main>",
            "<h1>评测日志分析报告</h1>",
            _render_basic_info(metrics.basic_info),
            _render_core_cards(metrics),
            _render_exception_summary(metrics.exception_summary),
            _render_retry_table(display_traces, metrics, max_attempt_columns),
            _render_compact_response_length_chart(display_traces, metrics),
            _render_response_length_chart(display_traces, metrics),
            _render_hash_repeat_chart(metrics, enable_hash_repeat_chart),
            "</main>",
            _render_modal(),
        ]
    )
    html_text = HTML_TEMPLATE.format(title="评测日志分析报告", css=BASE_CSS, body=body, js=js)
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
    boxplots = export.get("boxplots") or {}
    metric_cards = [
        ("平均 complete tokens", export.get("avg_complete_tokens"), boxplots.get("complete_tokens")),
        ("平均 reasoning tokens", export.get("avg_reasoning_token"), boxplots.get("reasoning_token")),
        ("平均 content tokens", export.get("avg_content_token"), boxplots.get("content_token")),
        ("平均 used_time", export.get("avg_used_time"), boxplots.get("used_time")),
        ("平均 total_used_time", export.get("avg_total_used_time"), boxplots.get("total_used_time")),
    ]
    items = [
        ("retry req_id 数量", trace.get("retry_req_id_count")),
        ("retry 最终成功数量", trace.get("retry_final_success_count")),
        ("最终失败数量", trace.get("final_failed_count")),
        ("empty 数量", export.get("empty_count")),
        ("overlength 数量", export.get("overlength_count")),
        ("timeout 数量", export.get("timeout_attempt_count")),
    ]
    return (
        "<section><h2>核心指标</h2><div class=\"grid\">"
        + "".join(_metric_card(k, v, boxplot) for k, v, boxplot in metric_cards)
        + "".join(_card(k, v) for k, v in items)
        + "</div></section>"
    )


def _render_exception_summary(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{_escape(row['type'])}</td><td>{_escape(row['count'])}</td><td>{_escape(row['description'])}</td></tr>"
        for row in rows
    )
    return (
        "<section><h2>异常摘要</h2><table><thead><tr><th>类型</th><th>数量</th><th>说明</th></tr></thead>"
        f"<tbody>{body}</tbody></table></section>"
    )


def _render_retry_table(traces: list[ReqTrace], metrics: Metrics, max_attempt_columns: int) -> str:
    headers = "".join(f"<th>t{i}</th>" for i in range(1, max_attempt_columns + 1))
    rows = []
    for display_id, trace in enumerate(traces, start=1):
        attempt_cells = []
        for index in range(max_attempt_columns):
            attempt = trace.attempts[index] if index < len(trace.attempts) else None
            if attempt is None:
                attempt_cells.append("<td></td>")
                continue
            symbol = "🟩" if attempt.success else "🟥"
            attempt_cells.append(
                f"<td><button class=\"status-btn\" onclick=\"elaOpenAttempt('{_attempt_id(trace.req_id, attempt.attempt_index)}')\">{symbol}</button></td>"
            )
        if len(trace.attempts) > max_attempt_columns:
            attempt_cells[-1] = f"<td><button onclick=\"elaOpenAttempt('{_attempt_id(trace.req_id, trace.attempts[-1].attempt_index)}')\">更多</button></td>"
        final_symbol = "通过" if trace.final_success else "失败"
        final_class = "final-ok" if trace.final_success else "final-bad"
        final_id = _attempt_id(trace.req_id, trace.final_attempt.attempt_index) if trace.final_attempt else ""
        eval_result = metrics.eval_results.get(trace.req_id)
        eval_text = _eval_text(eval_result)
        eval_class = _status_class(trace, eval_result)
        has_failure = any(not attempt.success for attempt in trace.attempts)
        eval_failed = eval_result is False
        search_text = " ".join([trace.req_id, trace.prompt] + [a.failure_reason for a in trace.attempts]).lower()
        rows.append(
            f"<tr data-retry-row data-has-failure=\"{str(has_failure).lower()}\" "
            f"data-eval-failed=\"{str(eval_failed).lower()}\" data-search=\"{_escape(search_text)}\">"
            f"<td>{display_id}</td><td>{_escape(trace.req_id)}</td>"
            + "".join(attempt_cells)
            + f"<td><button class=\"{final_class}\" onclick=\"elaOpenAttempt('{final_id}')\">{final_symbol}</button></td>"
            + f"<td><span class=\"result-pill {eval_class}\">{eval_text}</span></td></tr>"
        )
    return (
        "<section><h2>重试链路表</h2>"
        "<div class=\"toolbar\"><input id=\"retry-search\" type=\"search\" placeholder=\"搜索 req_id / prompt / 失败原因\" oninput=\"elaFilterRetry()\">"
        "<button id=\"failure-filter\" type=\"button\" onclick=\"elaToggleFailureFilter()\">只看过程失败</button>"
        "<button id=\"eval-failed-filter\" type=\"button\" onclick=\"elaToggleEvalFailedFilter()\">只看做错</button></div>"
        f"<table><thead><tr><th>id</th><th>req_id</th>{headers}<th>最终链路</th><th>评测结果</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>"
    )


def _render_response_length_chart(traces: list[ReqTrace], metrics: Metrics) -> str:
    rows = []
    for display_id, trace in enumerate(traces, start=1):
        width = _fixed_width(trace.final_response_length)
        status = _status_class(trace, metrics.eval_results.get(trace.req_id))
        final_id = _attempt_id(trace.req_id, trace.final_attempt.attempt_index) if trace.final_attempt else ""
        title = f"req_id={trace.req_id} prompt={trace.prompt} 长度={trace.final_response_length} 评测结果={_eval_text(metrics.eval_results.get(trace.req_id))}"
        rows.append(
            f"<div class=\"length-row\" title=\"{_escape(title)}\" onclick=\"elaOpenAttempt('{final_id}')\">"
            f"<div>{display_id}</div><div class=\"bar-track\"><div class=\"bar {status}\" style=\"width:{width}%\"></div></div>"
            f"<div class=\"length-value\">{trace.final_response_length}</div></div>"
        )
    return f"<section><h2>response 长度分布图</h2>{''.join(rows)}</section>"


def _render_compact_response_length_chart(traces: list[ReqTrace], metrics: Metrics) -> str:
    lines = []
    for display_id, trace in enumerate(traces, start=1):
        width = _fixed_width(trace.final_response_length)
        status = _status_class(trace, metrics.eval_results.get(trace.req_id))
        final_id = _attempt_id(trace.req_id, trace.final_attempt.attempt_index) if trace.final_attempt else ""
        title = f"id={display_id} req_id={trace.req_id} 长度={trace.final_response_length} 评测结果={_eval_text(metrics.eval_results.get(trace.req_id))}"
        lines.append(
            f"<div class=\"compact-length-line {status}\" title=\"{_escape(title)}\" "
            f"style=\"width:{width}%\" onclick=\"elaOpenAttempt('{final_id}')\"></div>"
        )
    return f"<section><h2>response 长度紧凑分布图</h2><div class=\"compact-length-chart\">{''.join(lines)}</div></section>"


def _render_hash_repeat_chart(metrics: Metrics, enabled: bool) -> str:
    if not enabled:
        return ""
    groups = metrics.hash_repeat_groups
    rows = []
    compact_lines = []
    for group in groups:
        width = _fixed_width(float(group["avg_response_length"]))
        status = "ok" if group["correct_count"] > 0 else "bad"
        title = f"hash_id={group['hash_id']} 平均长度={group['avg_response_length']} 正确={group['correct_count']}/{group['total_count']}"
        rows.append(
            f"<div class=\"length-row\" title=\"{_escape(title)}\" onclick=\"elaOpenHash('{group['id']}')\">"
            f"<div>{group['id']}</div><div class=\"bar-track\"><div class=\"bar {status}\" style=\"width:{width}%\"></div></div>"
            f"<div class=\"length-value\">{_escape(group['avg_response_length'])} {group['correct_count']}/{group['total_count']}</div></div>"
        )
        compact_lines.append(
            f"<div class=\"compact-length-line {status}\" title=\"{_escape(title)}\" "
            f"style=\"width:{width}%\" onclick=\"elaOpenHash('{group['id']}')\"></div>"
        )
    return (
        f"<section><h2>hash_id 重复评测聚合紧凑分布图</h2><div class=\"compact-length-chart\">{''.join(compact_lines)}</div></section>"
        f"<section><h2>hash_id 重复评测聚合图</h2>{''.join(rows)}</section>"
    )


def _render_modal() -> str:
    return """
<div id="json-modal" class="modal-backdrop" onclick="if(event.target===this) elaCloseModal()">
  <div class="modal">
    <div class="modal-head">
      <div>
        <div id="modal-title" class="value"></div>
        <div id="modal-meta" class="muted"></div>
        <div id="modal-failure" class="failure"></div>
      </div>
      <button onclick="elaCloseModal()">关闭</button>
    </div>
    <div class="modal-body">
      <div class="modal-actions">
        <button onclick="elaCopyJson()">复制 JSON</button>
        <button onclick="elaShowFull()">显示完整 JSON</button>
      </div>
      <pre id="modal-json"></pre>
    </div>
  </div>
</div>
"""


def _card(label: str, value: Any) -> str:
    display = "-" if value is None or value == "" else value
    return f"<div class=\"card\"><div class=\"label\">{_escape(label)}</div><div class=\"value\">{_escape(display)}</div></div>"


def _metric_card(label: str, value: Any, boxplot: dict[str, Any] | None) -> str:
    if not boxplot:
        return _card(label, value)
    chart = _boxplot_html(boxplot)
    return (
        f"<div class=\"card metric-card\"><div class=\"label\">{_escape(label)}</div>"
        f"<div class=\"value\">{_escape(value)}</div>{chart}</div>"
    )


def _boxplot_html(boxplot: dict[str, Any]) -> str:
    maximum = float(boxplot.get("max") or 0)
    if maximum <= 0:
        maximum = 1
    min_pos = _box_percent(boxplot.get("min"), maximum)
    q1_pos = _box_percent(boxplot.get("q1"), maximum)
    median_pos = _box_percent(boxplot.get("median"), maximum)
    q3_pos = _box_percent(boxplot.get("q3"), maximum)
    max_pos = _box_percent(boxplot.get("max"), maximum)
    box_bottom = min(q1_pos, q3_pos)
    box_height = max(1, abs(q3_pos - q1_pos))
    whisker_bottom = min(min_pos, max_pos)
    whisker_height = max(1, abs(max_pos - min_pos))
    title = (
        f"count={boxplot.get('count')} min={boxplot.get('min')} q1={boxplot.get('q1')} "
        f"median={boxplot.get('median')} q3={boxplot.get('q3')} max={boxplot.get('max')}"
    )
    return (
        f"<div class=\"boxplot\" title=\"{_escape(title)}\">"
        f"<span class=\"whisker\" style=\"bottom:{whisker_bottom}%;height:{whisker_height}%\"></span>"
        f"<span class=\"cap min\" style=\"bottom:{min_pos}%\"></span>"
        f"<span class=\"cap max\" style=\"bottom:{max_pos}%\"></span>"
        f"<span class=\"box\" style=\"bottom:{box_bottom}%;height:{box_height}%\"></span>"
        f"<span class=\"quartile q1\" style=\"bottom:{q1_pos}%\"></span>"
        f"<span class=\"quartile q3\" style=\"bottom:{q3_pos}%\"></span>"
        f"<span class=\"median\" style=\"bottom:{median_pos}%\"></span></div>"
        f"<div class=\"boxplot-meta\">p25 {boxplot.get('q1')} · p50 {boxplot.get('median')} · p75 {boxplot.get('q3')}</div>"
    )


def _box_percent(value: Any, maximum: float) -> int:
    try:
        return max(0, min(100, round(float(value) / maximum * 100)))
    except (TypeError, ValueError):
        return 0


def _percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _sorted_traces(traces: list[ReqTrace]) -> list[ReqTrace]:
    return sorted(traces, key=lambda trace: (stable_trace_hash(trace), trace.req_id))


def _fixed_width(length: int | float) -> int:
    try:
        value = float(length)
    except (TypeError, ValueError):
        value = 0
    if value <= 0:
        return 0
    return max(1, min(100, round(value / 120000 * 100)))


def _eval_text(value: bool | None) -> str:
    if value is True:
        return "做对"
    if value is False:
        return "做错"
    return "-"


def _status_class(trace: ReqTrace, eval_result: bool | None) -> str:
    if eval_result is True:
        return "ok"
    if eval_result is False and not trace.final_success:
        return "warn"
    if eval_result is False:
        return "bad"
    return "ok" if trace.final_success else "bad"


def to_json_script(value: Any) -> str:
    """生成可安全嵌入 script 的 JSON 字符串。"""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def _attempt_payload(traces: list[ReqTrace]) -> dict[str, Any]:
    payload = {}
    for trace in traces:
        for attempt in trace.attempts:
            payload[_attempt_id(trace.req_id, attempt.attempt_index)] = {
                "req_id": attempt.req_id,
                "attempt_index": attempt.attempt_index,
                "success": attempt.success,
                "failure_reason": attempt.failure_reason,
                "response_length": attempt.response_length,
                "used_time": attempt.used_time,
                "request_json": attempt.request_json,
                "response_json": attempt.response_json,
            }
    return payload


def _hash_group_payload(metrics: Metrics, traces: list[ReqTrace]) -> dict[str, Any]:
    trace_by_req = {trace.req_id: trace for trace in traces}
    payload: dict[str, Any] = {}
    for group in metrics.hash_repeat_groups:
        items = []
        for req_id in group["req_ids"]:
            trace = trace_by_req.get(req_id)
            final_attempt = trace.final_attempt if trace else None
            items.append(
                {
                    "req_id": req_id,
                    "final_success": trace.final_success if trace else False,
                    "response_length": trace.final_response_length if trace else 0,
                    "request_json": final_attempt.request_json if final_attempt else None,
                    "response_json": final_attempt.response_json if final_attempt else None,
                }
            )
        payload[str(group["id"])] = {**group, "items": items}
    return payload


def _attempt_id(req_id: str, attempt_index: int) -> str:
    return f"{req_id}::{attempt_index}"
