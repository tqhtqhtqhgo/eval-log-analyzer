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
:root { color-scheme: light; --ok:#16803c; --bad:#b42318; --warn:#c46a12; --ink:#172033; --muted:#667085; --line:#d7dde8; --panel:#f7f9fc; }
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: #ffffff; }
main { max-width: 1240px; margin: 0 auto; padding: 24px; }
h1 { margin: 0 0 18px; font-size: 28px; }
h2 { margin: 28px 0 12px; font-size: 20px; }
h3 { margin: 20px 0 10px; font-size: 16px; }
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
.toolbar { display: flex; gap: 8px; flex-wrap: wrap; align-items: flex-start; margin-bottom: 12px; }
.toolbar input[type="search"] { margin: 0; }
.toolbar button.active { border-color: var(--warn); color: var(--warn); font-weight: 650; }
.status-btn { min-width: 36px; font-size: 18px; line-height: 1; }
.final-ok { color: var(--ok); font-weight: 700; }
.final-bad, .failure { color: var(--bad); font-weight: 700; }
.result-pill { display: inline-flex; min-width: 42px; justify-content: center; border-radius: 999px; padding: 2px 8px; font-size: 12px; font-weight: 650; border: 1px solid currentColor; }
.result-pill.ok { color: var(--ok); }
.result-pill.bad { color: var(--bad); }
.result-pill.warn { color: var(--warn); }
.result-pill.unknown { color: var(--muted); }
.length-row { display: grid; grid-template-columns: 48px 1fr 96px; gap: 10px; align-items: center; padding: 4px 0; border-bottom: 1px solid var(--line); cursor: pointer; min-height: 20px; }
.bar-track { height: 12px; background: #eef3f8; border-radius: 6px; overflow: hidden; }
.bar { height: 100%; min-width: 2px; }
.bar.ok { background: var(--ok); }
.bar.bad { background: var(--bad); }
.bar.warn { background: var(--warn); }
.bar.unknown { background: var(--muted); }
.length-value { text-align: right; font-variant-numeric: tabular-nums; }
.hash-repeat-row { display: grid; grid-template-columns: 42px minmax(120px, 1fr) 150px; gap: 8px; align-items: center; padding: 2px 0; border-bottom: 1px solid var(--line); cursor: pointer; min-height: 16px; font-size: 13px; }
.hash-repeat-row .bar-track { height: 8px; border-radius: 4px; }
.hash-repeat-value { display: flex; justify-content: flex-end; gap: 8px; white-space: nowrap; text-align: right; font-variant-numeric: tabular-nums; }
.compact-length-chart { width: 100%; display: flex; flex-direction: column; gap: 1px; padding: 8px; border: 1px solid var(--line); border-radius: 8px; background: #fbfcfe; overflow: hidden; }
.compact-length-line { height: 3px; min-width: 1px; border-radius: 0 2px 2px 0; cursor: pointer; }
.compact-length-line.ok { background: var(--ok); }
.compact-length-line.bad { background: var(--bad); }
.compact-length-line.warn { background: var(--warn); }
.compact-length-line.unknown { background: var(--muted); }
.boxplot-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }
.boxplot-row-title { color: var(--muted); font-size: 13px; font-weight: 650; margin: 12px 0 8px; }
.boxplot-card { border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: var(--panel); min-height: 178px; }
.boxplot { position: relative; width: 78px; height: 84px; margin: 12px auto 0; border-left: 1px solid #dce3ee; border-bottom: 1px solid #dce3ee; }
.boxplot .whisker { position: absolute; left: 38px; width: 2px; background: #475467; }
.boxplot .cap { position: absolute; left: 29px; width: 20px; height: 2px; background: #475467; }
.boxplot .box { position: absolute; left: 24px; width: 30px; border: 2px solid #475467; background: rgba(71, 84, 103, .12); border-radius: 3px; }
.boxplot .quartile { position: absolute; left: 20px; width: 38px; height: 1px; background: #475467; }
.boxplot .quartile::after { position: absolute; left: 42px; top: -8px; color: var(--muted); font-size: 10px; }
.boxplot .q1::after { content: "p25"; }
.boxplot .q3::after { content: "p75"; }
.boxplot .median { position: absolute; left: 18px; width: 42px; height: 2px; background: var(--bad); }
.boxplot-meta { color: var(--muted); font-size: 12px; margin-top: 2px; font-variant-numeric: tabular-nums; }
.pie-wrap { display: flex; gap: 20px; align-items: center; flex-wrap: wrap; border: 1px solid var(--line); border-radius: 8px; padding: 16px; background: var(--panel); }
.pie-chart { position: relative; width: 132px; height: 132px; border-radius: 50%; border: 1px solid var(--line); flex: 0 0 auto; }
.pie-chart::after { content: ""; position: absolute; inset: 34px; border-radius: 50%; background: var(--panel); border: 1px solid var(--line); }
.pie-legend { display: grid; gap: 8px; min-width: 220px; }
.pie-legend-item { display: grid; grid-template-columns: 14px 1fr auto; gap: 8px; align-items: center; font-size: 14px; }
.legend-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
.legend-dot.ok { background: var(--ok); }
.legend-dot.warn { background: var(--warn); }
.legend-dot.bad { background: var(--bad); }
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
const retryFilterState = { failureOnly: false, evalFailedOnly: false, finalFailedOnly: false };
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
function elaOpenHash(id) {
  const data = window.__evalLogAnalyzer.hashGroups[id];
  if (!data) return;
  modalState.current = { request_json: null, response_json: data };
  modalState.full = false;
  document.getElementById('modal-title').textContent = `hash_id ${data.hash_id}`;
  document.getElementById('modal-meta').textContent = `req_id=${data.req_ids.join(', ')} 平均长度=${data.avg_response_length} 正确=${data.correct_count}/${data.total_count}`;
  document.getElementById('modal-failure').textContent = data.correct_count > 0 ? '' : '正确次数为 0';
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
function elaToggleFailureFilter() {
  retryFilterState.failureOnly = !retryFilterState.failureOnly;
  const button = document.getElementById('failure-filter');
  if (button) button.classList.toggle('active', retryFilterState.failureOnly);
  elaFilterRetry();
}
function elaToggleEvalFailedFilter() {
  retryFilterState.evalFailedOnly = !retryFilterState.evalFailedOnly;
  const button = document.getElementById('eval-failed-filter');
  if (button) button.classList.toggle('active', retryFilterState.evalFailedOnly);
  elaFilterRetry();
}
function elaToggleFinalFailedFilter() {
  retryFilterState.finalFailedOnly = !retryFilterState.finalFailedOnly;
  const button = document.getElementById('final-failed-filter');
  if (button) button.classList.toggle('active', retryFilterState.finalFailedOnly);
  elaFilterRetry();
}
function elaFilterRetry() {
  const input = document.getElementById('retry-search');
  const keyword = (input ? input.value : '').trim().toLowerCase();
  for (const row of document.querySelectorAll('[data-retry-row]')) {
    const haystack = row.getAttribute('data-search') || '';
    const hasFailure = row.getAttribute('data-has-failure') === 'true';
    const evalFailed = row.getAttribute('data-eval-failed') === 'true';
    const finalFailed = row.getAttribute('data-final-failed') === 'true';
    row.style.display = haystack.includes(keyword)
      && (!retryFilterState.failureOnly || hasFailure)
      && (!retryFilterState.evalFailedOnly || evalFailed)
      && (!retryFilterState.finalFailedOnly || finalFailed) ? '' : 'none';
  }
}
"""
