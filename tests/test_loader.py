import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

from eval_log_analyzer.loader import LoaderError, load_eval_zip, read_json_flexible, read_json_flexible_text


def test_load_eval_zip_discovers_files(tmp_path: Path) -> None:
    zip_path = tmp_path / "case.zip"
    with ZipFile(zip_path, "w") as zf:
        zf.writestr("nested/case.log", "{}\n")
        zf.writestr("nested/case_export_data_list.json", json.dumps([{"req_id": "r1"}]))
        zf.writestr("nested/case_empty_result.json", "{\"req_id\":\"r2\"}\n{\"req_id\":\"r3\"}")
        zf.writestr("nested/case_overlength_result.json", "[]")
        zf.writestr("nested/case_timeout.json", "{}")
        zf.writestr("nested/case_duplicate_result.json", "[]")

    loaded = load_eval_zip(zip_path)

    assert loaded.log_name == "case.log"
    assert loaded.xlsx_rows is None
    assert loaded.export_data_list == [{"req_id": "r1"}]
    assert len(loaded.empty_result) == 2
    assert loaded.discovered_files["xlsx"] is None
    assert loaded.discovered_files["log"] == "case.log"


def test_load_eval_zip_reads_xlsx_without_extracting(tmp_path: Path) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["req_id", "score"])
    sheet.append(["r1", 1])
    buffer = BytesIO()
    workbook.save(buffer)

    zip_path = tmp_path / "case.zip"
    with ZipFile(zip_path, "w") as zf:
        zf.writestr("logs/case.log", "{}\n")
        zf.writestr("data/case.xlsx", buffer.getvalue())

    loaded = load_eval_zip(zip_path)

    assert loaded.xlsx_name == "case.xlsx"
    assert loaded.xlsx_rows == [{"req_id": "r1", "score": 1}]


def test_load_eval_zip_requires_log(tmp_path: Path) -> None:
    zip_path = tmp_path / "case.zip"
    with ZipFile(zip_path, "w") as zf:
        zf.writestr("case_export_data_list.json", "[]")

    with pytest.raises(LoaderError, match=".log"):
        load_eval_zip(zip_path)


def test_read_json_flexible_supports_jsonl_and_consecutive_objects(tmp_path: Path) -> None:
    jsonl = tmp_path / "a.json"
    jsonl.write_text("{\"a\": 1}\n{\"a\": 2}\n", encoding="utf-8")
    consecutive = tmp_path / "b.json"
    consecutive.write_text("{\"b\": 1}{\"b\": 2}", encoding="utf-8")

    assert read_json_flexible(jsonl) == [{"a": 1}, {"a": 2}]
    assert read_json_flexible(consecutive) == [{"b": 1}, {"b": 2}]


def test_read_json_flexible_text_reports_clear_error() -> None:
    with pytest.raises(LoaderError, match="JSON 文本解析失败"):
        read_json_flexible_text("{bad json")
