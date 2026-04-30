from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from .parser import ReqTrace


PASS_VALUES = {"TRUE", "True", "true", "1", "PASS", "pass", "正确"}
FAIL_VALUES = {"FALSE", "False", "false", "0", "FAIL", "fail", "错误"}


@dataclass
class Metrics:
    basic_info: dict[str, Any]
    export_summary: dict[str, Any]
    trace_summary: dict[str, Any]
    exception_summary: list[dict[str, Any]]
    hash_repeat_groups: list[dict[str, Any]]
    eval_results: dict[str, bool | None]


def calculate_metrics(
    export_data_list: list[dict[str, Any]] | None = None,
    traces: list[ReqTrace] | None = None,
    parse_error_count: int = 0,
    empty_result: Any | None = None,
    overlength_result: Any | None = None,
    timeout_result: Any | None = None,
    duplicate_result: Any | None = None,
    xlsx_rows: list[dict[str, Any]] | None = None,
    repeat_group_size: int | None = None,
    log_name: str | None = None,
    zip_name: str | None = None,
) -> Metrics:
    """汇总 export、log trace 和异常文件指标。"""
    export_rows = export_data_list or []
    req_traces = traces or []
    export_summary = _export_summary(export_rows)
    eval_results = _eval_results(export_rows)
    trace_summary = _trace_summary(req_traces, parse_error_count)
    optional_summary = _optional_file_summary(duplicate_result)
    basic_info = _basic_info(xlsx_rows or [], export_rows, export_summary, log_name, zip_name)
    exception_summary = _exception_summary(export_summary, trace_summary, optional_summary)
    hash_repeat_groups = build_hash_repeat_groups(req_traces, export_rows, repeat_group_size)
    return Metrics(
        basic_info=basic_info,
        export_summary={**export_summary, **optional_summary},
        trace_summary=trace_summary,
        exception_summary=exception_summary,
        hash_repeat_groups=hash_repeat_groups,
        eval_results=eval_results,
    )


def build_hash_repeat_groups(
    traces: list[ReqTrace],
    export_data_list: list[dict[str, Any]] | None,
    repeat_group_size: int | None = None,
) -> list[dict[str, Any]]:
    """按 prompt 计算出的稳定 hash_id 聚合重复评测数据。"""
    eval_by_req = _eval_results(export_data_list or [])
    groups: dict[str, list[ReqTrace]] = defaultdict(list)
    for trace in traces:
        # 部分真实日志里同一 user message 会带不同 hash_id，因此重复评测聚合以 prompt 自算 hash 为准。
        group_hash_id = stable_trace_hash(trace)
        groups[group_hash_id].append(trace)

    result = []
    for index, hash_id in enumerate(sorted(groups), start=1):
        group_traces = groups[hash_id]
        lengths = [trace.final_response_length for trace in group_traces]
        correct = sum(1 for trace in group_traces if eval_by_req.get(trace.req_id) is True)
        total = repeat_group_size if repeat_group_size is not None else len(group_traces)
        result.append(
            {
                "id": index,
                "hash_id": hash_id,
                "req_ids": [trace.req_id for trace in group_traces],
                "avg_response_length": round(sum(lengths) / len(lengths), 2) if lengths else 0,
                "correct_count": correct,
                "total_count": total,
                "items": [
                    {
                        "req_id": trace.req_id,
                        "final_success": trace.final_success,
                        "final_response_length": trace.final_response_length,
                        "eval_result": eval_by_req.get(trace.req_id),
                    }
                    for trace in group_traces
                ],
            }
        )
    return result


def stable_trace_hash(trace: ReqTrace) -> str:
    """返回由 user prompt 计算出的稳定排序和聚合 hash。"""
    prompt = _normalize_prompt(trace.prompt)
    if prompt:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:32]
    return hashlib.sha256(trace.req_id.encode("utf-8")).hexdigest()[:32]


def _normalize_prompt(prompt: str | None) -> str:
    return " ".join(str(prompt or "").split())


