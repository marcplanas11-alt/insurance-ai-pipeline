/* ─────────────────────────────────────────────────────────────
   Insurance AI Pipeline — Frontend Logic
───────────────────────────────────────────────────────────── */

// ─── TAB SWITCHING ───────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'analytics') loadAnalytics();
  });
});

// ─── FILE DRAG & DROP ────────────────────────────────────────
function handleDragOver(e) {
  e.preventDefault();
  e.currentTarget.classList.add('drag-over');
}
function handleDragLeave(e) {
  e.currentTarget.classList.remove('drag-over');
}
function handleDrop(e, prefix) {
  e.preventDefault();
  e.currentTarget.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(prefix, file);
}

// ─── FILE SELECTION ──────────────────────────────────────────
const _files = {};

function handleFileSelect(prefix) {
  const input = document.getElementById(prefix + '-file');
  if (input.files[0]) setFile(prefix, input.files[0]);
}

function setFile(prefix, file) {
  _files[prefix] = file;
  const nameEl = document.getElementById(prefix + '-filename');
  nameEl.textContent = '📎 ' + file.name + ' (' + formatBytes(file.size) + ')';
  nameEl.classList.remove('hidden');
  document.getElementById(prefix + '-run').disabled = false;
  document.getElementById(prefix + '-status').textContent = '';
  document.getElementById(prefix + '-results').classList.add('hidden');
}

function formatBytes(b) {
  if (b < 1024) return b + ' B';
  if (b < 1048576) return (b / 1024).toFixed(1) + ' KB';
  return (b / 1048576).toFixed(1) + ' MB';
}

// ─── VETFEES PARSER ──────────────────────────────────────────
async function runVetfees() {
  const btn = document.getElementById('vetfees-run');
  const status = document.getElementById('vetfees-status');
  const file = _files['vetfees'];
  if (!file) return;

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Parsing…';
  status.textContent = 'Running regex extraction pipeline…';

  const form = new FormData();
  form.append('file', file);

  try {
    const res = await fetch('/api/vetfees/parse', { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Unknown error');
    renderVetfeesResults(data);
    status.textContent = `Completed — ${data.total_rows.toLocaleString()} rows processed.`;
  } catch (err) {
    status.textContent = '⚠ Error: ' + err.message;
    status.style.color = 'var(--red)';
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run Parser';
  }
}

function renderVetfeesResults(d) {
  const results = document.getElementById('vetfees-results');
  results.classList.remove('hidden');

  // Stat cards
  const sc = d.status_counts || {};
  const total = d.total_rows || 0;
  const pct = (n) => total > 0 ? ' (' + ((n / total) * 100).toFixed(1) + '%)' : '';

  const statsEl = document.getElementById('vetfees-stats');
  statsEl.innerHTML = `
    ${statCard('Total Rows', total.toLocaleString(), '', 'blue')}
    ${statCard('Parsed',   (sc.parsed   || 0).toLocaleString(), pct(sc.parsed   || 0), 'green')}
    ${statCard('Partial',  (sc.partial  || 0).toLocaleString(), pct(sc.partial  || 0), 'amber')}
    ${statCard('Failed',   (sc.failed   || 0).toLocaleString(), pct(sc.failed   || 0), 'red')}
    ${d.avg_limit_confidence != null ? statCard('Avg Limit Conf.', d.avg_limit_confidence, '', 'blue') : ''}
    ${d.avg_excess_confidence != null ? statCard('Avg Excess Conf.', d.avg_excess_confidence, '', 'blue') : ''}
  `;

  // Row count label
  document.getElementById('vetfees-row-count').textContent =
    '(showing up to 200 of ' + total.toLocaleString() + ')';

  // Download link
  const dlBtn = document.getElementById('vetfees-download');
  dlBtn.href = '/api/download/' + d.job_id;
  dlBtn.removeAttribute('hidden');

  // Table
  renderTable('vetfees', d.preview_columns, d.preview);
}

// ─── BORDEREAUX CLEANER ──────────────────────────────────────
async function runBordereaux() {
  const btn = document.getElementById('bord-run');
  const status = document.getElementById('bord-status');
  const file = _files['bord'];
  if (!file) return;

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Cleaning…';
  status.textContent = 'Running 10-step cleaning pipeline…';

  const form = new FormData();
  form.append('file', file);

  try {
    const res = await fetch('/api/bordereaux/clean', { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Unknown error');
    renderBordereauResults(data);
    status.textContent = `Completed — ${data.total_rows.toLocaleString()} rows cleaned.`;
  } catch (err) {
    status.textContent = '⚠ Error: ' + err.message;
    status.style.color = 'var(--red)';
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run Cleaner';
  }
}

function renderBordereauResults(d) {
  const results = document.getElementById('bord-results');
  results.classList.remove('hidden');

  // Issues banner
  const issuesEl = document.getElementById('bord-issues');
  if (d.issues && d.issues.length > 0) {
    issuesEl.classList.remove('hidden');
    issuesEl.innerHTML = '<strong>⚠ Structural Issues Found</strong><ul>' +
      d.issues.map(i => '<li>' + escHtml(i) + '</li>').join('') + '</ul>';
  } else {
    issuesEl.classList.add('hidden');
  }

  // Stat cards
  const r = d.report || {};
  const statsEl = document.getElementById('bord-stats');
  statsEl.innerHTML = `
    ${statCard('Total Rows',   (r.total_rows || 0).toLocaleString(), '', 'blue')}
    ${statCard('Total Premium', r.total_premium != null ? '£' + r.total_premium.toLocaleString() : 'N/A', '', 'green')}
    ${statCard('Avg Premium',   r.avg_premium  != null ? '£' + r.avg_premium  : 'N/A', '', 'blue')}
    ${statCard('Date Errors',   (r.date_errors || 0), '', r.date_errors > 0 ? 'red' : 'green')}
    ${statCard('Invalid CCY',   (r.invalid_currencies || 0), '', r.invalid_currencies > 0 ? 'amber' : 'green')}
    ${statCard('Columns',       (r.total_columns || 0), '', 'blue')}
  `;

  document.getElementById('bord-row-count').textContent =
    '(showing up to 200 of ' + (d.total_rows || 0).toLocaleString() + ')';

  const dlBtn = document.getElementById('bord-download');
  dlBtn.href = '/api/download/' + d.job_id;
  dlBtn.removeAttribute('hidden');

  renderTable('bord', d.preview_columns, d.preview);
}

// ─── SQL ANALYTICS ───────────────────────────────────────────
let _analyticsLoaded = false;

async function loadAnalytics() {
  if (_analyticsLoaded) return;
  const grid = document.getElementById('analytics-grid');
  try {
    const res = await fetch('/api/analytics/queries');
    const data = await res.json();
    _analyticsLoaded = true;
    grid.innerHTML = data.queries.map(q => queryCard(q)).join('');
    // Attach toggle handlers
    grid.querySelectorAll('.query-card-header').forEach(h => {
      h.addEventListener('click', () => {
        h.closest('.query-card').classList.toggle('open');
      });
    });
  } catch (err) {
    grid.innerHTML = '<p style="color:var(--red)">⚠ Failed to load queries: ' + err.message + '</p>';
  }
}

function queryCard(q) {
  return `
  <div class="query-card" id="qcard-${q.id}">
    <div class="query-card-header">
      <div class="query-num">${q.id}</div>
      <div class="query-meta">
        <div class="query-title">${escHtml(q.title)}</div>
        <div class="query-desc">${escHtml(q.description)}</div>
      </div>
      <div class="query-toggle">▾</div>
    </div>
    <div class="query-body">
      <div class="query-actions">
        <button class="copy-btn" onclick="copyQuery(${q.id}, this)">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
          </svg>
          Copy SQL
        </button>
      </div>
      <pre class="sql-block">${highlightSql(escHtml(q.sql))}</pre>
    </div>
  </div>`;
}

function copyQuery(id, btn) {
  const pre = document.querySelector(`#qcard-${id} .sql-block`);
  const text = pre.textContent;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = '✓ Copied!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg> Copy SQL';
      btn.classList.remove('copied');
    }, 1800);
  });
}

