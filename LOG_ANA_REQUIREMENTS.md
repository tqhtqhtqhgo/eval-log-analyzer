# LOG_ANA_REQUIREMENTS.md

## 1. 项目目标

本项目实现一个评测日志分析模块，用 Python 读取评测日志 zip 压缩包，生成一个单文件静态 HTML 报告。

报告用于分析模型评测日志，包括：

- 评测整体通过率；
- token 和耗时统计；
- retry 链路分析；
- 每个 req_id 的最终成功/失败；
- response 长度分布；
- 可点击查看原始 request/response JSON；
- 可选的 hash_id 重复评测聚合分析。

最终用户只需要调用一个 Python 函数：

```python
from eval_log_analyzer import analysis_html

html_path = analysis_html(
    zip_path="/root/C-SimpleQA_xxx.zip",
    output_html=None,
    enable_hash_repeat_chart=False,
)
print(html_path)
```

## 2. 核心入口函数

必须实现以下入口函数：

```python
def analysis_html(
    zip_path: str,
    output_html: str | None = None,
    enable_hash_repeat_chart: bool = False,
    repeat_group_size: int | None = None,
    max_attempt_columns: int = 5,
    open_browser: bool = False,
) -> str:
    """
    分析评测日志 zip，生成单个静态 HTML 文件。

    Args:
        zip_path:
            评测日志压缩包路径。

        output_html:
            输出 HTML 路径。
            如果为空，则默认输出到 zip 同目录，文件名为：
            `{zip_stem}_analysis.html`

        enable_hash_repeat_chart:
            是否启用 hash_id 重复评测聚合图。
            例如 175 条题重复 3 次得到 525 条 req_id 时，可以打开该图。

        repeat_group_size:
            每个 hash_id 预期重复次数，例如 3 或 4。
            如果为空，则根据每个 hash_id 下 req_id 数量自动推断。

        max_attempt_columns:
            重试链路表最多显示 t1..tN。
            默认显示 t1 到 t5。
            如果实际 attempt 超过该值，需要额外显示“更多”入口或在弹窗中展示完整链路。

        open_browser:
            是否生成后自动打开浏览器。

    Returns:
        生成的 HTML 文件路径。
    """
```

## 3. 技术要求

### 3.1 Python 环境

- Python 3.10+
- 使用 uv 管理环境和依赖
- 推荐依赖：
  - `openpyxl`：读取 xlsx
  - `pytest`：测试

### 3.2 前端输出

HTML 报告必须满足：

- 单个 HTML 文件；
- CSS 内联；
- JS 内联；
- 不依赖 CDN；
- 不依赖外网；
- 不需要启动服务；
- 可以直接用浏览器打开；
- 支持中文；
- 大 JSON 内容使用滚动区域；
- 表格不要直接展开超长 reasoning/content。

### 3.3 npm / JS 要求

允许开发阶段使用 npm 工具，但最终用户运行时不能依赖 npm。

最终交付必须满足：

```text
uv run python examples/run_analysis.py
```

即可生成 HTML。

## 4. 项目结构要求

项目结构如下：

```text
eval-log-analyzer/
├── AGENTS.md
├── LOG_ANA_REQUIREMENTS.md
├── LOG_ANA_DESIGN.md
├── LOG_ANA_USER.md
├── pyproject.toml
├── src/
│   └── eval_log_analyzer/
│       ├── __init__.py
│       ├── analyzer.py
│       ├── loader.py
│       ├── parser.py
│       ├── metrics.py
│       ├── render.py
│       └── static_template.py
├── tests/
│   ├── test_loader.py
│   ├── test_parser.py
│   ├── test_metrics.py
│   ├── test_render.py
│   └── fixtures/
│       └── mini_eval.zip
└── examples/
    └── run_analysis.py
```

### 4.1 `src/eval_log_analyzer/__init__.py`

导出主入口：

```python
from .analyzer import analysis_html

__all__ = ["analysis_html"]
```

### 4.2 `analyzer.py`

职责：

