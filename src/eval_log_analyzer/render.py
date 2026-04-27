from __future__ import annotations

from pathlib import Path


def render_html(output_html: str) -> str:
    """渲染 HTML，骨架阶段写入最小页面。"""
    Path(output_html).write_text("<!doctype html><html><body></body></html>", encoding="utf-8")
    return output_html
