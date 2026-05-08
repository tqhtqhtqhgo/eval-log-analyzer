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
    js = (
        "window.__evalLogAnalyzer = "
        f"{{attempts: {to_json_script(attempt_payload)}, hashGroups: {{}}}};\n{BASE_JS}"
    )
    body = "\n".join(
        [
            "<main>",
            "<h1>评测日志分析报告</h1>",
            _render_basic_info(metrics.basic_info),
            _render_core_cards(metrics),
            _render_retry_pie_chart(display_traces, metrics),
            _render_exception_summary(metrics.exception_summary),
            _render_response_beeswarm_chart(display_traces, metrics),
            _render_retry_table(display_traces, metrics, max_attempt_columns),
            "</main>",
            _render_modal(),
        ]
    )
    html_text = HTML_TEMPLATE.format(title="评测日志分析报告", css=BASE_CSS, body=body, js=js)
    Path(output_html).write_text(html_text, encoding="utf-8")
    return output_html


def render_compare_html(
    output_html: str,
    left_metrics: Metrics,
    left_traces: list[ReqTrace],
    right_metrics: Metrics,
    right_traces: list[ReqTrace],
    left_label: str,
    right_label: str,
    max_attempt_columns: int = 5,
) -> str:
    """渲染两个评测日志的双列对比 HTML。"""
    left_display_traces = _sorted_traces(left_traces)
    right_display_traces = _sorted_traces(right_traces)
    attempt_payload = {
        **_attempt_payload(left_display_traces, "left::"),
        **_attempt_payload(right_display_traces, "right::"),
    }
    js = (
        "window.__evalLogAnalyzer = "
        f"{{attempts: {to_json_script(attempt_payload)}, hashGroups: {{}}}};\n{BASE_JS}"
    )
    body = "\n".join(
        [
            "<main class=\"compare-main\">",
            "<h1>评测日志对比报告</h1>",
            f"<section><h2>对比文件</h2><div class=\"compare-file-row\">{_compare_file_card('文件 1', left_label)}{_compare_file_card('文件 2', right_label)}</div></section>",
            _render_compare_core_boxplots(left_metrics, right_metrics, left_label, right_label),
            "<div class=\"compare-section-stack\">",
            _render_compare_section_row(
                "基础信息",
                left_label,
                right_label,
                _render_basic_info_content(left_metrics.basic_info),
                _render_basic_info_content(right_metrics.basic_info),
            ),
            _render_compare_section_row(
                "核心指标",
                left_label,
                right_label,
                _render_core_cards_content(left_metrics),
                _render_core_cards_content(right_metrics),
            ),
            _render_compare_section_row(
                "重试推理最终状态圆环图",
                left_label,
                right_label,
                _render_retry_pie_chart_content(left_display_traces, left_metrics),
                _render_retry_pie_chart_content(right_display_traces, right_metrics),
            ),
            _render_compare_section_row(
                "异常摘要",
                left_label,
                right_label,
                _render_exception_summary_content(left_metrics.exception_summary),
                _render_exception_summary_content(right_metrics.exception_summary),
            ),
            _render_compare_section_row(
                "response 长度点阵图",
                left_label,
                right_label,
                _render_response_beeswarm_chart_content(left_display_traces, left_metrics, "left::"),
                _render_response_beeswarm_chart_content(right_display_traces, right_metrics, "right::"),
            ),
            _render_compare_section_row(
                "重试推理表",
                left_label,
                right_label,
                _render_retry_table_content(left_display_traces, left_metrics, max_attempt_columns, "left-", "left::"),
                _render_retry_table_content(right_display_traces, right_metrics, max_attempt_columns, "right-", "right::"),
            ),
            "</div>",
            "</main>",
            _render_modal(),
        ]
    )
    html_text = HTML_TEMPLATE.format(title="评测日志对比报告", css=BASE_CSS, body=body, js=js)
    Path(output_html).write_text(html_text, encoding="utf-8")
    return output_html


def _render_basic_info(info: dict[str, Any]) -> str:
    return f"<section><h2>基础信息</h2>{_render_basic_info_content(info)}</section>"


def _render_basic_info_content(info: dict[str, Any]) -> str:
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
    return "<div class=\"grid\">" + "".join(_card(k, v) for k, v in items) + "</div>"


