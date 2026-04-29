from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class Attempt:
    req_id: str
    attempt_index: int
    request_json: dict[str, Any] | None
    response_json: dict[str, Any] | None
    success: bool
    failure_reason: str
    response_length: int
    used_time: float | None
    hash_id: str | None
    prompt: str
    missing_request: bool = False
    missing_response: bool = False


@dataclass
class ReqTrace:
    req_id: str
    row_id: int
    hash_id: str | None
    prompt: str
    attempts: list[Attempt]
    final_success: bool
    final_attempt: Attempt | None
    final_response_length: int


@dataclass
class ParseResult:
    traces: list[ReqTrace]
    parse_error_count: int


def parse_log(log_text: str) -> ParseResult:
    """解析 log 文本并构建 req_id 粒度的 attempt 链路。"""
    records, parse_error_count = parse_log_records(log_text)
    attempts_by_req: dict[str, list[Attempt]] = {}

    for record in records:
        req_id = str(record.get("req_id") or "")
        if not req_id:
            parse_error_count += 1
            continue
        if is_request_record(record):
            attempt = Attempt(
                req_id=req_id,
                attempt_index=len(attempts_by_req.get(req_id, [])) + 1,
                request_json=record,
                response_json=None,
                success=False,
                failure_reason="missing_response",
                response_length=0,
                used_time=None,
                hash_id=extract_hash_id(record),
                prompt=extract_prompt(record),
            )
            attempts_by_req.setdefault(req_id, []).append(attempt)
        elif is_response_record(record):
            attempt = _find_open_attempt(attempts_by_req.get(req_id, []))
            if attempt is None:
                attempt = Attempt(
                    req_id=req_id,
                    attempt_index=len(attempts_by_req.get(req_id, [])) + 1,
                    request_json=None,
                    response_json=None,
                    success=False,
                    failure_reason="missing_request",
                    response_length=0,
                    used_time=None,
                    hash_id=extract_hash_id(record),
                    prompt=extract_prompt(record),
                    missing_request=True,
                )
                attempts_by_req.setdefault(req_id, []).append(attempt)
            _bind_response(attempt, record)

    traces = []
    for row_id, (req_id, attempts) in enumerate(attempts_by_req.items(), start=1):
        for attempt in attempts:
            if attempt.response_json is None:
                attempt.missing_response = not attempt.missing_request
                attempt.success = False
                attempt.failure_reason = "missing_request" if attempt.missing_request else "missing_response"
        final_attempt = _final_attempt(attempts)
        traces.append(
            ReqTrace(
                req_id=req_id,
                row_id=row_id,
                hash_id=_first_non_empty([a.hash_id for a in attempts]),
                prompt=_first_non_empty([a.prompt for a in attempts]) or "",
                attempts=attempts,
                final_success=bool(final_attempt and final_attempt.success),
                final_attempt=final_attempt,
                final_response_length=final_attempt.response_length if final_attempt else 0,
            )
        )
    return ParseResult(traces=traces, parse_error_count=parse_error_count)


def parse_log_records(log_text: str) -> tuple[list[dict[str, Any]], int]:
    """解析 JSONL 和多行 JSON；单条坏记录只计数不终止整体解析。"""
    records: list[dict[str, Any]] = []
    parse_error_count = 0
    lines = [line for line in log_text.splitlines() if line.strip()]
    buffer = ""
    depth = 0
    in_string = False
    escape = False

    for line in lines:
        stripped = line.strip()
        if not buffer:
            try:
                value = json.loads(stripped)
                if isinstance(value, dict):
                    records.append(value)
                else:
                    parse_error_count += 1
                continue
            except json.JSONDecodeError:
                pass
        buffer = f"{buffer}\n{stripped}" if buffer else stripped
        for char in stripped:
            if escape:
                escape = False
                continue
            if char == "\\" and in_string:
                escape = True
                continue
            if char == '"':
                in_string = not in_string
            elif not in_string and char in "{[":
                depth += 1
            elif not in_string and char in "}]":
                depth -= 1
        if depth <= 0 and buffer:
            try:
                value = json.loads(buffer)
                if isinstance(value, dict):
                    records.append(value)
                else:
                    parse_error_count += 1
            except json.JSONDecodeError:
                parse_error_count += 1
            buffer = ""
            depth = 0
            in_string = False
            escape = False

    if buffer:
        parse_error_count += 1
    return records, parse_error_count


