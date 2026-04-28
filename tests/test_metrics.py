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
        {"req_id": "r1", "eval_result": "TRUE", "complete_tokens": 10, "reasoning_token": 3, "content_token": 7, "used_time": "1.5", "total_used_time": 2.0, "infer_retry": "否", "retry_success": "", "model_version": "m", "dataset_name": "d", "judge_model": "j"},
        {"req_id": "r2", "eval_result": "FALSE", "complete_tokens": 20, "reasoning_token": 4, "content_token": 8, "used_time": "2.5", "total_used_time": 3.0, "infer_retry": "是", "retry_success": "是", "exception": "Content OutOfMaxLength: x"},
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

    assert metrics.export_summary["total"] == 2
    assert metrics.export_summary["passed"] == 1
    assert metrics.export_summary["pass_rate"] == 0.5
    assert metrics.export_summary["avg_complete_tokens"] == 15
    assert metrics.export_summary["avg_used_time"] == 2
    assert metrics.export_summary["retry_count"] == 1
    assert metrics.export_summary["retry_success_count"] == 1
    assert metrics.trace_summary["retry_req_id_count"] == 1
    assert metrics.trace_summary["retry_final_success_count"] == 1
    assert metrics.trace_summary["final_failed_count"] == 1
    assert metrics.export_summary["exception_distribution"] == {"Content OutOfMaxLength": 1}
    assert metrics.export_summary["empty_count"] == 1
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
    assert groups[0]["hash_id"] == "83878c91171338902e0fe0fb97a8c47a"
    assert groups[0]["req_ids"] == ["r1", "r2"]
    assert groups[0]["avg_response_length"] == 15
    assert groups[0]["correct_count"] == 1
    assert groups[0]["total_count"] == 3