def _compare_file_card(label: str, value: str) -> str:
    return f"<div class=\"compare-file-card\"><div class=\"label\">{_escape(label)}</div><div class=\"value\">{_escape(value)}</div></div>"


def _render_compare_section_row(
    section_title: str,
    left_label: str,
    right_label: str,
    left_content: str,
    right_content: str,
) -> str:
    return (
        f"<section class=\"compare-section-row\"><h2>{_escape(section_title)}</h2>"
        "<div class=\"compare-section-grid\">"
        f"<article class=\"compare-panel\"><h3>{_escape(left_label)}</h3>{left_content}</article>"
        f"<article class=\"compare-panel\"><h3>{_escape(right_label)}</h3>{right_content}</article>"
        "</div></section>"
    )


def _render_core_cards_without_boxplots(metrics: Metrics) -> str:
    return f"<section><h2>核心指标</h2>{_render_core_cards_content(metrics)}</section>"


def _render_core_cards_content(metrics: Metrics) -> str:
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
        ("最终推理失败数量", trace.get("final_failed_count")),
        ("推理成功题目数量（不含推理失败）", trace.get("final_success_count")),
    ]
    return "<div class=\"grid\">" + "".join(_card(k, v) for k, v in items) + "</div>"


def _render_core_cards(metrics: Metrics) -> str:
    export = metrics.export_summary
    trace = metrics.trace_summary
    boxplots = export.get("boxplots") or {}
    items = [
        ("平均 complete tokens", export.get("avg_complete_tokens")),
        ("平均 reasoning tokens", export.get("avg_reasoning_token")),
        ("平均 content tokens", export.get("avg_content_token")),
        ("平均 used_time", export.get("avg_used_time")),
        ("平均 total_used_time", export.get("avg_total_used_time")),
        ("retry req_id 数量", trace.get("retry_req_id_count")),
        ("retry 最终成功数量", trace.get("retry_final_success_count")),
        ("最终推理失败数量", trace.get("final_failed_count")),
        ("推理成功题目数量（不含推理失败）", trace.get("final_success_count")),
    ]
    return (
        "<section><h2>核心指标</h2><div class=\"grid\">"
        + "".join(_card(k, v) for k, v in items)
        + "</div>"
        + _render_core_boxplots(boxplots)
        + "</section>"
    )


def _render_core_boxplots(boxplots: dict[str, Any]) -> str:
    all_items = [
        ("complete tokens", boxplots.get("complete_tokens")),
        ("reasoning tokens", boxplots.get("reasoning_token")),
        ("content tokens", boxplots.get("content_token")),
        ("used_time", boxplots.get("used_time")),
        ("total_used_time", boxplots.get("total_used_time")),
    ]
    nonzero_items = [
        ("complete tokens 非零", boxplots.get("complete_tokens_nonzero")),
        ("reasoning tokens 非零", boxplots.get("reasoning_token_nonzero")),
        ("content tokens 非零", boxplots.get("content_token_nonzero")),
    ]
    all_charts = _boxplot_row("全部数据", all_items)
    nonzero_charts = _boxplot_row("tokens推理成功数据", nonzero_items)
    if not all_charts and not nonzero_charts:
        return ""
    return f"<h3>核心指标箱线图</h3>{all_charts}{nonzero_charts}"


def _render_compare_core_boxplots(
    left_metrics: Metrics,
    right_metrics: Metrics,
    left_label: str,
    right_label: str,
) -> str:
    left_boxplots = left_metrics.export_summary.get("boxplots") or {}
    right_boxplots = right_metrics.export_summary.get("boxplots") or {}
    all_items = [
        ("complete tokens", "complete_tokens"),
        ("reasoning tokens", "reasoning_token"),
        ("content tokens", "content_token"),
        ("used_time", "used_time"),
        ("total_used_time", "total_used_time"),
    ]
    nonzero_items = [
        ("complete tokens 非零", "complete_tokens_nonzero"),
        ("reasoning tokens 非零", "reasoning_token_nonzero"),
        ("content tokens 非零", "content_token_nonzero"),
    ]
    all_rows = _compare_boxplot_rows("全部数据", all_items, left_boxplots, right_boxplots, left_label, right_label)
    nonzero_rows = _compare_boxplot_rows(
        "tokens推理成功数据",
        nonzero_items,
        left_boxplots,
        right_boxplots,
        left_label,
        right_label,
    )
    if not all_rows and not nonzero_rows:
        return ""
    return f"<section><h2>核心指标箱线图对比</h2>{all_rows}{nonzero_rows}</section>"