def is_request_record(record: dict[str, Any]) -> bool:
    return "requests" in record


def is_response_record(record: dict[str, Any]) -> bool:
    return any(key in record for key in ("status_code", "exception", "respMsg", "output_reason", "usage"))


def extract_hash_id(record: dict[str, Any] | None) -> str | None:
    if not record:
        return None
    value = record.get("hash_id")
    return str(value) if value else None


def extract_prompt(record: dict[str, Any] | None) -> str:
    if not record:
        return ""
    if record.get("prompt"):
        return str(record["prompt"])
    requests = record.get("requests")
    if isinstance(requests, dict):
        messages = requests.get("messages")
        if isinstance(messages, list):
            for message in messages:
                if isinstance(message, dict) and message.get("role") == "user":
                    return str(message.get("content") or "")
    return ""


def extract_response_length(response: dict[str, Any] | None) -> int:
    if not response:
        return 0
    usage = response.get("usage")
    if isinstance(usage, dict):
        for key in ("completion_tokens", "complete_tokens"):
            number = _to_int(usage.get(key))
            if number is not None:
                return number
    for key in ("token_num",):
        number = _to_int(response.get(key))
        if number is not None:
            return number
    sum_value = _sum_ints(response.get("reasoning_token"), response.get("content_token"))
    if sum_value is not None:
        return sum_value
    number = _to_int(response.get("total_chunk"))
    if number is not None:
        return number
    sum_value = _sum_ints(response.get("reasoning_chunk"), response.get("content_chunk"))
    if sum_value is not None:
        return sum_value
    resp_msg = response.get("respMsg")
    if isinstance(resp_msg, dict):
        text = f"{resp_msg.get('reasoning') or ''}{resp_msg.get('content') or ''}"
        if text:
            return len(text)
    text = f"{response.get('reasoning') or ''}{response.get('content') or ''}"
    return len(text) if text else 0


def _bind_response(attempt: Attempt, response: dict[str, Any]) -> None:
    attempt.response_json = response
    attempt.used_time = _to_float(response.get("used_time"))
    attempt.hash_id = attempt.hash_id or extract_hash_id(response)
    attempt.prompt = attempt.prompt or extract_prompt(response)
    attempt.response_length = extract_response_length(response)
    attempt.success = _is_success_response(response, attempt.missing_request)
    attempt.failure_reason = "" if attempt.success else _failure_reason(response, attempt.missing_request)


def _is_success_response(response: dict[str, Any], missing_request: bool) -> bool:
    if missing_request:
        return False
    if response.get("exception") or response.get("output_reason"):
        return False
    if response.get("status_code") != 200:
        return False
    return bool(_extract_content(response))


def _failure_reason(response: dict[str, Any] | None, missing_request: bool = False) -> str:
    if response is None:
        return "missing_request" if missing_request else "missing_response"
    if response.get("exception"):
        return str(response["exception"])
    if response.get("output_reason"):
        return str(response["output_reason"])
    if "status_code" in response and response.get("status_code") != 200:
        return f"status_code={response.get('status_code')}"
    if not _extract_content(response):
        return "content_empty"
    if missing_request:
        return "missing_request"
    return "unknown_error"


def _extract_content(response: dict[str, Any]) -> str:
    resp_msg = response.get("respMsg")
    if isinstance(resp_msg, dict):
        return str(resp_msg.get("content") or "")
    return str(response.get("content") or "")


def _find_open_attempt(attempts: list[Attempt] | None) -> Attempt | None:
    if not attempts:
        return None
    for attempt in reversed(attempts):
        if attempt.response_json is None:
            return attempt
    return None


def _final_attempt(attempts: list[Attempt]) -> Attempt | None:
    """最终链路优先取成功 attempt；多次重试中任一次成功即视为最终成功。"""
    for attempt in reversed(attempts):
        if attempt.success:
            return attempt
    return attempts[-1] if attempts else None


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sum_ints(left: Any, right: Any) -> int | None:
    left_int = _to_int(left)
    right_int = _to_int(right)
    if left_int is None and right_int is None:
        return None
    return (left_int or 0) + (right_int or 0)


def _first_non_empty(values: list[str | None]) -> str | None:
    for value in values:
        if value:
            return value
    return None
