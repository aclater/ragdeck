const API = '';
let adminToken = localStorage.getItem('ragdeck_admin_token') || '';

function setToken(t) { adminToken = t; localStorage.setItem('ragdeck_admin_token', t); }
function clearToken() { adminToken = ''; localStorage.removeItem('ragdeck_admin_token'); }

async function apiFetch(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (adminToken) headers['Authorization'] = `Bearer ${adminToken}`;
  const res = await fetch(API + path, { ...opts, headers });
  if (res.status === 401) { alert('Unauthorized — enter admin token'); return null; }
  return res.json();
}

async function apiGet(path) { return apiFetch(path); }
async function apiPost(path, body) { return apiFetch(path, { method: 'POST', body: JSON.stringify(body) }); }
async function apiDel(path) { return apiFetch(path, { method: 'DELETE' }); }

function loading(el) { el.classList.add('loading'); }
function done(el) { el.classList.remove('loading'); }

function showMsg(msg, type = 'info') {
  const prev = document.querySelector('.toast-msg');
  if (prev) prev.remove();
  const el = document.createElement('div');
  el.className = `toast-msg ${type}-msg`;
  el.textContent = msg;
  el.style.cssText = 'position:fixed;top:70px;right:1rem;z-index:200;max-width:320px;';
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function poll(fn, interval = 30000) {
  fn();
  return setInterval(fn, interval);
}

async function loadStatus() {
  const data = await apiGet('/status');
  if (!data || data.status === 'unavailable') return;
  const grid = document.getElementById('status-grid');
  if (!grid) return;
  const svcs = ['ragpipe', 'ragstuffer', 'ragorchestrator', 'ragwatch', 'qdrant', 'postgres'];
  svcs.forEach(name => {
    const s = data.services[name];
    const el = document.getElementById(`status-${name}`);
    if (!el) return;
    el.querySelector('.value').innerHTML = `<span class="status-badge ${s.status === 'up' ? 'up' : 'down'}">${s.status}</span>`;
  });
}

async function loadCollections() {
  const data = await apiGet('/collections');
  if (!data || data.status === 'unavailable') return;
  const tbody = document.querySelector('#collections-table tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  (data.collections || []).forEach(c => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${esc(c.name)}</strong></td>
      <td>${c.vector_count ?? '—'}</td>
      <td>${esc(c.source_types)}</td>
      <td>${c.created_at ? new Date(c.created_at).toLocaleDateString() : '—'}</td>
      <td>
        <button class="btn" onclick="viewCollection('${esc(c.name)}')">View</button>
        <button class="btn danger" onclick="confirmDeleteCollection('${esc(c.name)}')">Delete</button>
      </td>`;
    tbody.appendChild(tr);
  });
}

async function viewCollection(name) {
  const data = await apiGet(`/collections/${encodeURIComponent(name)}`);
  if (!data || data.status === 'unavailable') { showMsg('Collection not found', 'error'); return; }
  const detail = document.getElementById('collection-detail');
  if (!detail) return;
  detail.innerHTML = `
    <h3>${esc(data.name)}</h3>
    <p><strong>ID:</strong> ${esc(data.id)}</p>
    <p><strong>Description:</strong> ${esc(data.description || '—')}</p>
    <p><strong>Vectors:</strong> ${data.vector_count ?? '—'}</p>
    <p><strong>Points:</strong> ${data.points_count ?? '—'}</p>
    <p><strong>Source types:</strong> ${esc(data.source_types)}</p>
    <p><strong>Created:</strong> ${data.created_at ? new Date(data.created_at).toLocaleString() : '—'}</p>
  `;
  detail.hidden = false;
  window.location.hash = '#collection-detail';
}

async function triggerIngest(mode = 'now') {
  const data = await apiPost(`/ingest/trigger${mode === 'full' ? '-full' : ''}`, {});
  if (!data) return;
  if (data.error) { showMsg(data.error, 'error'); return; }
  showMsg(`Ingest triggered (${mode})`, 'success');
}

async function loadQuerylog(page = 0, grounding = '') {
  const limit = 20;
  const path = `/querylog?limit=${limit}&offset=${page * limit}${grounding ? `&grounding=${grounding}` : ''}`;
  const data = await apiGet(path);
  if (!data || data.status === 'unavailable') return;
  const tbody = document.querySelector('#querylog-table tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  (data.entries || []).forEach(e => {
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.onclick = () => viewQueryEntry(e.query_hash);
    tr.innerHTML = `
      <td>${e.created_at ? new Date(e.created_at).toLocaleString() : '—'}</td>
      <td><span class="badge badge-${e.grounding}">${esc(e.grounding)}</span></td>
      <td>${e.latency_ms ? e.latency_ms + 'ms' : '—'}</td>
      <td>${(e.cited_chunks || []).length} cited</td>
      <td><code style="font-size:.7rem">${esc(e.query_hash.slice(0, 12))}…</code></td>`;
    tbody.appendChild(tr);
  });
  updatePagination(data.total, data.limit, data.offset, 'querylog');
}

async function loadQuerylogStats() {
  const data = await apiGet('/querylog/stats');
  if (!data || data.status === 'unavailable') return;
  const el = document.getElementById('querylog-stats');
  if (!el) return;
  const total = data.total || 0;
  const byG = data.by_grounding || {};
  el.innerHTML = `
    <p>Total queries: <strong>${total}</strong></p>
    <p>Corpus: ${byG.corpus?.count || 0} (avg ${byG.corpus?.avg_latency?.toFixed(0) || '—'}ms)</p>
    <p>General: ${byG.general?.count || 0} (avg ${byG.general?.avg_latency?.toFixed(0) || '—'}ms)</p>
    <p>Mixed: ${byG.mixed?.count || 0} (avg ${byG.mixed?.avg_latency?.toFixed(0) || '—'}ms)</p>`;
  drawGroundingDonut(byG, total);
}

function drawGroundingDonut(byG, total) {
  const canvas = document.getElementById('grounding-canvas');
  if (!canvas || !total) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width = canvas.offsetWidth * 2;
  const H = canvas.height = canvas.offsetHeight * 2;
  ctx.clearRect(0, 0, W, H);
  const cx = W / 2, cy = H / 2, r = Math.min(W, H) / 2 - 20;
  const colors = { corpus: '#22c55e', general: '#eab308', mixed: '#3b82f6' };
  let start = -Math.PI / 2;
  Object.entries(colors).forEach(([key, color]) => {
    const count = byG[key]?.count || 0;
    if (!count) return;
    const slice = (count / total) * 2 * Math.PI;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, start, start + slice);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    start += slice;
  });
}

async function viewQueryEntry(hash) {
  const data = await apiGet(`/querylog/${encodeURIComponent(hash)}`);
  if (!data || data.status === 'unavailable') return;
  const el = document.getElementById('querylog-entry');
  if (!el) return;
  el.innerHTML = `
    <h3>Query: ${esc(hash.slice(0, 16))}…</h3>
    <p><strong>Ground:</strong> <span class="badge badge-${data.grounding}">${esc(data.grounding)}</span></p>
    <p><strong>Latency:</strong> ${data.latency_ms ? data.latency_ms + 'ms' : '—'}</p>
    <p><strong>Time:</strong> ${data.created_at ? new Date(data.created_at).toLocaleString() : '—'}</p>
    <p><strong>Cited chunks (${(data.cited_chunks || []).length}):</strong></p>
    <div class="json-view">${esc(JSON.stringify(data.cited_chunks || [], null, 2))}</div>`;
  el.hidden = false;
}

async function loadIngestStatus() {
  const data = await apiGet('/ingest/status');
  if (!data || data.status === 'unavailable') return;
  const el = document.getElementById('ingest-status');
  if (!el) return;
  const badge = data.ragstuffer_up
    ? '<span class="status-badge up">up</span>'
    : '<span class="status-badge down">down</span>';
  el.innerHTML = `<p>Ragstuffer: ${badge}</p>`;
  const tbody = document.querySelector('#ingest-collections tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  (data.collections || []).forEach(c => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${esc(c.name)}</strong></td>
      <td>${esc(c.source_types)}</td>
      <td>${c.last_updated ? new Date(c.last_updated).toLocaleString() : '—'}</td>`;
    tbody.appendChild(tr);
  });
}

