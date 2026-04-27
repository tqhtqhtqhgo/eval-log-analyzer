from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eval_log_analyzer import analysis_html


def main() -> None:
    html_path = analysis_html("tests/fixtures/mini_eval.zip", enable_hash_repeat_chart=True)
    print(html_path)


if __name__ == "__main__":
    main()
