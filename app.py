<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>Transformer Health Control Room</title>
<style>
  :root {
    --bg: #0a0f1a; --panel: #0c1829; --border: #1e2d45;
    --text-dim: #4a6080; --text: #e2e8f0;
    --safe: #22c55e; --warn: #f97316; --crit: #ef4444; --blue: #60a5fa;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--text); font-family: -apple-system, "Segoe UI", system-ui, sans-serif; padding: 24px; }
  .wrap { max-width: 1100px; margin: 0 auto; }
  .header { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); padding-bottom: 14px; margin-bottom: 18px; }
  .header-left { display: flex; align-items: center; gap: 10px; }
  .dot { width: 10px; height: 10px; border-radius: 50%; background: var(--safe); animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
  .title { font-size: 17px; font-weight: 600; }
  .subtitle { font-size: 11px; color: var(--text-dim); margin-top: 2px; }
  .live-badge { font-size: 11px; color: var(--safe); background: #0d2016; border: 1px solid #166534; border-radius: 20px; padding: 5px 14px; }
  .grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 18px; }
  .card { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px; text-align: center; }
  .card-label { font-size: 10px; color: var(--text-dim); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; }
  .card-value { font-size: 26px; font-weight: 600; }
  .section-label { font-size: 10px; color: var(--text-dim); letter-spacing: 1px; text-transform: uppercase; margin: 18px 0 10px; }
  .gas-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-bottom: 18px; }
  .gas-card { background: #0d1520; border: 1px solid var(--border); border-radius: 8px; padding: 12px 6px; text-align: center; }
  .gas-name { font-size: 11px; color: var(--text-dim); margin-bottom: 6px; }
  .gas-val { font-size: 19px; font-weight: 600; margin-bottom: 6px; }
  .bar-bg { background: var(--border); border-radius: 3px; height: 4px; }
  .bar-fill { height: 4px; border-radius: 3px; }
  .gas-limit { font-size: 9px; color: #2d4060; margin-top: 4px; }
  table { width: 100%; border-collapse: collapse; }
  th { padding: 6px 8px; color: var(--text-dim); font-weight: 400; font-size: 10px; text-align: left; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }
  td { padding: 7px 8px; font-size: 12px; color: #94a3b8; border-bottom: 1px solid #111c2d; }
  .log-panel { background: #0d1520; border: 1px solid var(--border); border-radius: 10px; padding: 14px; }
  .footer { margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border); font-size: 10px; color: #2d4060; text-align: center; }
  .status-line { font-size: 11px; color: var(--text-dim); text-align: center; margin-top: 8px; }
  .download-link { color: var(--blue); text-decoration: none; }
  .download-link:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="wrap">

  <div class="header">
    <div class="header-left">
      <div class="dot" id="liveDot"></div>
      <div>
        <div class="title">Transformer Health Control Room</div>
        <div class="subtitle" id="updatedAt">AI-Based DGA Monitoring — waiting for data...</div>
      </div>
    </div>
    <div class="live-badge" id="liveBadge">CONNECTING…</div>
  </div>

  <div class="grid4">
    <div class="card" id="alertCard">
      <div class="card-label">System Alert</div>
      <div class="card-value" id="alertVal">--</div>
    </div>
    <div class="card">
      <div class="card-label">Fault Type</div>
      <div class="card-value" id="faultVal" style="font-size:18px;">--</div>
    </div>
    <div class="card">
      <div class="card-label">Confidence</div>
      <div class="card-value" id="confVal" style="color:var(--blue);">--</div>
    </div>
    <div class="card">
      <div class="card-label">Risk Level</div>
      <div class="card-value" id="riskVal" style="font-size:16px; color:var(--blue);">--</div>
    </div>
  </div>

  <div class="section-label">Current Gas Concentrations (ppm)</div>
  <div class="gas-grid" id="gasGrid"></div>

  <div class="log-panel">
    <div class="section-label" style="margin-top:0;">Recent Reading Log</div>
    <table>
      <thead>
        <tr>
          <th>Timestamp</th><th>H2</th><th>CH4</th><th>C2H2</th><th>CO</th><th>CO2</th>
          <th>Fault Type</th><th>Alert</th>
        </tr>
      </thead>
      <tbody id="logBody"></tbody>
    </table>
  </div>

  <div class="status-line" id="statusLine">
    Auto-refreshes every 30 seconds — <a class="download-link" href="/api/download_csv">Download full log (CSV)</a>
  </div>
  <div class="footer">Smart Grid — AI Transformer Monitoring System</div>

</div>

<script>
const GAS_LIMITS = {
  H2:   { limit: 100,  color: '#60a5fa', label: 'H2' },
  CH4:  { limit: 120,  color: '#34d399', label: 'CH4' },
  C2H6: { limit: 65,   color: '#a78bfa', label: 'C2H6' },
  C2H4: { limit: 65,   color: '#f472b6', label: 'C2H4' },
  C2H2: { limit: 35,   color: '#f87171', label: 'C2H2' },
  CO:   { limit: 350,  color: '#fb923c', label: 'CO' },
  CO2:  { limit: 2500, color: '#c084fc', label: 'CO2' },
};
const ALERT_COLOR = { SAFE: 'var(--safe)', WARNING: 'var(--warn)', CRITICAL: 'var(--crit)' };
const FAULT_COLOR = {
  Normal: 'var(--safe)', Partial_Discharge: 'var(--warn)',
  Thermal_Fault: 'var(--crit)', Arcing: '#cc0000'
};

function renderGasGrid(latest) {
  const grid = document.getElementById('gasGrid');
  grid.innerHTML = '';
  Object.keys(GAS_LIMITS).forEach(key => {
    const val = parseFloat(latest[key] || 0);
    const { limit, color, label } = GAS_LIMITS[key];
    const pct = Math.min((val / limit) * 100, 100);
    const barColor = pct < 50 ? 'var(--safe)' : pct < 85 ? 'var(--warn)' : 'var(--crit)';
    grid.innerHTML += `
      <div class="gas-card">
        <div class="gas-name">${label}</div>
        <div class="gas-val" style="color:${color}">${val.toFixed(1)}</div>
        <div class="bar-bg"><div class="bar-fill" style="width:${pct}%; background:${barColor};"></div></div>
        <div class="gas-limit">Limit: ${limit}</div>
      </div>`;
  });
}

function renderLog(rows) {
  const body = document.getElementById('logBody');
  body.innerHTML = rows.slice().reverse().map(r => {
    const ac = ALERT_COLOR[r.Alert] || '#94a3b8';
    const fc = FAULT_COLOR[r.Fault_Type] || '#94a3b8';
    return `<tr>
      <td>${r.Timestamp}</td>
      <td>${parseFloat(r.H2).toFixed(1)}</td>
      <td>${parseFloat(r.CH4).toFixed(1)}</td>
      <td>${parseFloat(r.C2H2).toFixed(1)}</td>
      <td>${parseFloat(r.CO).toFixed(1)}</td>
      <td>${parseFloat(r.CO2).toFixed(1)}</td>
      <td style="color:${fc}">${(r.Fault_Type || '').replace('_',' ')}</td>
      <td style="color:${ac}; font-weight:600;">${r.Alert}</td>
    </tr>`;
  }).join('');
}

async function refresh() {
  try {
    const resp = await fetch('/api/latest?_=' + Date.now());
    const data = await resp.json();

    if (data.status !== 'live' || !data.latest) {
      throw new Error('waiting for data');
    }

    const latest = data.latest;

    document.getElementById('liveDot').style.background = 'var(--safe)';
    document.getElementById('liveBadge').textContent = 'LIVE';
    document.getElementById('liveBadge').style.color = 'var(--safe)';
    document.getElementById('updatedAt').textContent =
      `AI-Based DGA Monitoring — Updated: ${latest.Timestamp}`;

    const alertEl = document.getElementById('alertVal');
    alertEl.textContent = latest.Alert;
    alertEl.style.color = ALERT_COLOR[latest.Alert] || 'var(--blue)';
    document.getElementById('alertCard').style.borderColor = ALERT_COLOR[latest.Alert] || 'var(--border)';

    const faultEl = document.getElementById('faultVal');
    faultEl.textContent = (latest.Fault_Type || '').replace('_', ' ');
    faultEl.style.color = FAULT_COLOR[latest.Fault_Type] || 'var(--text)';

    document.getElementById('confVal').textContent =
      (parseFloat(latest.Confidence) * 100).toFixed(1) + '%';
    document.getElementById('riskVal').textContent = latest.Risk_Level;

    renderGasGrid(latest);
    renderLog(data.history || []);

    document.getElementById('statusLine').innerHTML =
      `Auto-refreshes every 30 seconds — ${data.total_readings} total readings — ` +
      `<a class="download-link" href="/api/download_csv">Download full log (CSV)</a>`;

  } catch (err) {
    document.getElementById('liveDot').style.background = 'var(--crit)';
    document.getElementById('liveBadge').textContent = 'NO DATA';
    document.getElementById('liveBadge').style.color = 'var(--crit)';
    document.getElementById('statusLine').textContent =
      'Waiting for sensor data...';
  }
}

refresh();
setInterval(refresh, 30000);
</script>
</body>
</html>
