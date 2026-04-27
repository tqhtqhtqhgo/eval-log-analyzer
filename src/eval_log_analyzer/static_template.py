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
button { border: 1px solid var(--line); border-radius: 6px; background: #fff; padding: 6px 9px; cursor: pointer; }
input[type="search"] { width: min(520px, 100%); padding: 10px 12px; border: 1px solid var(--line); border-radius: 6px; margin: 0 0 12px; }
.status-btn { min-width: 36px; font-size: 18px; line-height: 1; }
.final-ok { color: var(--ok); font-weight: 700; }
.final-bad, .failure { color: var(--bad); font-weight: 700; }
.modal-backdrop { position: fixed; inset: 0; background: rgba(15, 23, 42, .55); display: none; align-items: center; justify-content: center; padding: 18px; z-index: 10; }
.modal-backdrop.open { display: flex; }
.modal { background: #fff; border-radius: 8px; width: min(980px, 96vw); max-height: 90vh; display: flex; flex-direction: column; border: 1px solid var(--line); }
.modal-head { padding: 14px 16px; border-bottom: 1px solid var(--line); display: flex; gap: 12px; justify-content: space-between; align-items: flex-start; }
.modal-body { padding: 14px 16px; overflow: auto; }
.modal-actions { display: flex; gap: 8px; margin: 10px 0; flex-wrap: wrap; }
pre { background: #0f172a; color: #e5e7eb; padding: 12px; border-radius: 6px; overflow: auto; max-height: 55vh; white-space: pre-wrap; word-break: break-word; }
"""

BASE_JS = """
window.__evalLogAnalyzer = window.__evalLogAnalyzer || {};
const modalState = { current: null, full: false };
function elaData(id) { return window.__evalLogAnalyzer.attempts[id]; }
function elaOpenAttempt(id) {
  const data = elaData(id);
  if (!data) return;
  modalState.current = data;
  modalState.full = false;
  document.getElementById('modal-title').textContent = `${data.req_id} / t${data.attempt_index} / ${data.success ? '成功' : '失败'}`;
  document.getElementById('modal-meta').textContent = `used_time=${data.used_time ?? '-'} response_length=${data.response_length ?? 0}`;
  document.getElementById('modal-failure').textContent = data.failure_reason || '';
  elaRenderJson();
  document.getElementById('json-modal').classList.add('open');
}
function elaRenderJson() {
  const data = modalState.current;
  if (!data) return;
  const payload = { request: data.request_json, response: data.response_json };
  let text = JSON.stringify(payload, null, 2);
  if (!modalState.full && text.length > 51200) text = text.slice(0, 51200) + '\\n... 已截断，点击显示完整 JSON';
  document.getElementById('modal-json').textContent = text;
}
function elaShowFull() { modalState.full = true; elaRenderJson(); }
function elaCloseModal() { document.getElementById('json-modal').classList.remove('open'); }
function elaCopyJson() {
  const text = document.getElementById('modal-json').textContent;
  if (navigator.clipboard) navigator.clipboard.writeText(text);
}
function elaFilterRetry(value) {
  const keyword = value.trim().toLowerCase();
  for (const row of document.querySelectorAll('[data-retry-row]')) {
    const haystack = row.getAttribute('data-search') || '';
    row.style.display = haystack.includes(keyword) ? '' : 'none';
  }
}
"""
