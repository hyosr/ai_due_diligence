from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

@router.get("/ui", response_class=HTMLResponse)
def ui_page():
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>AI Due Diligence Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {
      --bg: #0b1020;
      --card: #111831;
      --card-2: #0f1730;
      --text: #e8ecff;
      --muted: #9aa6d1;
      --ok: #16a34a;
      --warn: #f59e0b;
      --bad: #dc2626;
      --accent: #4f46e5;
      --border: #253055;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; padding: 24px;
      font-family: Inter, Arial, sans-serif;
      background: radial-gradient(1200px 600px at 20% -10%, #1b2a5b 0%, var(--bg) 40%);
      color: var(--text);
    }
    .container { max-width: 1200px; margin: 0 auto; }
    h1 { margin: 0 0 8px; font-size: 28px; }
    .muted { color: var(--muted); font-size: 13px; margin-bottom: 18px; }
    .panel {
      background: linear-gradient(180deg, var(--card), var(--card-2));
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px;
      margin-bottom: 16px;
      box-shadow: 0 8px 30px rgba(0,0,0,.25);
    }
    .grid-2 { display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    .field label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 6px; }
    input {
      width: 100%; padding: 11px 12px; border-radius: 10px; border: 1px solid var(--border);
      background: #0c1328; color: var(--text); outline: none;
    }
    input:focus { border-color: #4457aa; box-shadow: 0 0 0 2px rgba(79,70,229,.2); }
    button {
      margin-top: 12px; width: 100%; padding: 12px;
      border: none; border-radius: 10px; cursor: pointer;
      color: white; font-weight: 600;
      background: linear-gradient(90deg, #4f46e5, #2563eb);
    }
    .kpis { display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; }
    .kpi {
      background: #0c1328; border: 1px solid var(--border); border-radius: 12px; padding: 12px;
    }
    .kpi .v { font-size: 24px; font-weight: 700; margin-top: 6px; }
    .signals {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(250px,1fr)); gap: 10px;
      margin-top: 10px;
    }
    .signal {
      border: 1px solid var(--border); border-radius: 12px; background: #0c1328; padding: 12px;
    }
    .signal h4 { margin: 0 0 8px; font-size: 14px; }
    .badge {
      display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 700;
      margin-bottom: 6px;
    }
    .ok { background: rgba(22,163,74,.2); color: #86efac; border: 1px solid rgba(22,163,74,.35); }
    .warn { background: rgba(245,158,11,.2); color: #fcd34d; border: 1px solid rgba(245,158,11,.35); }
    .bad { background: rgba(220,38,38,.2); color: #fca5a5; border: 1px solid rgba(220,38,38,.35); }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
    pre {
      background: #0c1328; border: 1px solid var(--border); border-radius: 10px;
      padding: 10px; max-height: 320px; overflow: auto; font-size: 12px;
    }
    a { color: #93c5fd; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .small { font-size: 12px; color: var(--muted); }
    @media (max-width: 980px) {
      .grid-2, .row, .kpis { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>AI Due Diligence Dashboard</h1>
    <div class="muted">Signal cards + credibility score + radar chart + report export</div>

    <div class="panel grid-2">
      <div>
        <div class="field">
          <label>Company Name</label>
          <input id="companyName" placeholder="e.g. Notion" />
        </div>
        <div class="field">
          <label>Website URL</label>
          <input id="website" placeholder="https://www.notion.so" />
        </div>
        <div class="field">
          <label>Extra URLs (comma separated)</label>
          <input id="extraUrls" placeholder="https://example.com/security, https://example.com/privacy" />
        </div>
        <button onclick="runFlow()">Run Full Assessment</button>
      </div>

      <div class="panel" style="margin:0;">
        <canvas id="radarChart" height="220"></canvas>
      </div>
    </div>

    <div class="panel">
      <div class="kpis">
        <div class="kpi"><div class="small">Credibility Score</div><div class="v" id="kpiScore">-</div></div>
        <div class="kpi"><div class="small">Confidence</div><div class="v" id="kpiConfidence">-</div></div>
        <div class="kpi"><div class="small">Signals</div><div class="v" id="kpiSignals">-</div></div>
        <div class="kpi"><div class="small">Assessment ID</div><div class="v" id="kpiAssessment">-</div></div>
      </div>
    </div>

    <div class="panel">
      <h3 style="margin-top:0;">Signal Cards</h3>
      <div id="signals" class="signals"></div>
    </div>

    <div class="row">
      <div class="panel">
        <h3 style="margin-top:0;">Reports</h3>
        <div id="links">No report generated yet.</div>
      </div>
      <div class="panel">
        <h3 style="margin-top:0;">Raw JSON</h3>
        <pre id="output">Waiting...</pre>
      </div>
    </div>
  </div>

<script>
const API = window.location.origin;
let radar;

function statusClass(v, passed) {
  if (passed === false || (v !== null && v < 0.5)) return "bad";
  if (passed === true && v !== null && v >= 0.7) return "ok";
  return "warn";
}
function statusText(v, passed) {
  if (passed === false || (v !== null && v < 0.5)) return "RISK";
  if (passed === true && v !== null && v >= 0.7) return "GOOD";
  return "MEDIUM";
}
function pct(v) {
  if (v === null || v === undefined) return "N/A";
  return Math.round(v * 100) + "%";
}

function renderSignals(signals) {
  const wrap = document.getElementById("signals");
  wrap.innerHTML = "";
  if (!signals || !signals.length) {
    wrap.innerHTML = '<div class="small">No signals found.</div>';
    return;
  }

  signals.forEach(s => {
    const cls = statusClass(s.numeric_value, s.passed);
    const st = statusText(s.numeric_value, s.passed);
    const div = document.createElement("div");
    div.className = "signal";
    div.innerHTML = `
      <span class="badge ${cls}">${st}</span>
      <h4>${s.key}</h4>
      <div class="small">Normalized: <strong>${pct(s.numeric_value)}</strong></div>
      <div class="small">Weight: <strong>${s.weight}</strong></div>
      <div class="small" style="margin-top:6px;">${s.rationale || ""}</div>
    `;
    wrap.appendChild(div);
  });
}

function renderRadar(signals) {
  const labels = signals.map(s => s.key);
  const data = signals.map(s => s.numeric_value == null ? 0.35 : s.numeric_value);

  const ctx = document.getElementById("radarChart");
  if (radar) radar.destroy();

  radar = new Chart(ctx, {
    type: "radar",
    data: {
      labels,
      datasets: [{
        label: "Signal Strength",
        data,
        fill: true,
        backgroundColor: "rgba(79,70,229,0.25)",
        borderColor: "rgba(99,102,241,1)",
        pointBackgroundColor: "rgba(147,197,253,1)"
      }]
    },
    options: {
      scales: {
        r: {
          min: 0, max: 1,
          angleLines: { color: "rgba(148,163,184,.2)" },
          grid: { color: "rgba(148,163,184,.2)" },
          pointLabels: { color: "#cbd5e1", font: { size: 10 } },
          ticks: { backdropColor: "transparent", color: "#94a3b8", stepSize: 0.2 }
        }
      },
      plugins: {
        legend: { labels: { color: "#cbd5e1" } }
      }
    }
  });
}

async function runFlow() {
  const companyName = document.getElementById("companyName").value.trim();
  const website = document.getElementById("website").value.trim();
  const extra = document.getElementById("extraUrls").value.trim();

  const output = document.getElementById("output");
  const links = document.getElementById("links");

  if (!companyName || !website) {
    alert("Please provide company name and website.");
    return;
  }

  output.textContent = "Running...";
  links.innerHTML = "Generating...";
  document.getElementById("signals").innerHTML = "";

  try {
    const extra_urls = extra ? extra.split(",").map(s => s.trim()).filter(Boolean) : [];

    // 1) intake
    const intakeRes = await fetch(`${API}/intake/company`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ company_name: companyName, website, extra_urls })
    });
    const intake = await intakeRes.json();
    if (!intakeRes.ok) throw new Error(JSON.stringify(intake));
    const companyId = intake.company.id;

    // 2) run assessment
    const runRes = await fetch(`${API}/assessment/run/${companyId}`, { method: "POST" });
    const run = await runRes.json();
    if (!runRes.ok) throw new Error(JSON.stringify(run));
    const assessmentId = run.assessment_id;

    // 3) get details
    const detailsRes = await fetch(`${API}/assessment/${assessmentId}`);
    const details = await detailsRes.json();
    if (!detailsRes.ok) throw new Error(JSON.stringify(details));

    // KPIs
    document.getElementById("kpiScore").textContent = `${details.score}/100`;
    document.getElementById("kpiConfidence").textContent = `${details.confidence}%`;
    document.getElementById("kpiSignals").textContent = `${(details.signals || []).length}`;
    document.getElementById("kpiAssessment").textContent = `${assessmentId}`;

    // signal cards + radar
    renderSignals(details.signals || []);
    renderRadar(details.signals || []);

    // report links
    links.innerHTML = `
      <p><a target="_blank" href="${API}/report/markdown/${assessmentId}">Open Markdown report</a></p>
      <p><a target="_blank" href="${API}/report/pdf/${assessmentId}">Download PDF report</a></p>
      <p class="small">Company ID: ${companyId}</p>
    `;

    output.textContent = JSON.stringify({ intake, run, details }, null, 2);
  } catch (e) {
    output.textContent = "Error:\\n" + e.message;
    links.innerHTML = '<span class="badge bad">FAILED</span>';
  }
}
</script>
</body>
</html>
"""