# 评测日志分析使用说明

## 安装方式

本项目使用 `uv` 管理 Python 环境。

## 快速开始

```bash
uv run pytest -q
```

## Python 调用

```python
from eval_log_analyzer import analysis_html

html_path = analysis_html("tests/fixtures/mini_eval.zip")
print(html_path)
```