- 暴露 `analysis_html`；
- 校验 zip 文件存在；
- 调用 loader 读取文件；
- 调用 parser 解析 log；
- 调用 metrics 计算统计信息；
- 调用 render 输出 HTML；
- 返回 HTML 路径。

### 4.3 `loader.py`

职责：

- 解压 zip；
- 查找关键文件；
- 读取 json；
- 读取 xlsx；
- 读取 log 文本；
- 支持缺失文件降级；
- 提供明确错误信息。

### 4.4 `parser.py`

职责：

- 解析 log；
- 支持 JSONL；
- 支持多行 JSON 对象；
- 构建 req_id -> attempts；
- 判断 attempt 成功/失败；
- 提取失败原因；
- 提取 response 长度；
- 提取 hash_id。

### 4.5 `metrics.py`

职责：

- 计算基础统计；
- 计算 token 均值；
- 计算耗时均值；
- 计算 retry 统计；
- 计算 exception 分布；
- 计算 timeout / overlength / empty 数量；
- 计算 hash_id 重复评测聚合数据。

### 4.6 `render.py`

职责：

- 渲染 HTML；
- 渲染顶部统计卡片；
- 渲染重试链路表；
- 渲染 response 长度分布；
- 渲染 hash_id 聚合图；
- 注入弹窗数据；
- 生成最终单文件 HTML。

### 4.7 `static_template.py`

职责：

- 保存 HTML 模板；
- 保存内联 CSS；
- 保存内联 JS。

## 5. 输入 zip 文件格式

一个评测 zip 包中通常包含以下文件：

```text
LiveCodeBench-V6-Total-500_pangu_auto_20251121021538.log
LiveCodeBench-V6-Total-500_pangu_auto_20251121021538.xlsx
LiveCodeBench-V6-Total-500_pangu_auto_20251121021538_duplicate_result.json
LiveCodeBench-V6-Total-500_pangu_auto_20251121021538_empty_result.json
LiveCodeBench-V6-Total-500_pangu_auto_20251121021538_export_data_list.json
LiveCodeBench-V6-Total-500_pangu_auto_20251121021538_overlength_result.json
LiveCodeBench-V6-Total-500_pangu_auto_20251121021538_timeout.json
```

另一个评测可能类似：

```text
C-SimpleQA_xxx_20260412232727.log
C-SimpleQA_xxx_20260412232727.xlsx
C-SimpleQA_xxx_20260412232727_duplicate_result.json
C-SimpleQA_xxx_20260412232727_empty_result.json
C-SimpleQA_xxx_20260412232727_export_data_list.json
C-SimpleQA_xxx_20260412232727_overlength_result.json
C-SimpleQA_xxx_20260412232727_timeout.json
```

## 6. 文件识别规则

### 6.1 必选文件

至少需要：

- 一个 `.log` 文件

如果没有 `.log` 文件，直接报错。

### 6.2 推荐文件

推荐存在：

- `*_export_data_list.json`
- `.xlsx`

如果二者都不存在，则部分统计无法生成，但仍应尽量从 `.log` 生成 retry 链路和 response 长度图。

### 6.3 可选文件

以下文件可选：

- `*_empty_result.json`
- `*_overlength_result.json`
- `*_timeout.json`
- `*_duplicate_result.json`

当前阶段：

- `empty_result.json`：统计数量，展示异常摘要；
- `overlength_result.json`：统计数量，展示异常摘要；
- `timeout.json`：统计数量，展示异常摘要；
- `duplicate_result.json`：当前阶段忽略复杂分析，只记录文件存在性和条数。

## 7. log 文件格式

### 7.1 request 记录示例

```json
{
    "time": "20260412 23:27:46.009",
    "req_id": "efa9d1ea67c14e8095d1516b34857c21",
    "hash_id": "6c47c51ec0489dc9ba8e84a3764c04b2",
    "requests": {
        "model": "pangu_auto",
        "messages": [
            {
                "role": "user",
                "content": "亚当航空574号班机空难发生在哪一年的1月1日？"
            }
        ],
        "stream": true
    },
    "retry": 2,
    "timeout": 3600,
    "reasoning_contents_truncate_tokens": 65536,
    "max_content_token": 16384
}
```

