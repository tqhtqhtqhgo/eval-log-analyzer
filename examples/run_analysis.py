from __future__ import annotations

from eval_log_analyzer import analysis_html


def main() -> None:
    html_path = analysis_html("tests/fixtures/mini_eval.zip")
    print(html_path)


if __name__ == "__main__":
    main()