def _export_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    distribution = Counter(_normalize_eval(row.get("eval_result")) for row in rows)
    passed = sum(1 for row in rows if _is_pass(row.get("eval_result")) is True)
    retry_rows = [row for row in rows if _is_retry(row)]
    retry_success = [row for row in retry_rows if _is_retry_success(row)]
    exception_rows = [row for row in rows if row.get("exception") or row.get("exception_list")]
    return {
        "total": len(rows),
        "passed": passed,
        "pass_rate": passed / len(rows) if rows else 0,
        "eval_result_distribution": dict(distribution),
        "avg_complete_tokens": _avg(row.get("complete_tokens") for row in rows),
        "avg_reasoning_token": _avg(row.get("reasoning_token") for row in rows),
        "avg_content_token": _avg(row.get("content_token") for row in rows),
        "avg_used_time": _avg(row.get("used_time") for row in rows),
        "avg_total_used_time": _avg(row.get("total_used_time") for row in rows),
        "boxplots": {
            "complete_tokens": _boxplot(row.get("complete_tokens") for row in rows),
            "reasoning_token": _boxplot(row.get("reasoning_token") for row in rows),
            "content_token": _boxplot(row.get("content_token") for row in rows),
            "used_time": _boxplot(row.get("used_time") for row in rows),
            "total_used_time": _boxplot(row.get("total_used_time") for row in rows),
            "complete_tokens_nonzero": _boxplot_nonzero(row.get("complete_tokens") for row in rows),
            "reasoning_token_nonzero": _boxplot_nonzero(row.get("reasoning_token") for row in rows),
            "content_token_nonzero": _boxplot_nonzero(row.get("content_token") for row in rows),
        },
        "retry_count": len(retry_rows),
        "retry_success_count": len(retry_success),
        "exception_count": len(exception_rows),
        "exception_distribution": dict(Counter(_exception_name(row) for row in exception_rows)),
        "exception_categories": _exception_categories(rows),
    }


def _eval_results(rows: list[dict[str, Any]]) -> dict[str, bool | None]:
    results: dict[str, bool | None] = {}
    for row in rows:
        req_id = row.get("req_id")
        if req_id is not None:
            results[str(req_id)] = _is_pass(row.get("eval_result"))
    return results


def _trace_summary(traces: list[ReqTrace], parse_error_count: int) -> dict[str, Any]:
    retry_traces = [trace for trace in traces if len(trace.attempts) > 1]
    final_content_empty_count = sum(1 for trace in traces if _is_final_content_empty(trace))
    content_empty_count = sum(1 for trace in traces for attempt in trace.attempts if _is_response_content_empty(attempt.response_json))
    final_success_count = sum(1 for trace in traces if trace.final_success)
    final_failed_count = sum(1 for trace in traces if not trace.final_success)
    return {
        "req_id_total": len(traces),
        "final_success_count": final_success_count,
        "final_failed_count": final_failed_count,
        "content_empty_count": content_empty_count,
        "final_content_empty_count": final_content_empty_count,
        "final_other_failed_count": max(0, final_failed_count - final_content_empty_count),
        "retry_req_id_count": len(retry_traces),
        "retry_final_success_count": sum(1 for trace in retry_traces if trace.final_success),
        "parse_error_count": parse_error_count,
    }


def _is_final_content_empty(trace: ReqTrace) -> bool:
    return bool(
        not trace.final_success
        and trace.final_attempt
        and trace.final_attempt.failure_reason == "content_empty"
    )


def _is_response_content_empty(response: dict[str, Any] | None) -> bool:
    if not response:
        return False
    resp_msg = response.get("respMsg")
    if not isinstance(resp_msg, dict):
        return False
    return str(resp_msg.get("content") or "").strip() == ""


def _optional_file_summary(duplicate_result: Any | None) -> dict[str, Any]:
    return {
        "duplicate_exists": duplicate_result is not None,
        "duplicate_count": _count_items(duplicate_result),
    }


def _basic_info(
    xlsx_rows: list[dict[str, Any]],
    export_rows: list[dict[str, Any]],
    export_summary: dict[str, Any],
    log_name: str | None,
    zip_name: str | None,
) -> dict[str, Any]:
    first_xlsx = xlsx_rows[0] if xlsx_rows else {}
    first_export = export_rows[0] if export_rows else {}
    return {
        "model": first_xlsx.get("评测模型") or first_export.get("model_version") or _infer_from_name(log_name),
        "dataset": first_xlsx.get("用例集") or first_export.get("dataset_name") or "",
        "created_time": first_export.get("created_time") or first_export.get("time") or "",
        "total": export_summary["total"],
        "passed": export_summary["passed"],
        "pass_rate": export_summary["pass_rate"],
        "judge_model": first_xlsx.get("裁判模型名称") or first_export.get("judge_model") or "",
        "log_name": log_name or "",
        "zip_name": zip_name or "",
    }


