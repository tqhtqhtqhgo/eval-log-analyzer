from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import webbrowser

from .loader import load_eval_zip
from .metrics import Metrics, calculate_metrics
from .parser import ReqTrace, parse_log
from .render import render_compare_html, render_html


@dataclass
class _ReportData:
    metrics: Metrics
    traces: list[ReqTrace]
    zip_name: str


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
    report_data = _build_report_data(path, repeat_group_size)
    render_html(
        str(target),
        report_data.metrics,
        report_data.traces,
        enable_hash_repeat_chart=enable_hash_repeat_chart,
        max_attempt_columns=max_attempt_columns,
    )
    if open_browser:
        webbrowser.open(target.resolve().as_uri())
    return str(target)


def compare_analysis_html(
    left_zip_path: str,
    right_zip_path: str,
    output_html: str | None = None,
    repeat_group_size: int | None = None,
    max_attempt_columns: int = 5,
    open_browser: bool = False,
) -> str:
    """对比两个同评测名前缀的评测日志 zip，生成双列静态 HTML。"""
    left_path = _validate_zip_file(left_zip_path)
    right_path = _validate_zip_file(right_zip_path)
    left_eval_name = _eval_name_prefix(left_path)
    right_eval_name = _eval_name_prefix(right_path)
    if left_eval_name != right_eval_name:
        raise ValueError(
            "两个 zip 文件名第一个下划线前的评测名必须一致: "
            f"{left_path.name} -> {left_eval_name}, {right_path.name} -> {right_eval_name}"
        )

    target = Path(output_html) if output_html else left_path.with_name(f"{left_eval_name}_compare_analysis.html")
    left_report = _build_report_data(left_path, repeat_group_size)
    right_report = _build_report_data(right_path, repeat_group_size)
    render_compare_html(
        str(target),
        left_report.metrics,
        left_report.traces,
        right_report.metrics,
        right_report.traces,
        left_report.zip_name,
        right_report.zip_name,
        max_attempt_columns=max_attempt_columns,
    )
    if open_browser:
        webbrowser.open(target.resolve().as_uri())
    return str(target)


def _validate_zip_file(zip_path: str) -> Path:
    path = Path(zip_path)
    if not path.exists():
        raise FileNotFoundError(f"zip 文件不存在: {zip_path}")
    if not path.is_file():
        raise ValueError(f"zip 路径不是文件: {zip_path}")
    return path


def _eval_name_prefix(path: Path) -> str:
    if "_" not in path.stem:
        raise ValueError(f"zip 文件名必须包含下划线，以便识别评测名前缀: {path.name}")
    prefix = path.stem.split("_", 1)[0]
    if not prefix:
        raise ValueError(f"zip 文件名第一个下划线前的评测名不能为空: {path.name}")
    return prefix


def _build_report_data(path: Path, repeat_group_size: int | None) -> _ReportData:
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
    return _ReportData(metrics=metrics, traces=parsed.traces, zip_name=loaded.zip_name)