def _compare_boxplot_rows(
    title: str,
    items: list[tuple[str, str]],
    left_boxplots: dict[str, Any],
    right_boxplots: dict[str, Any],
    left_label: str,
    right_label: str,
) -> str:
    rows = []
    for metric_label, key in items:
        left_boxplot = left_boxplots.get(key)
        right_boxplot = right_boxplots.get(key)
        if not left_boxplot and not right_boxplot:
            continue
        left_card = _boxplot_card(f"{left_label} · {metric_label}", left_boxplot) if left_boxplot else _empty_boxplot_card(left_label)
        right_card = _boxplot_card(f"{right_label} · {metric_label}", right_boxplot) if right_boxplot else _empty_boxplot_card(right_label)
        rows.append(
            f"<div class=\"compare-boxplot-row\"><div class=\"compare-metric-label\">{_escape(metric_label)}</div>"
            f"<div class=\"compare-boxplot-pair\">{left_card}{right_card}</div></div>"
        )
    if not rows:
        return ""
    return f"<div class=\"boxplot-row-title\">{_escape(title)}</div>{''.join(rows)}"


def _empty_boxplot_card(label: str) -> str:
    return f"<div class=\"boxplot-card empty\"><div class=\"label\">{_escape(label)}</div><div class=\"muted\">无数据</div></div>"


def _boxplot_row(title: str, items: list[tuple[str, Any]]) -> str:
    charts = "".join(_boxplot_card(label, boxplot) for label, boxplot in items if boxplot)
    if not charts:
        return ""
    return f"<div class=\"boxplot-row-title\">{_escape(title)}</div><div class=\"boxplot-grid\">{charts}</div>"


def _render_retry_pie_chart(traces: list[ReqTrace], metrics: Metrics) -> str:
    content = _render_retry_pie_chart_content(traces, metrics)
    if not content:
        return ""
    return f"<section><h2>重试推理最终状态圆环图</h2>{content}</section>"


def _render_retry_pie_chart_content(traces: list[ReqTrace], metrics: Metrics) -> str:
    pass_correct, pass_wrong, failed = _retry_pie_counts(traces, metrics)
    total = pass_correct + pass_wrong + failed
    if total <= 0:
        return ""
    pass_correct_deg = round(pass_correct / total * 360, 2)
    pass_wrong_deg = round(pass_wrong / total * 360, 2)
    style = (
        "background:conic-gradient("
        f"var(--ok) 0deg {pass_correct_deg}deg,"
        f"var(--warn) {pass_correct_deg}deg {pass_correct_deg + pass_wrong_deg}deg,"
        f"var(--infer-fail) {pass_correct_deg + pass_wrong_deg}deg 360deg)"
    )
    legend = [
        ("ok", "推理通过且做对", pass_correct),
        ("warn", "推理通过但做错", pass_wrong),
        ("infer-fail", "推理失败", failed),
    ]
    legend_html = "".join(
        f"<div class=\"pie-legend-item\"><span class=\"legend-dot {klass}\"></span>{label}<b>{count}</b></div>"
        for klass, label, count in legend
    )
    return (
        "<div class=\"pie-wrap\">"
        f"<div class=\"pie-chart\" style=\"{style}\" title=\"总数={total} 推理通过且做对={pass_correct} 推理通过但做错={pass_wrong} 推理失败={failed}\"></div>"
        f"<div class=\"pie-legend\">{legend_html}</div>"
        "</div>"
    )


def _retry_pie_counts(traces: list[ReqTrace], metrics: Metrics) -> tuple[int, int, int]:
    pass_correct = 0
    pass_wrong = 0
    failed = 0
    for trace in traces:
        if not trace.final_success:
            failed += 1
        elif metrics.eval_results.get(trace.req_id) is True:
            pass_correct += 1
        else:
            # 圆环图只按 export_data_list.json 的 eval_result 判定做对/做错。
            pass_wrong += 1
    return pass_correct, pass_wrong, failed


def _render_exception_summary(rows: list[dict[str, Any]]) -> str:
    return f"<section><h2>异常摘要</h2>{_render_exception_summary_content(rows)}</section>"


