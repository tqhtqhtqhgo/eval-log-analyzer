from eval_log_analyzer.parser import extract_response_length, parse_log


def test_parse_single_success_and_hash_id() -> None:
    result = parse_log(
        """
{"req_id":"r1","hash_id":"h1","requests":{"messages":[{"role":"user","content":"p1"}]}}
{"req_id":"r1","status_code":200,"usage":{"completion_tokens":7},"respMsg":{"content":"ok"}}
"""
    )

    trace = result.traces[0]
    assert trace.req_id == "r1"
    assert trace.hash_id == "h1"
    assert trace.prompt == "p1"
    assert trace.final_success is True
    assert trace.final_response_length == 7


def test_parse_retry_first_fail_then_success() -> None:
    result = parse_log(
        """
{"req_id":"r2","requests":{"messages":[{"role":"user","content":"p2"}]}}
{"req_id":"r2","status_code":500,"respMsg":{"content":"bad"}}
{"req_id":"r2","requests":{"messages":[{"role":"user","content":"p2"}]}}
{"req_id":"r2","status_code":200,"token_num":3,"respMsg":{"content":"ok"}}
"""
    )

    trace = result.traces[0]
    assert [a.success for a in trace.attempts] == [False, True]
    assert trace.attempts[0].failure_reason == "status_code=500"
    assert trace.final_success is True


def test_parse_final_fail_content_empty() -> None:
    result = parse_log(
        """
{"req_id":"r3","requests":{"messages":[{"role":"user","content":"p3"}]}}
{"req_id":"r3","status_code":200,"respMsg":{"content":""}}
"""
    )

    assert result.traces[0].final_success is False
    assert result.traces[0].final_attempt.failure_reason == "content_empty"


def test_parse_missing_response_and_orphan_response() -> None:
    result = parse_log(
        """
{"req_id":"r4","requests":{"messages":[{"role":"user","content":"p4"}]}}
{"req_id":"r5","status_code":200,"respMsg":{"content":"orphan"}}
"""
    )

    traces = {trace.req_id: trace for trace in result.traces}
    assert traces["r4"].final_attempt.failure_reason == "missing_response"
    assert traces["r5"].final_attempt.failure_reason == "missing_request"


def test_parse_multiline_json() -> None:
    result = parse_log(
        """
{
  "req_id": "r6",
  "requests": {"messages": [{"role": "user", "content": "p6"}]}
}
{
  "req_id": "r6",
  "status_code": 200,
  "usage": {"completion_tokens": 8},
  "respMsg": {"content": "ok"}
}
"""
    )

    assert result.parse_error_count == 0
    assert result.traces[0].final_success is True


def test_response_length_priority() -> None:
    assert extract_response_length({"usage": {"completion_tokens": 9}, "token_num": 2}) == 9
    assert extract_response_length({"reasoning_token": 2, "content_token": 3}) == 5
    assert extract_response_length({"respMsg": {"reasoning": "ab", "content": "cd"}}) == 4