// Basic SQL syntax highlighting.
// Order matters: comments and strings first (so keywords inside them aren't coloured),
// then functions before keywords so shared names (COUNT, SUM, etc.) get the function style.
function highlightSql(html) {
  const comments  = /(--[^\n]*)/g;
  const strings   = /('[^']*')/g;
  // Function names only — coloured before keywords to prevent keyword class overwriting them
  const functions = /\b(RANK|CUME_DIST|NTILE|COUNT|ROUND|AVG|SUM|MIN|MAX|COALESCE|NULLIF|STDDEV|CONCAT|CAST|CONVERT|ISNULL|NVL|TO_DATE|DATE_TRUNC|EXTRACT)\b/g;
  // Keywords that are not also function names
  const keywords  = /\b(SELECT|FROM|WHERE|HAVING|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AS|CASE|WHEN|THEN|ELSE|END|AND|OR|NOT|IN|IS|NULL|DISTINCT|OVER|BY|WITH|LIMIT|OFFSET|ASC|DESC|INTO|INSERT|UPDATE|DELETE|CREATE|TABLE|INDEX|VIEW|DROP|ALTER|SET|VALUES|GROUP|ORDER|PARTITION)\b/g;
  const numbers   = /\b(\d+(?:\.\d+)?)\b/g;

  return html
    .replace(comments,  '<span class="sql-cmt">$1</span>')
    .replace(strings,   '<span class="sql-str">$1</span>')
    .replace(functions, '<span class="sql-fn">$1</span>')
    .replace(keywords,  '<span class="sql-kw">$1</span>')
    .replace(numbers,   '<span class="sql-num">$1</span>');
}

// ─── TABLE RENDERER ──────────────────────────────────────────
function renderTable(prefix, cols, rows) {
  const thead = document.getElementById(prefix + '-thead');
  const tbody = document.getElementById(prefix + '-tbody');

  thead.innerHTML = '<tr>' + cols.map(c => `<th title="${escHtml(c)}">${escHtml(c)}</th>`).join('') + '</tr>';

  tbody.innerHTML = rows.map(row => {
    const cells = cols.map(col => {
      const val = row[col];
      const cls = cellClass(col, val);
      return `<td class="${cls}" title="${escHtml(String(val))}">${escHtml(String(val))}</td>`;
    });
    return '<tr>' + cells.join('') + '</tr>';
  }).join('');
}

function cellClass(col, val) {
  if (col === 'parse_status') return 'status-' + String(val).toLowerCase();
  if (col === 'date_error' || col === 'has_missing_required') {
    return val === true || val === 'True' || val === 'true' ? 'bool-true' : 'bool-false';
  }
  if (col === 'currency_valid') {
    return val === false || val === 'False' || val === 'false' ? 'bool-true' : 'bool-false';
  }
  return '';
}

// ─── STAT CARD HELPER ────────────────────────────────────────
function statCard(label, value, sub, colour) {
  return `
  <div class="stat-card">
    <div class="stat-label">${escHtml(label)}</div>
    <div class="stat-value ${colour}">${escHtml(String(value))}</div>
    ${sub ? `<div class="stat-sub">${escHtml(sub)}</div>` : ''}
  </div>`;
}

// ─── UTILITY ─────────────────────────────────────────────────
function escHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