def _render_exception_summary_content(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{_escape(row['type'])}</td><td>{_escape(row['count'])}</td><td>{_escape(row['description'])}</td></tr>"
        for row in rows
    )
    return (
        "<table><thead><tr><th>类型</th><th>数量</th><th>说明</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def _render_retry_table(
    traces: list[ReqTrace],
    metrics: Metrics,
    max_attempt_columns: int,
    dom_prefix: str = "",
    attempt_prefix: str = "",
) -> str:
    return (
        "<section><h2>重试推理表</h2>"
        f"{_render_retry_table_content(traces, metrics, max_attempt_columns, dom_prefix, attempt_prefix)}"
        "</section>"
    )


def _render_retry_table_content(
    traces: list[ReqTrace],
    metrics: Metrics,
    max_attempt_columns: int,
    dom_prefix: str = "",
    attempt_prefix: str = "",
) -> str:
    headers = "".join(f"<th>t{i}</th>" for i in range(1, max_attempt_columns + 1))
    rows = []
    for display_id, trace in enumerate(traces, start=1):
        attempt_cells = []
        for index in range(max_attempt_columns):
            attempt = trace.attempts[index] if index < len(trace.attempts) else None
            if attempt is None:
                attempt_cells.append("<td></td>")
                continue
            status_class = "ok" if attempt.success else "bad"
            label = "推理成功" if attempt.success else "推理失败"
            attempt_cells.append(
                f"<td><button class=\"status-btn\" title=\"{label}\" aria-label=\"{label}\" "
                f"onclick=\"elaOpenAttempt('{_attempt_id(trace.req_id, attempt.attempt_index, attempt_prefix)}')\">"
                f"<span class=\"status-square {status_class}\"></span></button></td>"
            )
        if len(trace.attempts) > max_attempt_columns:
            attempt_cells[-1] = f"<td><button onclick=\"elaOpenAttempt('{_attempt_id(trace.req_id, trace.attempts[-1].attempt_index, attempt_prefix)}')\">更多</button></td>"
        final_symbol = "推理通过" if trace.final_success else "推理失败"
        final_class = "final-ok" if trace.final_success else "final-bad"
        final_id = _attempt_id(trace.req_id, trace.final_attempt.attempt_index, attempt_prefix) if trace.final_attempt else ""
        eval_result = metrics.eval_results.get(trace.req_id)
        eval_text = _eval_text(eval_result)
        eval_class = _status_class(trace, eval_result)
        has_failure = any(not attempt.success for attempt in trace.attempts)
        eval_failed = eval_result is False
        final_success = trace.final_success
        final_failed = not trace.final_success
        hash_id = _trace_hash_id(trace)
        search_text = " ".join([trace.req_id, hash_id, trace.prompt] + [a.failure_reason for a in trace.attempts]).lower()
        rows.append(
            f"<tr data-retry-row data-has-failure=\"{str(has_failure).lower()}\" "
            f"data-eval-failed=\"{str(eval_failed).lower()}\" data-final-success=\"{str(final_success).lower()}\" "
            f"data-final-failed=\"{str(final_failed).lower()}\" "
            f"data-search=\"{_escape(search_text)}\">"
            f"<td>{display_id}</td><td>{_escape(trace.req_id)}</td><td>{_escape(hash_id)}</td>"
            + "".join(attempt_cells)
            + f"<td><button class=\"{final_class}\" onclick=\"elaOpenAttempt('{final_id}')\">{final_symbol}</button></td>"
            + f"<td><span class=\"result-pill {eval_class}\">{eval_text}</span></td></tr>"
        )
    return (
        f"<div class=\"toolbar\"><input id=\"{dom_prefix}retry-search\" type=\"search\" placeholder=\"搜索 req_id / hash_id / prompt / 失败原因\" oninput=\"elaFilterRetry('{dom_prefix}')\">"
        f"<button id=\"{dom_prefix}failure-filter\" type=\"button\" onclick=\"elaToggleFailureFilter('{dom_prefix}')\">只看过程失败</button>"
        f"<button id=\"{dom_prefix}eval-failed-filter\" type=\"button\" onclick=\"elaToggleEvalFailedFilter('{dom_prefix}')\">只看做错</button>"
        f"<button id=\"{dom_prefix}final-success-filter\" type=\"button\" onclick=\"elaToggleFinalSuccessFilter('{dom_prefix}')\">只看推理成功</button>"
        f"<button id=\"{dom_prefix}final-failed-filter\" type=\"button\" onclick=\"elaToggleFinalFailedFilter('{dom_prefix}')\">只看推理失败</button></div>"
        f"<table class=\"retry-table\"><thead><tr><th>id</th><th>req_id</th><th>hash_id</th>{headers}<th>最终推理</th><th>评测结果</th></tr></thead><tbody data-retry-scope=\"{dom_prefix}\">{''.join(rows)}</tbody></table>"
    )


