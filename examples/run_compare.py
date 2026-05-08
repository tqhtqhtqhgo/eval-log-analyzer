from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eval_log_analyzer import compare_analysis_html


def main() -> None:
    fixture_dir = ROOT / "tests" / "fixtures"
    source_zip = fixture_dir / "mini_eval.zip"

    with tempfile.TemporaryDirectory(prefix="eval-log-compare-") as temp_dir:
        temp_path = Path(temp_dir)
        left_zip = temp_path / "AIME_compare_left.zip"
        right_zip = temp_path / "AIME_compare_right.zip"

        # 对比函数要求两个 zip 文件名第一个下划线前的评测名一致。
        shutil.copyfile(source_zip, left_zip)
        shutil.copyfile(source_zip, right_zip)

        html_path = compare_analysis_html(
            str(left_zip),
            str(right_zip),
            output_html=str(fixture_dir / "AIME_compare_analysis.html"),
        )
    print(html_path)


if __name__ == "__main__":
    main()