def _exception_summary(
    export_summary: dict[str, Any],
    trace_summary: dict[str, Any],
    optional_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "type": "Content OutOfMaxLength",
            "count": export_summary["exception_categories"]["content_out_of_max_length"],
            "description": "exception 包含 OutOfMaxLength",
        },
        {
            "type": "timeout",
            "count": export_summary["exception_categories"]["streaming_parse_timeout"],
            "description": "exception 以 Streaming parse timeout 开头",
        },
        {
            "type": "HTTP Connection 异常",
            "count": export_summary["exception_categories"]["http_connection"],
            "description": "exception 包含 HTTPConnection",
        },
        {
            "type": "content_empty",
            "count": trace_summary["content_empty_count"],
            "description": "response.respMsg.content 为空",
        },
        {
            "type": "duplicate_result",
            "count": optional_summary["duplicate_count"],
            "description": "duplicate_result.json 已存在，当前版本暂不做 COT 循环深度分析"
            if optional_summary["duplicate_exists"]
            else "未发现 duplicate_result.json",
        },
        {"type": "parse_error", "count": trace_summary["parse_error_count"], "description": "log 中存在无法解析的 JSON"},
    ]


def _normalize_eval(value: Any) -> str:
    if value is True:
        return "PASS"
    if value is False:
        return "FAIL"
    normalized = str(value).strip()
    if normalized in PASS_VALUES:
        return "PASS"
    if normalized in FAIL_VALUES:
        return "FAIL"
    return "UNKNOWN"


def _is_pass(value: Any) -> bool | None:
    normalized = _normalize_eval(value)
    if normalized == "PASS":
        return True
    if normalized == "FAIL":
        return False
    return None


def _is_retry(row: dict[str, Any]) -> bool:
    value = row.get("infer_retry")
    return str(value).strip() not in {"", "否", "False", "false", "0", "None"}


def _is_retry_success(row: dict[str, Any]) -> bool:
    return str(row.get("retry_success") or "").strip() in {"是", "TRUE", "True", "true", "1", "PASS", "pass"}


def _exception_name(row: dict[str, Any]) -> str:
    exception = row.get("exception")
    if exception:
        return str(exception).split(":")[0]
    exception_list = row.get("exception_list")
    if isinstance(exception_list, list) and exception_list:
        return str(exception_list[0]).split(":")[0]
    return "unknown_exception"


def _exception_categories(rows: list[dict[str, Any]]) -> dict[str, int]:
    """按报告约定从 response exception 文本统计关键异常类型。"""
    counter = {
        "content_out_of_max_length": 0,
        "streaming_parse_timeout": 0,
        "http_connection": 0,
    }
    for row in rows:
        texts = _exception_texts(row)
        if any("OutOfMaxLength" in text for text in texts):
            counter["content_out_of_max_length"] += 1
        if any(text.startswith("Streaming parse timeout") for text in texts):
            counter["streaming_parse_timeout"] += 1
        if any("HTTPConnection" in text for text in texts):
            counter["http_connection"] += 1
    return counter


def _exception_texts(row: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    exception = row.get("exception")
    if exception:
        texts.append(str(exception))
    exception_list = row.get("exception_list")
    if isinstance(exception_list, list):
        texts.extend(str(item) for item in exception_list if item)
    return texts


def _count_items(value: Any | None) -> int:
    if value is None:
        return 0
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return len(value)
    return 1


def _avg(values: object) -> float:
    numbers = [_to_float(value) for value in values]
    clean = [value for value in numbers if value is not None]
    return round(sum(clean) / len(clean), 2) if clean else 0.0


def _boxplot(values: object) -> dict[str, float | int] | None:
    numbers = sorted(value for value in (_to_float(value) for value in values) if value is not None)
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


def _boxplot_nonzero(values: object) -> dict[str, float | int] | None:
    numbers = [_to_float(value) for value in values]
    return _boxplot(value for value in numbers if value is not None and value != 0)


def _percentile(numbers: list[float], ratio: float) -> float:
    if len(numbers) == 1:
        return numbers[0]
    position = (len(numbers) - 1) * ratio
    lower = int(position)
    upper = min(lower + 1, len(numbers) - 1)
    weight = position - lower
    return numbers[lower] * (1 - weight) + numbers[upper] * weight


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _infer_from_name(name: str | None) -> str:
    if not name:
        return ""
    return name.rsplit(".", 1)[0]
