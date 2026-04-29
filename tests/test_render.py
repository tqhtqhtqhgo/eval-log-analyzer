from pathlib import Path

from eval_log_analyzer.metrics import calculate_metrics
from eval_log_analyzer.parser import parse_log
from eval_log_analyzer.render import render_html


def test_render_basic_html_without_remote_assets(tmp_path: Path) -> None:
    parsed = parse_log(
        """
{"req_id":"r1","requests":{"messages":[{"role":"user","content":"p1"}]}}
{"req_id":"r1","status_code":200,"usage":{"completion_tokens":7},"respMsg":{"content":"ok"}}
"""
    )
    metrics = calculate_metrics(
        [{"req_id": "r1", "eval_result": "TRUE", "model_version": "m1", "dataset_name": "d1", "judge_model": "j1"}],
        parsed.traces,
        log_name="mini.log",
        zip_name="mini.zip",
    )
    output = tmp_path / "report.html"

    render_html(str(output), metrics, parsed.traces, enable_hash_repeat_chart=True)
    html = output.read_text(encoding="utf-8")

    assert "评测日志分析报告" in html
    assert "m1" in html
    assert "异常摘要" in html
    assert "重试链路表" in html
    assert "response 长度紧凑分布图" in html
    assert "compact-length-line" in html
    assert "response 长度分布图" in html
    assert "length-row" in html
    assert "只看过程失败" in html
    assert "只看做错" in html
    assert "评测结果" in html
    assert "data-eval-failed=\"false\"" in html
    assert "做对" in html
    assert "boxplot" in html
    assert "style=\"width:1%\"" in html
    assert "elaToggleFailureFilter" in html
    assert "elaToggleEvalFailedFilter" in html
    assert "hash_id 重复评测聚合紧凑分布图" in html
    assert "hash_id 重复评测聚合图" in html
    assert "elaOpenHash" in html
    assert "r1" in html
    assert "elaOpenAttempt" in html
    assert "json-modal" in html
    assert "https://" not in html
    assert "http://" not in html
    assert "cdn" not in html.lower()