def _render_response_beeswarm_chart(traces: list[ReqTrace], metrics: Metrics, attempt_prefix: str = "") -> str:
    return (
        "<section><h2>response 长度点阵图</h2>"
        f"{_render_response_beeswarm_chart_content(traces, metrics, attempt_prefix)}"
        "</section>"
    )


def _render_response_beeswarm_chart_content(traces: list[ReqTrace], metrics: Metrics, attempt_prefix: str = "") -> str:
    points = []
    column_counts: dict[float, int] = {}
    max_column_count = 0
    for display_id, trace in enumerate(traces, start=1):
        left = _beeswarm_left(trace.final_response_length)
        column_index = column_counts.get(left, 0)
        column_counts[left] = column_index + 1
        max_column_count = max(max_column_count, column_index + 1)
        top = _beeswarm_top(column_index)
        status = _status_class(trace, metrics.eval_results.get(trace.req_id))
        final_id = _attempt_id(trace.req_id, trace.final_attempt.attempt_index, attempt_prefix) if trace.final_attempt else ""
        title = (
            f"id={display_id} req_id={trace.req_id} hash={stable_trace_hash(trace)} "
            f"长度={trace.final_response_length} 评测结果={_eval_text(metrics.eval_results.get(trace.req_id))}"
        )
        points.append(
            f"<button class=\"beeswarm-point {status}\" style=\"left:{left}%;top:{top}px\" "
            f"title=\"{_escape(title)}\" onclick=\"elaOpenAttempt('{final_id}')\"></button>"
        )
    chart_height = _beeswarm_chart_height(max_column_count)
    return (
        f"{_render_length_scale('beeswarm')}<div class=\"beeswarm-chart\" style=\"height:{chart_height}px\">{''.join(points)}</div>"
        f"{_render_success_response_length_boxplots(traces, metrics)}"
    )


def _render_success_response_length_boxplots(traces: list[ReqTrace], metrics: Metrics) -> str:
    correct_lengths: list[int] = []
    wrong_lengths: list[int] = []
    for trace in traces:
        # 只统计最终推理成功的题，避免推理失败样本影响做对/做错 response 长度分布。
        if not trace.final_success:
            continue
        eval_result = metrics.eval_results.get(trace.req_id)
        if eval_result is True:
            correct_lengths.append(trace.final_response_length)
        elif eval_result is False:
            wrong_lengths.append(trace.final_response_length)

    correct_boxplot = _response_length_boxplot(correct_lengths)
    wrong_boxplot = _response_length_boxplot(wrong_lengths)
    charts = "".join(
        _boxplot_card(label, boxplot)
        for label, boxplot in [
            ("做对题目 response 长度", correct_boxplot),
            ("做错题目 response 长度", wrong_boxplot),
        ]
        if boxplot
    )
    if not charts:
        return ""
    sample_count = len(correct_lengths) + len(wrong_lengths)
    return (
        "<div class=\"boxplot-row-title\">不含推理失败题目的 response 长度箱线图"
        f"<span class=\"sample-count\">总样本数 {sample_count}</span></div>"
        f"<div class=\"boxplot-grid response-boxplot-grid\">{charts}</div>"
    )


