# AGENTS.md

## 项目目标

本项目实现一个评测日志分析模块，用 Python 读取评测日志压缩包，生成一个单文件静态 HTML 报告。

核心入口函数：

```python
def analysis_html(
    zip_path: str,
    output_html: str | None = None,
    enable_hash_repeat_chart: bool = False,
    repeat_group_size: int | None = None,
    max_attempt_columns: int = 5,
    open_browser: bool = False,
) -> str:
    ...
```

`analysis_html` 返回生成的 HTML 文件路径。

## 工作方式

开发必须按照“小步实现、小步验证、小步提交”的方式进行。

每完成一个相对独立的功能，必须：

1. 运行语法检查；
2. 运行相关测试；
3. 确认示例脚本可以生成 HTML；
4. 使用 git commit 提交；
5. commit message 使用中文，并说明本次改动内容。

不要一次性实现所有功能。优先保证每一步都能运行、能测试、能回滚。

## 技术栈要求

- 使用 Python 3.10+
- 使用 uv 管理依赖和运行环境
- 不引入服务端 Web 框架
- 输出必须是单个静态 HTML 文件
- HTML 中允许内联 CSS 和 JS
- 不依赖 CDN
- 不依赖运行时 npm
- 如果临时使用 npm 或前端工具，最终产物必须已经编译/内联，用户运行时只依赖 uv 的 Python 环境

## 推荐项目结构

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

## 模块职责

### `analyzer.py`

对外入口模块。

必须提供：

```python
analysis_html(...)
```

职责：

- 校验输入 zip 路径；
- 调用 loader 读取文件；
- 调用 parser 解析日志；
- 调用 metrics 计算统计指标；
- 调用 render 生成 HTML；
- 返回生成的 HTML 路径。

### `loader.py`

负责输入文件读取。

职责：

- 解压 zip 到临时目录；
- 自动识别 `.log`、`.xlsx`、`*_export_data_list.json`、`*_empty_result.json`、`*_overlength_result.json`、`*_timeout.json`、`*_duplicate_result.json`；
- 读取 JSON / JSONL / xlsx；
- 对缺失文件提供清晰错误或降级逻辑；
- 结束后清理临时目录。

### `parser.py`

负责 log 解析和 request/response 配对。

职责：

- 支持 JSONL；
- 支持多行 JSON 对象的容错解析；
- 识别 request 记录；
- 识别 response / exception 记录；
- 按 `req_id` 构建 attempt 链路；
- 判定每次 attempt 成功或失败；
- 提取失败原因；
- 提取 response 长度。

### `metrics.py`

负责统计指标。

职责：

- 评测基础信息；
- 通过数、总数、通过率；
- token 均值；
- 耗时均值；
- retry 统计；
- timeout 统计；
- exception 分布；
- hash_id 重复评测聚合统计。

### `render.py`

负责生成 HTML。

职责：

- 渲染汇总卡片；
- 渲染重试链路表；
- 渲染 response 长度分布图；
- 渲染 hash_id 重复评测聚合图；
- 注入内联 CSS / JS；
- 生成单文件 HTML。

### `static_template.py`

负责保存 HTML/CSS/JS 模板字符串。

要求：

- 不依赖外部 CDN；
- 不加载远程 JS；
- 页面可以直接用浏览器打开；
- 弹窗、搜索、折叠、复制等交互都用内联 JS 实现。

## 代码质量要求

- 所有 public 函数必须有类型注解；
- 关键逻辑必须有中文注释；
- 解析逻辑不要写成一个大函数；
- 不要把真实大日志提交到仓库；
- 不要把 reasoning/content 大字段直接展开在页面表格里；
- 大字段只在弹窗中按需展示；
- HTML 中的大 JSON 默认使用滚动区域；
- 对异常输入要给出明确错误信息；
- 单元测试优先覆盖解析和统计逻辑。

## 必须维护的文档

### `LOG_ANA_DESIGN.md`

设计文档，至少包含：

- 项目目标；
- 模块架构；
- 数据流；
- log 解析规则；
- attempt 成功/失败判定规则；
- retry 链路构建方式；
- response 长度计算规则；
- hash_id 聚合规则；
- HTML 渲染设计。

### `LOG_ANA_USER.md`

使用文档，至少包含：

- 安装方式；
- uv 环境初始化；
- 命令行示例；
- Python 函数调用示例；
- 输入 zip 文件要求；
- 输出 HTML 说明；
- 常见问题。

## 验证命令

优先使用以下命令：

```bash
uv run python -m compileall src tests
uv run pytest -q
uv run python examples/run_analysis.py
```

如果测试还没写完，至少运行：

```bash
uv run python -m compileall src
```

## git commit 要求

每完成一个独立功能并验证通过后，必须 commit。

commit message 示例：

```text
初始化评测日志分析项目结构
实现 zip 文件发现和读取逻辑
实现 log request response 配对解析
实现重试链路 HTML 表格
实现 response 长度分布图
实现 hash_id 重复评测聚合图
完善使用文档和设计文档
```

## 禁止事项

- 不要依赖外网资源；
- 不要使用 CDN；
- 不要要求用户启动服务才能查看报告；
- 不要把真实大日志提交到仓库；
- 不要在没有运行验证命令的情况下 commit；
- 不要把多个大功能混在一个 commit 里；
- 不要在当前阶段实现复杂的 duplicate_result 循环检测；
- 不要把全部 reasoning/content 展开到主页面表格中。

## 当前阶段忽略项

`duplicate_result.json` 当前阶段只读取文件存在性，不做复杂分析。

后续可以单独扩展 COT 循环检测模块。