### 7.2 success response 记录示例

```json
{
    "time": "20260412 23:27:58.767",
    "req_id": "efa9d1ea67c14e8095d1516b34857c21",
    "reinfer": false,
    "status_code": 200,
    "used_time": 12.75801706314087,
    "usage": {
        "prompt_tokens": 29,
        "total_tokens": 255,
        "completion_tokens": 226
    },
    "token_num": 225,
    "reasoning_token": 180,
    "content_token": 45,
    "respMsg": {
        "reasoning": "xxx",
        "content": "xxx"
    }
}
```

### 7.3 exception response 记录示例

```json
{
    "time": "20260413 00:09:41.303",
    "req_id": "f72f575bcc3d49389d52a6e721dabaa4",
    "reinfer": false,
    "error_times": 0,
    "exception": "Content OutOfMaxLength: Exceeded 16384 token length, retry",
    "usage": {
        "prompt_tokens": 28,
        "total_tokens": 17400,
        "completion_tokens": 17372
    },
    "total_chunk": 17372,
    "reasoning_chunk": 987,
    "content_chunk": 16385,
    "respMsg": {
        "reasoning": "xxx",
        "content": "xxx"
    }
}
```

## 8. log 解析规则

### 8.1 记录类型识别

request 记录：

```text
包含 requests 字段
```

response / exception 记录：

```text
包含以下任意字段：
- status_code
- exception
- respMsg
- output_reason
- usage
```

### 8.2 JSON 解析要求

`.log` 文件优先按 JSONL 解析。

如果不是严格 JSONL，需要支持多行 JSON 对象解析。

要求：

- 跳过空行；
- 遇到单条坏记录时不要让整个任务崩溃；
- 记录 parse error 数量；
- parse error 在 HTML 的异常摘要中展示。

### 8.3 attempt 构建规则

同一个 `req_id` 可能出现多次 request 和 response。

按 log 文件出现顺序扫描：

1. 每遇到一个 request 记录，创建一个新的 attempt。
2. 这个 attempt 归属于该 request 的 `req_id`。
3. 后续第一个相同 `req_id` 的 response / exception 记录，归属到最近一个尚未绑定 response 的 attempt。
4. 如果某个 response 找不到对应 request，则创建一个 orphan attempt，并标记 `missing_request=True`。
5. 如果某个 request 到日志结束仍没有 response，则该 attempt 失败，失败原因为 `missing_response`。

### 8.4 attempt 数据结构建议

可以使用 dataclass：

```python
@dataclass
class Attempt:
    req_id: str
    attempt_index: int
    request_json: dict[str, Any] | None
    response_json: dict[str, Any] | None
    success: bool
    failure_reason: str
    response_length: int
    used_time: float | None
    hash_id: str | None
    prompt: str
```

### 8.5 req_id 汇总结构建议

```python
@dataclass
class ReqTrace:
    req_id: str
    row_id: int
    hash_id: str | None
    prompt: str
    attempts: list[Attempt]
    final_success: bool
    final_attempt: Attempt | None
    final_response_length: int
```

## 9. 成功/失败判定规则

### 9.1 单次 attempt 成功条件

一个 attempt 满足以下条件才算成功：

```text
1. 有 response_json；
2. response_json.status_code == 200；
3. 没有 exception；
4. 没有 output_reason；
5. respMsg.content 或 content 非空。
```

### 9.2 单次 attempt 失败条件

满足任一条件即失败：

```text
1. 没有 response_json；
2. 有 exception；
3. 有 output_reason；
4. status_code 存在且不等于 200；
5. content 为空；
6. response 解析失败；
7. request 缺失。
```

### 9.3 失败原因优先级

失败原因按以下优先级提取：

```text
1. exception
2. output_reason
3. status_code != 200
4. content 为空
5. missing_response
6. missing_request
7. parse_error
8. unknown_error
```

### 9.4 最终成功/失败判定

同一个 `req_id` 的最终结果：

```text
如果最后一个 attempt 成功，则最终成功，显示 ✅。
否则最终失败，显示 ✖️。
```

