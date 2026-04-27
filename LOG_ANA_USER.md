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

## 重试链路表

重试链路表中每个 req_id 一行，t1、t2 等列展示每次 attempt 的状态。点击状态符号或最终结果可以查看该 attempt 的 request/response JSON；搜索框支持按 req_id、prompt、失败原因过滤。

## response 长度分布图

response 长度分布图按 req_id 展示最终 attempt 的 response 长度。绿色表示最终成功，红色表示最终失败；点击行可以查看最终 attempt 的 JSON。

## hash_id 重复评测聚合图

调用 `analysis_html(..., enable_hash_repeat_chart=True)` 时会显示 hash_id 聚合图。每行展示平均 response 长度和 `正确次数/总次数`，总次数可用 `repeat_group_size` 指定。
