from pathlib import Path
from zipfile import ZipFile

from eval_log_analyzer import analysis_html


def test_analysis_html_minimal(tmp_path: Path) -> None:
    zip_path = tmp_path / "mini.zip"
    with ZipFile(zip_path, "w") as zf:
        zf.writestr("mini.log", "")

    output = analysis_html(str(zip_path), str(tmp_path / "out.html"))

    assert Path(output).exists()
