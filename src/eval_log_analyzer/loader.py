from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zipfile import ZipFile


class LoaderError(ValueError):
    """输入压缩包读取失败。"""


@dataclass
class LoadedEvalLog:
    zip_path: Path
    zip_name: str
    log_name: str
    log_text: str
    xlsx_name: str | None
    xlsx_rows: list[dict[str, Any]] | None
    export_data_list: list[Any] | None
    empty_result: Any | None
    overlength_result: Any | None
    timeout_result: Any | None
    duplicate_result: Any | None
    discovered_files: dict[str, str | None]


def load_eval_zip(zip_path: str | Path) -> LoadedEvalLog:
    """解压并读取评测 zip 中的关键文件。"""
    source = Path(zip_path)
    if not source.exists():
        raise FileNotFoundError(f"zip 文件不存在: {source}")
    if not source.is_file():
        raise LoaderError(f"zip 路径不是文件: {source}")

    with tempfile.TemporaryDirectory(prefix="eval-log-analyzer-") as tmp:
        tmp_dir = Path(tmp)
        with ZipFile(source) as zf:
            zf.extractall(tmp_dir)
        files = [p for p in tmp_dir.rglob("*") if p.is_file()]
        discovered = _discover_files(files)
        log_path = discovered["log"]
        if log_path is None:
            raise LoaderError("zip 中未发现 .log 文件，无法分析 retry 链路")

        log_file = Path(log_path)
        export_path = _optional_path(discovered["export_data_list"])
        empty_path = _optional_path(discovered["empty_result"])
        overlength_path = _optional_path(discovered["overlength_result"])
        timeout_path = _optional_path(discovered["timeout"])
        duplicate_path = _optional_path(discovered["duplicate_result"])
        xlsx_path = _optional_path(discovered["xlsx"])

        return LoadedEvalLog(
            zip_path=source,
            zip_name=source.name,
            log_name=log_file.name,
            log_text=log_file.read_text(encoding="utf-8", errors="replace"),
            xlsx_name=xlsx_path.name if xlsx_path else None,
            xlsx_rows=read_xlsx(xlsx_path) if xlsx_path else None,
            export_data_list=_as_list(read_json_flexible(export_path)) if export_path else None,
            empty_result=read_json_flexible(empty_path) if empty_path else None,
            overlength_result=read_json_flexible(overlength_path) if overlength_path else None,
            timeout_result=read_json_flexible(timeout_path) if timeout_path else None,
            duplicate_result=read_json_flexible(duplicate_path) if duplicate_path else None,
            discovered_files={k: (Path(v).name if v else None) for k, v in discovered.items()},
        )


def read_json_flexible(path: str | Path) -> Any:
    """读取普通 JSON、JSONL 或连续 JSON 对象。"""
    text = Path(path).read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return []
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    jsonl_items: list[Any] = []
    jsonl_ok = True
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            jsonl_items.append(json.loads(line))
        except json.JSONDecodeError:
            jsonl_ok = False
            break
    if jsonl_ok and jsonl_items:
        return jsonl_items

    decoder = json.JSONDecoder()
    index = 0
    items = []
    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            break
        try:
            item, end = decoder.raw_decode(text, index)
        except json.JSONDecodeError as exc:
            raise LoaderError(f"JSON 文件解析失败: {path}: {exc}") from exc
        items.append(item)
        index = end
    return items


def read_xlsx(path: str | Path) -> list[dict[str, Any]]:
    """读取 xlsx 首行表头为字典列表；缺少 openpyxl 时给出明确错误。"""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover
        raise LoaderError("读取 xlsx 需要安装 openpyxl") from exc

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(value) if value is not None else "" for value in rows[0]]
    result = []
    for row in rows[1:]:
        result.append({headers[i]: row[i] if i < len(row) else None for i in range(len(headers))})
    return result


def _discover_files(files: list[Path]) -> dict[str, str | None]:
    def first_match(predicate: object) -> str | None:
        for file_path in sorted(files):
            if predicate(file_path):
                return str(file_path)
        return None

    return {
        "log": first_match(lambda p: p.suffix == ".log"),
        "xlsx": first_match(lambda p: p.suffix == ".xlsx"),
        "export_data_list": first_match(lambda p: p.name.endswith("_export_data_list.json")),
        "empty_result": first_match(lambda p: p.name.endswith("_empty_result.json")),
        "overlength_result": first_match(lambda p: p.name.endswith("_overlength_result.json")),
        "timeout": first_match(lambda p: p.name.endswith("_timeout.json")),
        "duplicate_result": first_match(lambda p: p.name.endswith("_duplicate_result.json")),
    }


def _optional_path(value: str | None) -> Path | None:
    return Path(value) if value else None


def _as_list(value: Any) -> list[Any] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return value
    return [value]