async function loadMetrics() {
  const data = await apiGet('/metrics');
  if (!data || data.error) {
    document.getElementById('metrics-sources').innerHTML = '<p class="error-msg">Metrics unavailable. Is ragwatch running?</p>';
    document.getElementById('metrics-ragpipe').innerHTML = '';
    document.getElementById('metrics-ragstuffer').innerHTML = '';
    document.getElementById('metrics-ragorchestrator').innerHTML = '';
    return;
  }

  const sources = data.sources || {};
  const sourcesEl = document.getElementById('metrics-sources');
  if (sourcesEl) {
    const svcs = [
      { key: 'ragpipe', label: 'ragpipe', port: ':8090' },
      { key: 'ragstuffer', label: 'ragstuffer', port: ':8091' },
      { key: 'ragorchestrator', label: 'ragorchestrator', port: ':8095' },
    ];
    sourcesEl.innerHTML = svcs.map(s => {
      const src = sources[s.key] || {};
      const up = src.up !== false;
      return `<div class="tile">
        <div class="label">${esc(s.label)}</div>
        <div class="value"><span class="status-badge ${up ? 'up' : 'down'}">${up ? 'up' : 'down'}</span></div>
        <div class="sub">${s.port} · ${src.metric_count ?? 0} metrics</div>
      </div>`;
    }).join('');
  }

  renderMetricTiles('metrics-ragpipe', data.ragpipe, [
    { key: 'queries_total', label: 'Queries', fmt: 'int' },
    { key: 'embed_cache_hits', label: 'Cache Hits', fmt: 'int' },
    { key: 'embed_cache_misses', label: 'Cache Misses', fmt: 'int' },
    { key: 'embed_cache_hit_rate', label: 'Cache Hit Rate', fmt: 'pct' },
    { key: 'invalid_citations_total', label: 'Invalid Citations', fmt: 'int' },
    { key: 'chunks_retrieved_total', label: 'Chunks Retrieved', fmt: 'int' },
  ]);

  renderMetricTiles('metrics-ragstuffer', data.ragstuffer, [
    { key: 'documents_ingested_total', label: 'Documents Ingested', fmt: 'int' },
    { key: 'chunks_created_total', label: 'Chunks Created', fmt: 'int' },
    { key: 'embed_requests_total', label: 'Embed Requests', fmt: 'int' },
    { key: 'embed_errors_total', label: 'Embed Errors', fmt: 'int' },
  ]);

  renderMetricTiles('metrics-ragorchestrator', data.ragorchestrator, [
    { key: 'queries_total', label: 'Queries', fmt: 'int' },
    { key: 'query_latency_seconds', label: 'Avg Latency', fmt: 'latency' },
    { key: 'tool_calls_total', label: 'Tool Calls', fmt: 'int' },
    { key: 'complexity_classified_total', label: 'Complexity Classifications', fmt: 'int' },
  ]);

  const rawEl = document.getElementById('metrics-raw');
  if (rawEl) rawEl.textContent = JSON.stringify(data, null, 2);
}

