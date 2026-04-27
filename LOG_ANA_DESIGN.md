# 评测日志分析设计

## 项目目标

读取评测日志 zip 压缩包，生成一个可以直接用浏览器打开的单文件静态 HTML 报告。

## 模块架构

- `analyzer.py`：对外入口，串联读取、解析、统计和渲染。
- `loader.py`：负责 zip 解压、文件发现和文件读取。
- `parser.py`：负责 log 解析和 request/response attempt 链路构建。
- `metrics.py`：负责汇总统计指标。
- `render.py`：负责生成最终 HTML。
- `static_template.py`：保存内联 HTML/CSS/JS 模板。

## 当前假设

## 数据流

`analysis_html` 接收 zip 路径，`loader` 解压到临时目录并发现关键文件。`.log` 是必选文件；xlsx、export、empty、overlength、timeout、duplicate 均为可选文件。读取完成后临时目录自动清理，后续模块只消费内存中的结构化数据。

## 文件读取规则

- `.log` 按 UTF-8 文本读取，遇到非法字符使用替换策略。
- JSON 文件支持普通 JSON、JSON 数组、JSONL 和多个 JSON 对象连续写入。
- `.xlsx` 缺失时不报错；存在时用首行作为表头读取为字典列表。
- `duplicate_result.json` 当前阶段只记录存在性和条数，不做复杂循环检测。

## log 解析规则

`.log` 优先逐行按 JSONL 解析；遇到多行 JSON 对象时用括号深度合并后解析。坏记录不终止整体流程，只增加 `parse_error_count`。

request 记录通过 `requests` 字段识别。response / exception 记录通过 `status_code`、`exception`、`respMsg`、`output_reason`、`usage` 任一字段识别。

## attempt 成功/失败判定规则

attempt 成功必须同时满足：有 response、`status_code == 200`、没有 `exception`、没有 `output_reason`、`respMsg.content` 或顶层 `content` 非空。否则判定失败。

失败原因优先级为：`exception`、`output_reason`、非 200 `status_code`、content 为空、`missing_response`、`missing_request`、`unknown_error`。

## retry 链路构建方式

按 log 出现顺序扫描。每个 request 创建新 attempt；后续第一个同 req_id response 绑定到最近未绑定 response 的 attempt。没有 request 的 response 会创建 orphan attempt 并标记 `missing_request`；日志结束仍无 response 的 request 标记 `missing_response`。

## response 长度计算规则

按需求优先级读取 `usage.completion_tokens`、`usage.complete_tokens`、`token_num`、`reasoning_token + content_token`、`total_chunk`、`reasoning_chunk + content_chunk`，最后退化为 response 文本长度。

## 指标统计规则

`metrics` 同时消费 `export_data_list` 和 log trace。export 侧统计总数、通过数、通过率、`eval_result` 分布、token 均值、耗时均值、retry、timeout 和 exception 分布。log trace 侧统计 req_id 总数、最终成功/失败、retry req_id、retry 最终成功和 parse error。

empty、overlength、timeout、duplicate 文件只做基础摘要。duplicate 当前仅展示存在性和条数，不做 COT 循环深度分析。

## hash_id 聚合规则

按 request 中的 `hash_id` 分组，组内 response 长度取最终 attempt 的平均值。正确次数来自 export 中同 req_id 的 `eval_result`，总次数优先使用 `repeat_group_size`，为空时使用该 hash_id 下 req_id 数量。

## HTML 渲染设计

报告输出为单个 HTML 文件，CSS 和 JS 全部内联，不加载 CDN 或远程资源。基础阶段包含顶部基础信息卡片、核心指标卡片和异常摘要表。主页面只展示摘要字段，大 JSON 后续通过弹窗按需展示。
