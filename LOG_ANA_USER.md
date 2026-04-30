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

基础信息区展示评测模型、用例集、创建时间、总题数、通过题数、通过率、裁判模型、log 文件名和 zip 文件名。通过题数和通过率根据 `export_data_list.json` 中每个对象的 `eval_result` 判断，支持 `"True"` / `"False"` 字符串。

核心指标区展示平均 complete/reasoning/content tokens、平均 used_time、平均 total_used_time、retry req_id 数量、retry 最终成功数量、最终链路失败数量和推理成功题目数量（不含链路失败）。complete/reasoning/content tokens、used_time 和 total_used_time 会保留平均值，并在核心指标下方单独展示竖向箱线图，标出 min、1/4 分位、3/4 分位、中位数和 max。complete/reasoning/content tokens 还会额外在“tokens推理成功数据”中展示过滤 0 后的箱线图，便于查看有效 token 数据分布。所有箱线图都使用 0 到 120k 的固定纵向标尺。

异常摘要区从 `export_data_list.json` 的 `exception` / `exception_list` 文本统计关键异常：`Content OutOfMaxLength` 统计 exception 以该字符串开头的条数；`timeout` 统计 exception 以 `Streaming parse timeout` 开头的条数；`HTTP Connection 异常` 统计 exception 包含 `HTTPConnection` 的条数。empty、overlength、timeout 文件当前不再进入核心指标或异常摘要。

重试链路最终状态圆环图根据重试链路表的最终链路和 `export_data_list.json` 的 `eval_result` 绘制，分为链路通过且做对、链路通过但做错、链路失败三类。

重试链路表位于页面最底部，每个 req_id 一行，按本条数据的 `hash_id` 排序，并增加 `hash_id` 列。t1、t2 等列展示每次 attempt 的状态，最后一列展示该题评测结果是做对还是做错，表格使用紧凑行高。多次重试中只要有一次 attempt 成功，最终链路就按成功展示，并打开那次成功 attempt 的 JSON。点击状态符号或最终链路结果可以查看该 attempt 的 request/response JSON；搜索框支持按 req_id、hash_id、prompt、失败原因过滤。“只看过程失败”按钮会筛出过程中出现失败的题，包括最终失败和重试后成功的题；“只看做错”按钮会筛出评测结果为做错的题；“只看链路成功”按钮会筛出最终链路成功的题；“只看链路失败”按钮会筛出最终链路失败的题。

重试链路表和 response 长度分布图都按本条数据的 `hash_id` 排序，因此多次评测中同一题的位置会尽量保持一致。

response 长度分布图按 req_id 展示最终 attempt 的 response 长度，使用紧凑字体和行高。做对/做错只根据 `export_data_list.json` 的 `eval_result` 判断：绿色表示做对，红色表示推理成功但评测做错，橙色表示推理失败或异常且最终评测做错；点击行可以查看最终 attempt 的 JSON。长度条以 120k token 为满刻度，超过 120k 按满刻度显示；图上方会显示 0 到 120k 的标尺，每 10k 一个刻度。

response 长度点阵图中每道题是一个点，x 轴是 response 长度，y 轴按稳定 hash 做轻微错位以减少重叠，图高为原始点阵图高度的 3 倍。链路失败且 `eval_result=False` 的点显示为橙色。把光标放在点上可以看到 id、req_id、hash、长度和评测结果，点击点可以查看最终 attempt 的 JSON。点阵图下方会排除推理失败题目，再分别展示做对题目和做错题目的 response 长度箱线图，并显示这两个图的总样本数。

`analysis_html(..., enable_hash_repeat_chart=True)` 参数当前保留兼容，但页面不再显示 hash_id 聚合紧凑分布图和 hash_id 聚合图。

## 常见问题

### 没有 xlsx 可以运行吗？

可以。缺少 xlsx 时会使用 export_data_list 或 log 文件名兜底。

### 没有 export_data_list 可以运行吗？

可以，但通过率、token 均值和部分基础信息可能为空或 0。

### HTML 为什么比较大？

报告是单文件静态 HTML，会内联必要的 CSS、JS 和弹窗 JSON 数据。主表不会展开 reasoning/content，大字段只在弹窗中按需查看。

### duplicate_result.json 是否会做循环检测？

当前版本不会。页面只展示该文件存在性和条数。