中间失败但最后成功的情况：

```text
t1 = 🟥
t2 = 🟩
最终结果 = ✅
```

## 10. response 长度计算规则

response 长度默认使用 completion token。

优先级如下：

```text
1. response_json.usage.completion_tokens
2. response_json.usage.complete_tokens
3. response_json.token_num
4. response_json.reasoning_token + response_json.content_token
5. response_json.total_chunk
6. response_json.reasoning_chunk + response_json.content_chunk
7. len(respMsg.reasoning + respMsg.content)
8. len(reasoning + content)
9. 0
```

## 11. xlsx 文件解析规则

xlsx 表头可能类似：

| 序号 | 评测模型 | 用例集 | 请求id | 用例序号 | 模型输入 | 推理重试 | 重试是否成功 | 失败详情 | 输入长度(token) | Reasoning输出长度(token) | Content输出长度(token) | 成功推理耗时(s) | 推理总耗时(s) | 思考过程 | 模型回答 | 参考答案 | 评测结果 | 裁判模型名称 | 裁判模型回答 |
|---|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|---|---|---|---|---|

需要从 xlsx 或 export_data_list 中获取：

- 评测模型；
- 用例集；
- 总题数；
- 通过题数；
- 通过率；
- 裁判模型名称；
- 创建时间。

优先级：

```text
1. xlsx
2. export_data_list.json
3. log 文件名推断
```

如果 xlsx 不存在，不报错，使用 export_data_list.json 兜底。

## 12. export_data_list.json 解析规则

`export_data_list.json` 是数组，每个元素是一条评测结果。

示例字段：

```json
{
    "model_version": "pangu_auto_xxx",
    "dataset_name": "C-SimpleQA",
    "req_id": "c3857f4c0ff0421197ab8b112495511e",
    "case_id": "xxx",
    "case_index": "chinese_simpleqa_1036",
    "prompt": "Gboard首次发布是在哪一年？",
    "infer_retry": "否",
    "retry_success": "",
    "prompt_tokens": 20,
    "complete_tokens": 429,
    "reasoning_token": 210,
    "content_token": 218,
    "used_time": "19.50",
    "model_reasoning": "xxx",
    "model_answer": "xxx",
    "ref_answer": "2016",
    "eval_result": "FALSE",
    "judge_model": "gpt-4o-2024-08-06",
    "judge_result": "B",
    "exception": "",
    "exception_list": [],
    "time_out": 0,
    "time_out_times": 0,
    "error_use_time": 0,
    "reasoning_content": "",
    "total_used_time": 19.5
}
```

### 12.1 需要统计的字段

基于 export_data_list 统计：

- 总条数；
- `eval_result` 分布；
- 通过题数；
- 通过率；
- 平均 `complete_tokens`；
- 平均 `reasoning_token`；
- 平均 `content_token`；
- 平均 `used_time`；
- 平均 `total_used_time`；
- retry 条数；
- retry 成功条数；
- timeout 条数；
- exception 条数；
- exception 类型分布。

### 12.2 eval_result 通过判定

以下值视为通过：

```text
TRUE
True
true
1
PASS
pass
正确
```

以下值视为失败：

```text
FALSE
False
false
0
FAIL
fail
错误
```

未知值归入 `UNKNOWN`。

## 13. empty_result.json 解析规则

`empty_result.json` 可能是：

- JSON 数组；
- 多个 JSON 对象连续写入；
- JSONL。

每条记录通常包含：

```json
{
    "req_id": "xxx",
    "used_time": "0.00",
    "output_reason": "OutOfMaxLength: Exceeded 65536 token length, retry",
    "prompt": "xxx",
    "reasoning_content": "xxx",
    "content": "",
    "usage": {
        "prompt_tokens": 19,
        "complete_tokens": 65537
    }
}
```

需要统计：

- empty_result 条数；
- 按 output_reason 聚合数量；
- 展示前若干条异常样例；
- 可以点击查看完整 JSON。

## 14. overlength_result.json 解析规则

`overlength_result.json` 通常是数组。

需要统计：

