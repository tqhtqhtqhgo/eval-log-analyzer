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
