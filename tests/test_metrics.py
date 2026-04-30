from eval_log_analyzer.metrics import build_hash_repeat_groups, calculate_metrics
from eval_log_analyzer.parser import parse_log


def test_calculate_export_and_trace_metrics() -> None:
    parsed = parse_log(
        """
{"req_id":"r1","hash_id":"h1","requests":{"messages":[{"role":"user","content":"p1"}]}}
{"req_id":"r1","status_code":200,"usage":{"completion_tokens":10},"respMsg":{"content":"ok"}}
{"req_id":"r2","hash_id":"h1","requests":{"messages":[{"role":"user","content":"p1"}]}}
{"req_id":"r2","exception":"boom","respMsg":{"content":"bad"}}
{"req_id":"r2","hash_id":"h1","requests":{"messages":[{"role":"user","content":"p1"}]}}
{"req_id":"r2","status_code":200,"usage":{"completion_tokens":20},"respMsg":{"content":"ok"}}
{"req_id":"r3","hash_id":"h2","requests":{"messages":[{"role":"user","content":"p3"}]}}
{"req_id":"r3","status_code":200,"respMsg":{"content":""}}
"""
    )
    export_rows = [
        {"req_id": "r1", "eval_result": "True", "complete_tokens": 10, "reasoning_token": 3, "content_token": 7, "used_time": "1.5", "total_used_time": 2.0, "infer_retry": "否", "retry_success": "", "model_version": "m", "dataset_name": "d", "judge_model": "j", "exception_list": ["HTTPConnectionPool failed"]},
        {"req_id": "r2", "eval_result": "False", "complete_tokens": 20, "reasoning_token": 4, "content_token": 8, "used_time": "2.5", "total_used_time": 3.0, "infer_retry": "是", "retry_success": "是", "exception": "Content OutOfMaxLength: x"},
        {"req_id": "r3", "eval_result": "False", "complete_tokens": 0, "reasoning_token": 0, "content_token": 0, "used_time": "", "total_used_time": "", "infer_retry": "否", "retry_success": "", "exception": "Streaming parse timeout after 60s"},
    ]

    metrics = calculate_metrics(
        export_rows,
        parsed.traces,
        parsed.parse_error_count,
        empty_result=[{"output_reason": "empty"}],
        overlength_result=[{"output_reason": "Content OutOfMaxLength"}],
        timeout_result={"r2": [{"output_reason": "timeout"}]},
        duplicate_result=[{"req_id": "r2"}],
        log_name="mini.log",
        zip_name="mini.zip",
    )

    assert metrics.export_summary["total"] == 3
    assert metrics.export_summary["passed"] == 1
    assert metrics.export_summary["pass_rate"] == 1 / 3
    assert metrics.export_summary["avg_complete_tokens"] == 10
    assert metrics.export_summary["avg_used_time"] == 2
    assert metrics.export_summary["boxplots"]["complete_tokens"]["median"] == 10
    assert metrics.export_summary["boxplots"]["complete_tokens_nonzero"]["median"] == 15
    assert metrics.export_summary["boxplots"]["reasoning_token_nonzero"]["min"] == 3
    assert metrics.export_summary["boxplots"]["content_token_nonzero"]["min"] == 7
    assert metrics.export_summary["boxplots"]["total_used_time"]["q1"] == 2.25
    assert metrics.export_summary["boxplots"]["total_used_time"]["q3"] == 2.75
    assert metrics.eval_results == {"r1": True, "r2": False, "r3": False}
    assert metrics.export_summary["retry_count"] == 1
    assert metrics.export_summary["retry_success_count"] == 1
    assert metrics.trace_summary["retry_req_id_count"] == 1
    assert metrics.trace_summary["retry_final_success_count"] == 1
    assert metrics.trace_summary["final_success_count"] == 2
    assert metrics.trace_summary["final_failed_count"] == 1
    assert metrics.trace_summary["content_empty_count"] == 1
    assert metrics.trace_summary["final_content_empty_count"] == 1
    assert metrics.trace_summary["final_other_failed_count"] == 0
    assert metrics.export_summary["exception_categories"] == {
        "content_out_of_max_length": 1,
        "streaming_parse_timeout": 1,
        "http_connection": 1,
    }
    assert all(row["type"] != "empty_result" for row in metrics.exception_summary)
    assert all(row["type"] != "overlength_result" for row in metrics.exception_summary)
    assert any(row["type"] == "content_empty" and row["count"] == 1 for row in metrics.exception_summary)
    assert all(row["type"] != "export_exception" for row in metrics.exception_summary)
    assert metrics.basic_info["model"] == "m"


def test_hash_repeat_groups() -> None:
    parsed = parse_log(
        """
{"req_id":"r1","hash_id":"h1","requests":{"messages":[{"role":"user","content":"p"}]}}
{"req_id":"r1","status_code":200,"usage":{"completion_tokens":10},"respMsg":{"content":"ok"}}
{"req_id":"r2","hash_id":"different_hash","requests":{"messages":[{"role":"user","content":"p"}]}}
{"req_id":"r2","status_code":200,"usage":{"completion_tokens":20},"respMsg":{"content":"ok"}}
"""
    )

    groups = build_hash_repeat_groups(parsed.traces, [{"req_id": "r1", "eval_result": "TRUE"}], 3)

    assert len(groups) == 1
    assert groups[0]["hash_id"] == "148de9c5a7a44d19e56cd9ae1a554bf6"
    assert groups[0]["req_ids"] == ["r1", "r2"]
    assert groups[0]["avg_response_length"] == 15
    assert groups[0]["correct_count"] == 1
    assert groups[0]["total_count"] == 3


def test_hash_repeat_groups_are_sorted_by_stable_hash() -> None:
    parsed = parse_log(
        """
{"req_id":"r_b","requests":{"messages":[{"role":"user","content":"b"}]}}
{"req_id":"r_b","status_code":200,"usage":{"completion_tokens":20},"respMsg":{"content":"ok"}}
{"req_id":"r_a","requests":{"messages":[{"role":"user","content":"a"}]}}
{"req_id":"r_a","status_code":200,"usage":{"completion_tokens":10},"respMsg":{"content":"ok"}}
"""
    )

    groups = build_hash_repeat_groups(parsed.traces, [])

    assert [group["req_ids"] for group in groups] == [["r_b"], ["r_a"]]
