from pathlib import Path
from zipfile import ZipFile

from eval_log_analyzer import analysis_html


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
    assert "hash_id 重复评测聚合图" in html