- overlength 条数；
- Content OutOfMaxLength 数量；
- Reasoning OutOfMaxLength 数量；
- 其他 OutOfMaxLength 数量；
- 按 req_id 聚合；
- 展示前若干条异常样例。

## 15. timeout.json 解析规则

`timeout.json` 通常是对象：

```json
{
    "req_id_1": [
        {
            "req_time": "xxx",
            "timeout_time": "xxx",
            "error_times": 1,
            "output_reason": "xxx",
            "prompt": "xxx",
            "usage": {
                "prompt_tokens": 28,
                "completion_tokens": 17372
            },
            "reasoning": "xxx",
            "content": "xxx"
        }
    ]
}
```

需要统计：

- timeout req_id 数量；
- timeout attempt 数量；
- 按 output_reason 聚合；
- 展示前若干条异常样例。

## 16. duplicate_result.json 解析规则

当前阶段忽略复杂分析。

只需要：

- 判断文件是否存在；
- 如果存在，统计条数；
- 在页面异常摘要中显示：

```text
duplicate_result.json 已存在，当前版本暂不做 COT 循环深度分析。
```

## 17. 页面整体结构

HTML 页面建议分区：

```text
1. 页面标题
2. 评测基础信息卡片
3. 核心指标卡片
4. 异常摘要
5. 重试链路表
6. response 长度分布图
7. hash_id 重复评测聚合图，可选
8. export_data_list 明细摘要，可选
9. 原始 JSON 弹窗
```

## 18. 页面顶部基础信息

需要展示：

- 评测模型；
- 用例集；
- 创建时间；
- 总题数；
- 通过题数；
- 通过率；
- 裁判模型；
- log 文件名；
- zip 文件名。

示例：

```text
评测模型：pangu_auto_R-0403-7bv5...
用例集：C-SimpleQA
创建时间：2026-04-12 23:27:27
通过率：150 / 300，50.00%
裁判模型：gpt-4o-2024-08-06
```

## 19. 核心指标卡片

需要展示：

```text
平均 complete tokens
平均 reasoning tokens
平均 content tokens
平均 used_time
平均 total_used_time
retry req_id 数量
retry 最终成功数量
最终失败数量
empty 数量
overlength 数量
timeout 数量
```

## 20. 图表 A：重试链路表

### 20.1 表格格式

```markdown
| id | req_id | t1 | t2 | t3 | t4 | t5 | 最终结果 |
|---|---|---|---|---|---|---|---|
| 1 | f72f575bcc3d49389d52a6e721dabaa4 | 🟥 | 🟩 |  |  |  | ✅ |
| 2 | 313882a55c9a4eb78aaa4e197c27d8a7 | 🟩 |  |  |  |  | ✅ |
```

### 20.2 显示规则

- id 从 1 开始；
- 每个不同 req_id 一行；
- t1..tN 是该 req_id 的 attempt；
- 单次成功显示 🟩；
- 单次失败显示 🟥；
- 最终成功显示 ✅；
- 最终失败显示 ✖️；
- 超过 `max_attempt_columns` 的 attempt，需要显示更多提示；
- 表格支持搜索 req_id / prompt / 失败原因。

### 20.3 点击交互

点击 t1/t2/...：

- 弹窗标题显示：
  - req_id；
  - attempt 序号；
  - 成功/失败；
  - used_time；
  - response_length。
- 弹窗顶部红字显示失败原因。
- 弹窗主体显示格式化后的 response JSON。
- 允许切换查看 request JSON。

点击最终结果：

- 弹窗显示最终 attempt 的 request + response JSON。

## 21. 图表 B：response 长度分布图

### 21.1 展示格式

```text
id | response 长度
1  | ------- 2345
2  | ------------ 23124
3  | --- 32
4  | --------------- 232
```

实际 HTML 可以使用 div bar 实现。

### 21.2 规则

- 每个 req_id 一行；
- id 与重试链路表中的 id 一致；
- 长度使用最终 attempt 的 response 长度；
- 线条长度按最大 response 长度归一化；
- 最终成功用绿色线条；
- 最终失败用红色线条；
- 末尾显示实际长度数字；
- 点击行弹窗显示最终 attempt 的 response JSON；
- 鼠标 hover 显示 req_id、prompt、长度、最终结果。