function renderMetricTiles(elId, data, metrics) {
  const el = document.getElementById(elId);
  if (!el || !data) { if (el) el.innerHTML = '<p style="color:var(--text-muted)">No data</p>'; return; }
  el.innerHTML = metrics.map(m => {
    const val = data[m.key];
    if (val == null) return '';
    let display;
    if (m.fmt === 'int') display = Number(val).toLocaleString();
    else if (m.fmt === 'pct') display = (Number(val) * 100).toFixed(1) + '%';
    else if (m.fmt === 'latency') display = Number(val).toFixed(3) + 's';
    else display = esc(val);
    return `<div class="tile">
      <div class="label">${esc(m.label)}</div>
      <div class="value">${display}</div>
    </div>`;
  }).join('');
  if (!el.innerHTML) el.innerHTML = '<p style="color:var(--text-muted)">No data</p>';
}

let rawJsonVisible = false;
function toggleRawJson() {
  rawJsonVisible = !rawJsonVisible;
  const el = document.getElementById('metrics-raw');
  if (el) el.style.display = rawJsonVisible ? 'block' : 'none';
}

async function loadAdminConfig() {
  const data = await apiGet('/admin/config');
  const el = document.getElementById('admin-config');
  if (!el) return;
  el.innerHTML = data.error
    ? `<p class="error-msg">${esc(data.error)}</p>`
    : `<pre class="json-view">${esc(JSON.stringify(data, null, 2))}</pre>`;
}

async function adminAction(action) {
  const body = {};
  if (action !== 'config') {
    const token = document.getElementById('ragpipe-token')?.value;
    if (token) body.ragpipe_admin_token = token;
  }
  const data = await apiPost(`/admin/${action}`, body);
  if (!data) return;
  const el = document.getElementById(`admin-${action}-result`);
  if (!el) return;
  if (data.error) {
    el.innerHTML = `<p class="error-msg">${esc(data.error)}</p>`;
  } else {
    el.innerHTML = `<p class="success-msg">Action completed: ${esc(JSON.stringify(data))}</p>`;
    if (action === 'config') loadAdminConfig();
  }
}

function updatePagination(total, limit, offset, prefix) {
  const el = document.getElementById(`${prefix}-pagination`);
  if (!el) return;
  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit);
  let html = `<span class="info">${offset + 1}–${Math.min(offset + limit, total)} of ${total}</span>`;
  html += `<button class="btn" ${currentPage === 0 ? 'disabled' : ''} onclick="${prefix}_page(${currentPage - 1})">&laquo; Prev</button>`;
  html += `<button class="btn" ${currentPage >= totalPages - 1 ? 'disabled' : ''} onclick="${prefix}_page(${currentPage + 1})">Next &raquo;</button>`;
  el.innerHTML = html;
}

function querylog_page(p) { loadQuerylog(p, document.getElementById('grounding-filter')?.value || ''); }

function esc(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

async function confirmDeleteCollection(name) {
  if (!confirm(`Delete collection "${name}"? This removes it from Postgres and Qdrant.`)) return;
  const data = await apiDel(`/collections/${encodeURIComponent(name)}`);
  if (!data) return;
  if (data.error) { showMsg(data.error, 'error'); return; }
  showMsg(`Deleted ${name}`, 'success');
  loadCollections();
}

function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
