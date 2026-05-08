from pathlib import Path
from shutil import copyfile
from zipfile import ZipFile

import pytest

from eval_log_analyzer import analysis_html, compare_analysis_html


def test_analysis_html_minimal(tmp_path: Path) -> None:
    zip_path = tmp_path / "mini.zip"
    with ZipFile(zip_path, "w") as zf:
        zf.writestr("mini.log", "")

    output = analysis_html(str(zip_path), str(tmp_path / "out.html"))

    assert Path(output).exists()


def test_analysis_html_fixture_generates_report(tmp_path: Path) -> None:
    output = analysis_html("tests/fixtures/mini_eval.zip", str(tmp_path / "fixture.html"), enable_hash_repeat_chart=True)
    html = Path(output).read_text(encoding="utf-8")

    assert "r_success" in html
    assert "r_retry" in html
    assert "hash_id 重复评测聚合图" not in html
    assert "<th>hash_id</th>" in html


def test_compare_analysis_html_requires_same_eval_prefix(tmp_path: Path) -> None:
    left = tmp_path / "AIME_left.zip"
    right = tmp_path / "MATH_right.zip"
    copyfile("tests/fixtures/mini_eval.zip", left)
    copyfile("tests/fixtures/mini_eval.zip", right)

    with pytest.raises(ValueError, match="评测名必须一致"):
        compare_analysis_html(str(left), str(right), str(tmp_path / "compare.html"))


def test_compare_analysis_html_generates_two_column_report(tmp_path: Path) -> None:
    left = tmp_path / "AIME_left.zip"
    right = tmp_path / "AIME_right.zip"
    copyfile("tests/fixtures/mini_eval.zip", left)
    copyfile("tests/fixtures/mini_eval.zip", right)

    output = compare_analysis_html(str(left), str(right), str(tmp_path / "compare.html"))
    html = Path(output).read_text(encoding="utf-8")

    assert "评测日志对比报告" in html
    assert "compare-columns" in html
    assert "AIME_left.zip" in html
    assert "AIME_right.zip" in html
    assert "核心指标箱线图对比" in html
    assert "compare-boxplot-pair" in html
    assert "AIME_left.zip · complete tokens" in html
    assert "AIME_right.zip · complete tokens" in html
    assert "id=\"left-retry-search\"" in html
    assert "id=\"right-retry-search\"" in html
    assert "left::r_success" in html
    assert "right::r_success" in html
