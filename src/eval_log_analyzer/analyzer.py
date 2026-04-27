from __future__ import annotations

from pathlib import Path


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
    target.write_text("<!doctype html><html><body>eval log analyzer</body></html>", encoding="utf-8")
    return str(target)
