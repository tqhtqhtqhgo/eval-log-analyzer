HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>{css}</style>
</head>
<body>
  {body}
  <script>{js}</script>
</body>
</html>
"""

BASE_CSS = """
:root { color-scheme: light; --ok:#16803c; --bad:#b42318; --ink:#172033; --muted:#667085; --line:#d7dde8; --panel:#f7f9fc; }
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: #ffffff; }
main { max-width: 1240px; margin: 0 auto; padding: 24px; }
h1 { margin: 0 0 18px; font-size: 28px; }
h2 { margin: 28px 0 12px; font-size: 20px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }
.card { border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: var(--panel); min-height: 76px; }
.label { color: var(--muted); font-size: 13px; margin-bottom: 8px; }
.value { font-size: 20px; font-weight: 650; overflow-wrap: anywhere; }
table { width: 100%; border-collapse: collapse; border: 1px solid var(--line); }
th, td { border-bottom: 1px solid var(--line); padding: 10px; text-align: left; vertical-align: top; }
th { background: #eef3f8; font-weight: 650; }
.muted { color: var(--muted); }
"""

BASE_JS = """
window.__evalLogAnalyzer = window.__evalLogAnalyzer || {};
"""