## 22. 图表 C：hash_id 重复评测聚合图

该图仅当：

```python
enable_hash_repeat_chart=True
```

时显示。

### 22.1 使用场景

例如：

```text
实际评测 log 有 525 个 req_id
但只有 175 个唯一 hash_id
每个 prompt 重复评测 3 次
```

需要把 525 行聚合成 175 行。

### 22.2 聚合规则

- 从 request 记录中读取 `hash_id`；
- 相同 `hash_id` 归为一组；
- 每组包含多个 req_id；
- response 长度取该 hash_id 下所有 req_id 最终 response 长度的平均值；
- 正确次数从 export_data_list.json 中相同 req_id 的 eval_result 计算；
- 总次数优先使用 `repeat_group_size`；
- 如果 `repeat_group_size=None`，则使用该 hash_id 下 req_id 数量。

### 22.3 展示格式

```text
id | response 平均长度
1  | ------- 2345 0/3
2  | ------------ 23124 1/3
3  | --- 32 2/3
4  | --------------- 232 1/3
```

### 22.4 颜色规则

- 如果正确次数为 0，线条红色；
- 如果正确次数大于 0，线条绿色。

### 22.5 点击交互

点击一行：

- 弹窗展示该 hash_id；
- 展示所有 req_id；
- 展示每个 req_id 的最终结果；
- 展示每个 req_id 的最终 response JSON 摘要；
- 允许查看完整 JSON。

## 23. 异常摘要

页面需要展示异常摘要表：

```markdown
| 类型 | 数量 | 说明 |
|---|---:|---|
| empty_result | 12 | content 为空 |
| overlength_result | 8 | 输出超长 |
| timeout | 5 | 超时或超长重试 |
| duplicate_result | 3 | 当前版本暂不做 COT 循环深度分析 |
| parse_error | 1 | log 中存在无法解析的 JSON |
```

异常样例可以点击查看 JSON。

## 24. HTML 交互要求

### 24.1 搜索

至少支持在重试链路表中搜索：

- req_id；
- prompt；
- 失败原因。

### 24.2 弹窗

弹窗要求：

- 支持关闭；
- 支持滚动；
- 支持复制 JSON；
- JSON 使用 pretty format；
- 失败原因使用红色字体；
- 大 JSON 默认最多显示 50KB；
- 提供“显示完整 JSON”按钮。

### 24.3 页面性能

要求：

- 主表格不要直接渲染完整 reasoning/content；
- reasoning/content 只在点击弹窗时展示；
- 如果数据量很大，至少保证几千行可以打开；
- JS 数据结构尽量只保存必要字段；
- 如果保存完整 JSON，应该压缩成字符串后按需解析，或延迟渲染。

## 25. 测试要求

必须创建最小测试 zip：

```text
tests/fixtures/mini_eval.zip
```

包含：

```text
mini.log
mini.xlsx 或 mini_export_data_list.json
mini_empty_result.json
mini_overlength_result.json
mini_timeout.json
```

### 25.1 mini.log 至少覆盖

```text
case 1: 单次成功
case 2: 第一次失败，第二次成功
case 3: 最终失败，content 为空
case 4: request 存在但 response 缺失
case 5: response 存在但 request 缺失
```

### 25.2 parser 测试

必须测试：

- request 识别；
- response 识别；
- req_id 分组；
- attempt 数量；
- 成功 attempt；
- 失败 attempt；
- 失败原因；
- response 长度；
- hash_id 提取；
- 多行 JSON 解析。

### 25.3 metrics 测试

必须测试：

- 通过率；
- 平均 token；
- 平均耗时；
- retry 数量；
- retry 最终成功数量；
- final failed 数量；
- hash_id 聚合结果；
- exception 分布。

### 25.4 render 测试

必须测试：

- 生成 HTML 文件；
- HTML 包含基础信息；
- HTML 包含 req_id；
- HTML 包含重试链路表；
- HTML 包含 response 长度分布；
- HTML 不包含外部 CDN 链接；
- HTML 中存在弹窗 JS。

