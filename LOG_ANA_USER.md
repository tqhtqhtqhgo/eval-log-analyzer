# 评测日志分析使用说明

## 安装方式

项目使用 Python 3.10+ 和 `uv`。在项目根目录执行命令即可自动创建环境并安装依赖。

```bash
uv run pytest -q
```

## uv 环境初始化

```bash
uv sync
uv run python -m compileall src tests
uv run pytest -q
```

## 命令行示例

示例脚本默认读取 `tests/fixtures/mini_eval.zip`，并在同目录生成 `mini_eval_analysis.html`。

```bash
uv run python examples/run_analysis.py
```

## Python 函数调用示例

```python
from eval_log_analyzer import analysis_html

html_path = analysis_html(
    zip_path="tests/fixtures/mini_eval.zip",
    output_html=None,
    enable_hash_repeat_chart=True,
    repeat_group_size=None,
    max_attempt_columns=5,
    open_browser=False,
)
print(html_path)
```

## 输入 zip 文件要求

压缩包中至少需要一个 `.log` 文件。推荐同时包含：

- `*_export_data_list.json`
- `.xlsx`

可选文件：

- `*_empty_result.json`
- `*_overlength_result.json`
- `*_timeout.json`
- `*_duplicate_result.json`

缺少 xlsx 或 export 时不会报错，报告会尽量从 log 中生成 retry 链路和 response 长度图。缺少 `.log` 会报错。

## 输出 HTML 说明

默认输出到 zip 同目录，文件名为 `{zip_stem}_analysis.html`。HTML 是单个静态文件，包含内联 CSS 和 JS，不使用 CDN，不需要启动服务，可以直接用浏览器打开。

## 页面功能

基础信息区展示评测模型、用例集、创建时间、总题数、通过题数、通过率、裁判模型、log 文件名和 zip 文件名。

核心指标区展示平均 complete/reasoning/content tokens、平均 used_time、平均 total_used_time、retry req_id 数量、retry 最终成功数量、最终失败数量、empty 数量、overlength 数量和 timeout 数量。

重试链路表中每个 req_id 一行，t1、t2 等列展示每次 attempt 的状态。点击状态符号或最终结果可以查看该 attempt 的 request/response JSON；搜索框支持按 req_id、prompt、失败原因过滤。

response 长度分布图按 req_id 展示最终 attempt 的 response 长度。绿色表示最终成功，红色表示最终失败；点击行可以查看最终 attempt 的 JSON。

调用 `analysis_html(..., enable_hash_repeat_chart=True)` 时会显示 hash_id 聚合图。每行展示平均 response 长度和 `正确次数/总次数`，总次数可用 `repeat_group_size` 指定。

## 常见问题

### 没有 xlsx 可以运行吗？

可以。缺少 xlsx 时会使用 export_data_list 或 log 文件名兜底。

### 没有 export_data_list 可以运行吗？

可以，但通过率、token 均值和部分基础信息可能为空或 0。

### HTML 为什么比较大？

报告是单文件静态 HTML，会内联必要的 CSS、JS 和弹窗 JSON 数据。主表不会展开 reasoning/content，大字段只在弹窗中按需查看。

### duplicate_result.json 是否会做循环检测？

当前版本不会。页面只展示该文件存在性和条数。
