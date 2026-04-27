# 评测日志分析使用说明

## 安装方式

本项目使用 `uv` 管理 Python 环境。

## 快速开始

```bash
uv run pytest -q
```

## 输入 zip 文件要求

压缩包中至少需要一个 `.log` 文件。`*_export_data_list.json`、`.xlsx`、`*_empty_result.json`、`*_overlength_result.json`、`*_timeout.json`、`*_duplicate_result.json` 都是可选文件；缺失时报告会降级展示已有信息。

## Python 调用

```python
from eval_log_analyzer import analysis_html

html_path = analysis_html("tests/fixtures/mini_eval.zip")
print(html_path)
```

## 输出 HTML 说明

默认输出到 zip 同目录，文件名为 `{zip_stem}_analysis.html`。HTML 是单个静态文件，包含内联 CSS 和 JS，可以直接用浏览器打开，不需要启动服务。
