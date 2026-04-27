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

初始骨架阶段仅提供模块边界，后续任务逐步补齐数据流、解析规则和渲染规则。