## 26. 验收命令

必须通过：

```bash
uv run python -m compileall src tests
uv run pytest -q
uv run python examples/run_analysis.py
```

如果 `examples/run_analysis.py` 依赖测试 fixture，则它应该默认使用：

```text
tests/fixtures/mini_eval.zip
```

## 27. pyproject.toml 建议

```toml
[project]
name = "eval-log-analyzer"
version = "0.1.0"
description = "Generate static HTML reports for evaluation logs."
requires-python = ">=3.10"
dependencies = [
    "openpyxl>=3.1.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

## 28. 开发任务拆分

Codex 开发时按以下任务顺序执行。

### 任务 1：初始化项目骨架

要求：

- 创建项目结构；
- 创建 pyproject.toml；
- 创建 `analysis_html` 空入口；
- 创建最小测试；
- 创建 `LOG_ANA_DESIGN.md`；
- 创建 `LOG_ANA_USER.md`；
- 运行 compileall 和 pytest；
- git commit。

### 任务 2：实现 zip 和文件发现

要求：

- 支持 zip 解压；
- 自动发现 log/xlsx/json 文件；
- 读取 JSON；
- 读取 log 文本；
- 添加测试；
- 更新设计文档；
- 运行测试；
- git commit。

### 任务 3：实现 log parser

要求：

- 支持 JSONL；
- 支持多行 JSON；
- 构建 ReqTrace 和 Attempt；
- 判定 success/failure；
- 提取 failure_reason；
- 提取 response_length；
- 添加测试；
- 运行测试；
- git commit。

### 任务 4：实现 export_data_list 指标

要求：

- 计算总数；
- 计算通过数；
- 计算通过率；
- 计算 token 均值；
- 计算耗时均值；
- 计算 retry 统计；
- 添加测试；
- 运行测试；
- git commit。

### 任务 5：实现基础 HTML

要求：

- 顶部基础信息卡片；
- 核心指标卡片；
- 异常摘要；
- 单文件 HTML；
- 不依赖 CDN；
- 添加测试；
- 运行测试；
- git commit。

### 任务 6：实现重试链路表

要求：

- t1..tN；
- 🟩 / 🟥；
- ✅ / ✖️；
- 点击弹窗查看 JSON；
- 搜索 req_id / prompt / 失败原因；
- 添加测试；
- 运行测试；
- git commit。

### 任务 7：实现 response 长度分布图

要求：

- 每个 req_id 一行；
- 成功绿色；
- 失败红色；
- 长度归一化；
- 点击弹窗；
- 添加测试；
- 运行测试；
- git commit。

### 任务 8：实现 hash_id 重复评测聚合图

要求：

- 仅在 `enable_hash_repeat_chart=True` 时显示；
- 按 hash_id 聚合；
- 计算平均 response 长度；
- 计算 x/y 正确次数；
- 点击弹窗展示组内 req_id；
- 添加测试；
- 运行测试；
- git commit。

### 任务 9：最终文档和打磨

要求：

- 完善 `LOG_ANA_DESIGN.md`；
- 完善 `LOG_ANA_USER.md`；
- 确认 examples 可运行；
- 确认全部测试通过；
- 最终 commit。

## 29. 非目标

当前版本不做：

- Web 服务；
- 数据库；
- 用户登录；
- 在线上传；
- 多评测横向对比；
- 复杂 COT 循环检测；
- duplicate_result 深度分析；
- 远程文件下载；
- CDN 图表库；
- React/Vue 前端工程。

## 30. 最终交付标准

最终交付必须满足：

1. 可以通过 `analysis_html(zip_path)` 生成 HTML；
2. HTML 可以直接用浏览器打开；
3. 页面包含基础统计；
4. 页面包含重试链路表；
5. 页面包含 response 长度分布；
6. 可选显示 hash_id 重复评测聚合图；
7. 点击表格可以查看格式化 JSON；
8. 所有测试通过；
9. 有设计文档；
10. 有使用文档；
11. git 历史中每个功能都有独立 commit。
