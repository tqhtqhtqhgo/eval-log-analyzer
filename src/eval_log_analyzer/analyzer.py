from __future__ import annotations

from pathlib import Path
import webbrowser

from .loader import load_eval_zip
from .metrics import calculate_metrics
from .parser import parse_log
from .render import render_html


def analysis_html(
    zip_path: str,
    output_html: str | None = None,
    enable_hash_repeat_chart: bool = False,
    repeat_group_size: int | None = None,
    max_attempt_columns: int = 5,
    open_browser: bool = False,
) -> str:
    """分析评测日志 zip，生成单个静态 HTML 文件。"""
    path = Path(zip_path)
    if not path.exists():
        raise FileNotFoundError(f"zip 文件不存在: {zip_path}")
    if not path.is_file():
        raise ValueError(f"zip 路径不是文件: {zip_path}")
    target = Path(output_html) if output_html else path.with_name(f"{path.stem}_analysis.html")
    loaded = load_eval_zip(path)
    parsed = parse_log(loaded.log_text)
    metrics = calculate_metrics(
        export_data_list=loaded.export_data_list,
        traces=parsed.traces,
        parse_error_count=parsed.parse_error_count,
        empty_result=loaded.empty_result,
        overlength_result=loaded.overlength_result,
        timeout_result=loaded.timeout_result,
        duplicate_result=loaded.duplicate_result,
        xlsx_rows=loaded.xlsx_rows,
        repeat_group_size=repeat_group_size,
        log_name=loaded.log_name,
        zip_name=loaded.zip_name,
    )
    render_html(
        str(target),
        metrics,
        parsed.traces,
        enable_hash_repeat_chart=enable_hash_repeat_chart,
        max_attempt_columns=max_attempt_columns,
    )
    if open_browser:
        webbrowser.open(target.resolve().as_uri())
    return str(target)
