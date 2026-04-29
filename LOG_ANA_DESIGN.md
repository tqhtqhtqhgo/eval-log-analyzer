# 评测日志分析设计

## 项目目标

本项目读取评测日志 zip 压缩包，生成一个单文件静态 HTML 报告。报告用于查看评测基础信息、通过率、token 和耗时统计、retry 链路、最终成功/失败、response 长度分布，以及可选的 hash_id 重复评测聚合。

## 模块架构

- `analyzer.py`：对外入口，校验输入并串联 loader、parser、metrics、render。
- `loader.py`：直接从 zip 内发现关键文件，读取 log、JSON 和 xlsx。
- `parser.py`：解析 log，构建 `ReqTrace` 和 `Attempt`。
- `metrics.py`：计算 export 指标、trace 指标、异常摘要和 hash_id 聚合。
- `render.py`：生成单文件 HTML，渲染卡片、表格、图表和弹窗。
- `static_template.py`：保存内联 HTML/CSS/JS 模板。

## 数据流

`analysis_html(zip_path)` 校验 zip 路径后调用 `load_eval_zip`。loader 不落盘解压，直接从 zip 内读取必选 `.log` 和可选 json/xlsx 文件，避免长路径问题。parser 消费 log 文本生成 trace；metrics 消费 trace、export、异常文件生成统计；render 将统计和 trace 写入单个 HTML。

## 文件发现和读取规则

- `.log` 是必选文件，缺失时抛出明确异常。
- `.xlsx` 和 `*_export_data_list.json` 缺失时不报错，相关指标降级为空或 0。
- 支持 `*_empty_result.json`、`*_overlength_result.json`、`*_timeout.json`、`*_duplicate_result.json`。
- JSON 读取支持普通 JSON、JSON 数组、JSONL 和连续 JSON 对象。
- xlsx 使用首行作为表头读取为字典列表。
- `duplicate_result.json` 当前只记录存在性和条数，不做 COT 循环深度分析。

## log 解析规则

`.log` 优先逐行按 JSONL 解析。遇到多行 JSON 对象时，按括号深度合并后解析。单条坏记录不会终止整体流程，只累加 `parse_error_count`。

request 记录：包含 `requests` 字段。

response / exception 记录：包含 `status_code`、`exception`、`respMsg`、`output_reason`、`usage` 任一字段。

## attempt 成功/失败判定规则

attempt 成功必须同时满足：

- 有 response；
- `status_code == 200`；
- 没有 `exception`；
- 没有 `output_reason`；
- `respMsg.content` 或顶层 `content` 非空；
- request 未缺失。

失败原因按优先级提取：`exception`、`output_reason`、非 200 `status_code`、content 为空、`missing_response`、`missing_request`、`unknown_error`。

## retry 链路构建方式

按 log 出现顺序扫描。每遇到 request 创建一个新的 attempt；后续第一个相同 req_id 的 response/exception 绑定到最近尚未绑定 response 的 attempt。找不到 request 的 response 会创建 orphan attempt 并标记 `missing_request`；日志结束仍没有 response 的 request 标记 `missing_response`。同一 req_id 的最终结果由最后一个 attempt 决定。

## response 长度计算规则

按以下优先级取值：

1. `response_json.usage.completion_tokens`
2. `response_json.usage.complete_tokens`
3. `response_json.token_num`
4. `response_json.reasoning_token + response_json.content_token`
5. `response_json.total_chunk`
6. `response_json.reasoning_chunk + response_json.content_chunk`
7. `len(respMsg.reasoning + respMsg.content)`
8. `len(reasoning + content)`
9. `0`

## 指标统计规则

export 侧统计总条数、通过数、通过率、`eval_result` 分布、平均 complete/reasoning/content tokens、平均 used_time、平均 total_used_time、retry 条数、retry 成功条数、timeout 条数、exception 条数和 exception 类型分布。

核心指标中的 complete tokens、reasoning tokens、content tokens、used_time 同时计算箱线图数据，包含 count、min、q1、median、q3、max 和平均值。页面保留平均值展示，并用箱线图补充展示全量数据分布。

trace 侧统计 req_id 总数、最终成功数、最终失败数、retry req_id 数量、retry 最终成功数量和 parse error 数量。

empty、overlength、timeout、duplicate 文件做基础摘要。timeout 同时统计 req_id 数量和 attempt 数量。

## hash_id 聚合规则

重复评测聚合不直接信任 request 中的 `hash_id`。真实日志中可能出现同一 user message 但 hash_id 不同的情况，因此当前实现对解析出的 prompt 做空白规范化后计算 md5，作为聚合用的稳定 hash_id。prompt 为空时才退回使用日志中的 `hash_id`，仍为空则退回 `req_id`。

每组 response 长度取组内所有 req_id 最终 response_length 的平均值。正确次数从 `export_data_list.json` 中相同 req_id 的 `eval_result` 计算。总次数优先使用 `repeat_group_size`，为空时使用该聚合 hash 下 req_id 数量。

hash_id 重复评测聚合图按聚合 hash 升序排序，因此不同评测报告中同一题会尽量出现在同一行。

## HTML 渲染设计

报告输出为单个 HTML 文件，CSS 和 JS 全部内联，不加载 CDN 或远程资源，可以直接用浏览器打开。

页面包含：

- 基础信息卡片：评测模型、用例集、创建时间、总题数、通过题数、通过率、裁判模型、log 文件名、zip 文件名。
- 核心指标卡片：平均 token、平均耗时、retry、最终失败、empty、overlength、timeout；complete tokens、reasoning tokens、content tokens、used_time 同时显示箱线图。
- 异常摘要表：empty、overlength、timeout、duplicate、parse_error、export_exception。
- 重试链路表：每个 req_id 一行，t1..tN 仅显示状态符号，不在主表展开 reasoning/content；提供“只看过程失败”按钮筛选最终失败和重试成功这类过程中出现失败的题；最后一列展示 `export_data_list.json` 中评测结果是做对还是做错。
- response 长度紧凑分布图：按 user prompt 稳定 hash 排序，每个 req_id 对应一条紧凑横线，不直接标注长度，hover 显示 id、req_id、长度和评测结果。
- response 长度分布图：与重试链路表使用相同稳定排序和序号。绿色表示做对，红色表示推理成功但评测做错，橙色表示推理失败或异常且最终评测做错。
- hash_id 重复评测聚合紧凑分布图和聚合图：仅在 `enable_hash_repeat_chart=True` 时显示，按聚合 hash 升序排序。
- JSON 弹窗：点击 attempt、最终结果或图表行时展示 request/response，超过 50KB 默认截断，可显示完整 JSON 和复制。

除重试链路表外，response 长度图和 hash_id 聚合长度图都使用固定 120k token 作为满刻度，不再按当前报告最大值归一化。超过 120k 的长度按满刻度绘制。

## 格式歧义假设

- 创建时间优先从 export 行的 `created_time` 或 `time` 字段读取；缺失时展示为空。
- xlsx 表头按原始中文列名读取，当前仅用于基础信息兜底。
- export 中 `infer_retry` 不为“否/False/0/空”即视为 retry。
- export 中 `retry_success` 为“是/TRUE/1/PASS/pass”即视为 retry 成功。
