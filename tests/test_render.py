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

    render_html(str(output), metrics, parsed.traces)
    html = output.read_text(encoding="utf-8")

    assert "评测日志分析报告" in html
    assert "m1" in html
    assert "异常摘要" in html
    assert "重试链路表" in html
    assert "r1" in html
    assert "elaOpenAttempt" in html
    assert "json-modal" in html
    assert "https://" not in html
    assert "http://" not in html
    assert "cdn" not in html.lower()