def _render_length_scale(kind: str) -> str:
    labels = "".join(f"<span>{value}k</span>" for value in range(0, 121, 10))
    return (
        f"<div class=\"length-scale-row {kind}\"><div></div>"
        f"<div class=\"length-scale-track\">{labels}</div><div></div></div>"
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


def _boxplot_card(label: str, boxplot: dict[str, Any]) -> str:
    chart = _boxplot_html(label, boxplot)
    return (
        f"<div class=\"boxplot-card\"><div class=\"label\">{_escape(label)}</div>"
        f"{chart}</div>"
    )


def _boxplot_html(label: str, boxplot: dict[str, Any]) -> str:
    maximum, scale_text = _boxplot_scale(label, boxplot)
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
    if scale_text:
        title += f" scale=0-{scale_text}"
    meta = (
        f"min {boxplot.get('min')} · p25 {boxplot.get('q1')} · p50 {boxplot.get('median')} "
        f"· p75 {boxplot.get('q3')} · max {boxplot.get('max')}"
    )
    if scale_text:
        meta += f" · scale {scale_text}"
    return (
        f"<div class=\"boxplot\" title=\"{_escape(title)}\">"
        f"<span class=\"whisker\" style=\"bottom:{whisker_bottom}%;height:{whisker_height}%\"></span>"
        f"<span class=\"cap min\" style=\"bottom:{min_pos}%\"></span>"
        f"<span class=\"cap max\" style=\"bottom:{max_pos}%\"></span>"
        f"<span class=\"box\" style=\"bottom:{box_bottom}%;height:{box_height}%\"></span>"
        f"<span class=\"quartile q1\" style=\"bottom:{q1_pos}%\"></span>"
        f"<span class=\"quartile q3\" style=\"bottom:{q3_pos}%\"></span>"
        f"<span class=\"median\" style=\"bottom:{median_pos}%\"></span></div>"
        f"<div class=\"boxplot-meta\">{meta}</div>"
    )


def _boxplot_scale(label: str, boxplot: dict[str, Any]) -> tuple[float, str]:
    if label in {"content tokens", "content tokens 非零"}:
        return 64000.0, "64k"
    if label in {"used_time", "total_used_time"}:
        maximum = float(boxplot.get("max") or 0)
        return (maximum if maximum > 0 else 1.0), ""
    return 120000.0, "120k"


def _response_length_boxplot(values: list[int]) -> dict[str, float | int] | None:
    numbers = sorted(float(value) for value in values)
    if not numbers:
        return None
    return {
        "count": len(numbers),
        "min": round(numbers[0], 2),
        "q1": round(_percentile(numbers, 0.25), 2),
        "median": round(_percentile(numbers, 0.5), 2),
        "q3": round(_percentile(numbers, 0.75), 2),
        "max": round(numbers[-1], 2),
        "avg": round(sum(numbers) / len(numbers), 2),
    }


def _percentile(numbers: list[float], ratio: float) -> float:
    if len(numbers) == 1:
        return numbers[0]
    position = (len(numbers) - 1) * ratio
    lower = int(position)
    upper = min(lower + 1, len(numbers) - 1)
    weight = position - lower
    return numbers[lower] * (1 - weight) + numbers[upper] * weight


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
    return sorted(traces, key=lambda trace: (_trace_hash_id(trace), trace.req_id))


def _trace_hash_id(trace: ReqTrace) -> str:
    return stable_trace_hash(trace)


def _fixed_width(length: int | float) -> int:
    try:
        value = float(length)
    except (TypeError, ValueError):
        value = 0
    if value <= 0:
        return 0
    return max(1, min(100, round(value / 120000 * 100)))


def _beeswarm_top(column_index: int) -> int:
    return 12 + column_index * 11


def _beeswarm_chart_height(max_column_count: int) -> int:
    if max_column_count <= 0:
        return 384
    return max(384, 24 + (max_column_count - 1) * 11)


def _beeswarm_left(length: int) -> float:
    width = _fixed_width(length)
    if width <= 0:
        # 推理失败通常长度为 0；保持在同一列，同时避免贴边裁剪。
        return 2.4
    return round(2 + width * 0.97, 3)


def _eval_text(value: bool | None) -> str:
    if value is True:
        return "做对"
    if value is False:
        return "做错"
    return "-"


def _status_class(trace: ReqTrace, eval_result: bool | None) -> str:
    if not trace.final_success:
        return "infer-fail"
    if eval_result is True:
        return "ok"
    if eval_result is False:
        return "bad"
    return "unknown"


def to_json_script(value: Any) -> str:
    """生成可安全嵌入 script 的 JSON 字符串。"""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def _attempt_payload(traces: list[ReqTrace], attempt_prefix: str = "") -> dict[str, Any]:
    payload = {}
    for trace in traces:
        for attempt in trace.attempts:
            payload[_attempt_id(trace.req_id, attempt.attempt_index, attempt_prefix)] = {
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


def _attempt_id(req_id: str, attempt_index: int, attempt_prefix: str = "") -> str:
    return f"{attempt_prefix}{req_id}::{attempt_index}"
