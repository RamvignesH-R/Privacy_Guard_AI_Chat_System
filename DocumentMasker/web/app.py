"""
web/app.py
Medical PHI Masker — Web Interface
Run: python web/app.py
"""

import sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from utils.ocr_extractor import extract_text

app   = Flask(__name__)
CORS(app)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

print("DocumentMasker web app starting. Will use port 8000 for masking logic.")
import requests


# ── HTML ──────────────────────────────────────────────────────────────────────
PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  /* Reset */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  /* Tokens */
  :root {
    --bg:        #f5f5f4;
    --surface:   #ffffff;
    --border:    #e2e2e0;
    --border-dk: #c8c8c5;
    --text:      #1a1a18;
    --muted:     #6b6b68;
    --accent:    #1a3a5c;
    --accent-lt: #e8eef5;
    --danger:    #8b1a1a;
    --mono:      'Courier New', Courier, monospace;
    --sans:      'Segoe UI', system-ui, -apple-system, sans-serif;
    --radius:    4px;
  }

  html, body {
    height: 100%;
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    font-size: 14px;
    line-height: 1.6;
  }

  /* Layout */
  .shell {
    display: grid;
    grid-template-rows: auto 1fr auto;
    min-height: 100vh;
  }

  /* Header */
  header {
    background: var(--accent);
    color: #fff;
    padding: 0 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 52px;
    border-bottom: 1px solid rgba(0,0,0,.2);
  }
  header .brand {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: .04em;
    text-transform: uppercase;
    color: #fff;
  }
  header .sub {
    font-size: 11px;
    color: rgba(255,255,255,.55);
    letter-spacing: .03em;
    text-transform: uppercase;
  }

  /* Main content */
  main {
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
    width: 100%;
  }

  /* Two-column layout */
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }
  @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }

  /* Cards */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }
  .card-header {
    padding: .75rem 1rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .card-title {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: var(--muted);
  }
  .card-body { padding: 1rem; }

  /* Drop zone */
  .drop-zone {
    border: 1px dashed var(--border-dk);
    border-radius: var(--radius);
    padding: 2.5rem 1rem;
    text-align: center;
    cursor: pointer;
    transition: border-color .15s, background .15s;
    background: var(--bg);
  }
  .drop-zone:hover, .drop-zone.over {
    border-color: var(--accent);
    background: var(--accent-lt);
  }
  .drop-zone .icon {
    display: block;
    width: 36px;
    height: 36px;
    margin: 0 auto .75rem;
    opacity: .35;
  }
  .drop-zone .label {
    font-size: 13px;
    color: var(--muted);
  }
  .drop-zone .hint {
    font-size: 11px;
    color: var(--border-dk);
    margin-top: .35rem;
    letter-spacing: .02em;
  }
  #file-input { display: none; }
  .file-chosen {
    margin-top: .75rem;
    font-size: 12px;
    color: var(--accent);
    min-height: 18px;
  }

  /* Button */
  .btn {
    display: block;
    width: 100%;
    margin-top: 1rem;
    padding: .6rem 1rem;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: var(--radius);
    font-family: var(--sans);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: .05em;
    text-transform: uppercase;
    cursor: pointer;
    transition: opacity .15s;
  }
  .btn:hover  { opacity: .85; }
  .btn:disabled { opacity: .4; cursor: not-allowed; }

  .btn-sm {
    display: inline-block;
    padding: .35rem .9rem;
    background: transparent;
    color: var(--accent);
    border: 1px solid var(--accent);
    border-radius: var(--radius);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .05em;
    text-transform: uppercase;
    cursor: pointer;
    transition: background .15s, color .15s;
    text-decoration: none;
  }
  .btn-sm:hover { background: var(--accent); color: #fff; }

  /* Status bar */
  .status-bar {
    margin-top: 1rem;
    padding: .5rem .75rem;
    font-size: 12px;
    border-radius: var(--radius);
    display: none;
  }
  .status-bar.loading {
    display: flex;
    align-items: center;
    gap: .5rem;
    background: var(--accent-lt);
    color: var(--accent);
    border: 1px solid #c0d4ec;
  }
  .status-bar.error {
    display: block;
    background: #fdf0f0;
    color: var(--danger);
    border: 1px solid #e8c0c0;
  }
  .spinner {
    width: 14px; height: 14px;
    border: 2px solid #c0d4ec;
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin .7s linear infinite;
    flex-shrink: 0;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Output panel */
  .output-panel { display: none; }

  /* Stats row */
  .stats-row {
    display: flex;
    flex-wrap: wrap;
    gap: .5rem;
    padding: 1rem;
    border-bottom: 1px solid var(--border);
    background: var(--bg);
  }
  .stat-pill {
    padding: .25rem .6rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 2px;
    font-size: 11px;
    color: var(--muted);
  }
  .stat-pill span {
    font-weight: 700;
    color: var(--accent);
    margin-right: 3px;
  }
  .total-badge {
    margin-left: auto;
    padding: .25rem .6rem;
    background: var(--accent);
    color: #fff;
    border-radius: 2px;
    font-size: 11px;
    font-weight: 700;
  }

  /* Text output */
  .text-out {
    padding: 1rem;
    font-family: var(--mono);
    font-size: 12px;
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 420px;
    overflow-y: auto;
    background: var(--surface);
  }
  .text-out .redacted {
    background: #1a3a5c;
    color: #fff;
    padding: 1px 5px;
    border-radius: 2px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .02em;
  }

  /* Action row */
  .action-row {
    padding: .75rem 1rem;
    border-top: 1px solid var(--border);
    display: flex;
    gap: .5rem;
    align-items: center;
  }

  /* Info panel */
  .info-list {
    list-style: none;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: .35rem;
  }
  .info-list li {
    font-size: 12px;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: .4rem;
  }
  .info-list li::before {
    content: '';
    display: inline-block;
    width: 6px; height: 6px;
    background: var(--accent);
    border-radius: 50%;
    flex-shrink: 0;
  }

  /* Divider */
  .divider {
    margin: 1.5rem 0;
    border: none;
    border-top: 1px solid var(--border);
  }

  /* Section label */
  .section-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: var(--muted);
    margin-bottom: .6rem;
  }

  /* Footer */
  footer {
    padding: .75rem 2rem;
    border-top: 1px solid var(--border);
    font-size: 11px;
    color: var(--muted);
    display: flex;
    justify-content: space-between;
    background: var(--surface);
  }
</style>
</head>
<body>
<div class="shell">

<main>

  <!-- Top info bar -->
  <div text-align:center>
  <h3> MEDICAL DATA MASKER </h3>
  </div>

  <div class="grid">

    <!-- Left column: upload -->
    <div>
      <div class="card">
        <div class="card-header">
          <span class="card-title">Document Upload</span>
        </div>
        <div class="card-body">

          <div class="drop-zone" id="drop-zone"
               onclick="document.getElementById('file-input').click()">
            <svg class="icon" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0
                       2-2V8z"/><polyline points="14 2 14 8 20 8"/>
              <line x1="12" y1="18" x2="12" y2="12"/>
              <line x1="9" y1="15" x2="15" y2="15"/>
            </svg>
            <div class="label">Click to browse or drag a file here</div>
            <div class="hint">TXT &nbsp;|&nbsp; PDF &nbsp;|&nbsp;
                              PNG &nbsp;|&nbsp; DOCX</div>
          </div>

          <input type="file" id="file-input"
                 accept=".txt,.pdf,.png,.docx">
          <div class="file-chosen" id="file-name"></div>

          <button class="btn" id="run-btn" disabled onclick="runMasker()">
            Mask Document
          </button>

          <div class="status-bar loading" id="status-loading">
            Processing document
          </div>
          <div class="status-bar error" id="status-error"></div>

        </div>
      </div>

      <hr class="divider">

      <!-- Entity reference card -->
      <div class="card">
        <div class="card-header">
          <span class="card-title">Entities Detected and Masked</span>
        </div>
        <div class="card-body">
          <ul class="info-list">
            <li>Patient Name</li>
            <li>Date of Birth</li>
            <li>Age</li>
            <li>Phone Number</li>
            <li>Email Address</li>
            <li>Address</li>
            <li>Aadhaar Number</li>
            <li>MRN</li>
            <li>IP Number</li>
            <li>Doctor Name</li>
            <li>Hospital Name</li>
            <li>Dates (Admission etc.)</li>
            <li>Diagnosis</li>
            <li>Medication</li>
            <li>Blood Group</li>
          </ul>

          <hr class="divider" style="margin:.9rem 0">
          <div class="section-label">Detection Method</div>
          
        </div>
      </div>
    </div>

    <!-- Right column: output -->
    <div>
      <div class="card" style="height:100%">
        <div class="card-header">
          <span class="card-title">Masked Output</span>
          <div id="output-actions" style="display:none; gap:.5rem; display:none">
            <button class="btn-sm" onclick="copyOutput()">Copy</button>
            <button class="btn-sm" onclick="downloadTxt()">Download TXT</button>
          </div>
        </div>

        <!-- placeholder -->
        <div id="placeholder" style="padding:3rem 1rem; text-align:center; color:var(--border-dk)">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="1" opacity=".4"
               style="margin:0 auto .75rem; display:block">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <line x1="9" y1="9" x2="15" y2="9"/>
            <line x1="9" y1="13" x2="15" y2="13"/>
            <line x1="9" y1="17" x2="13" y2="17"/>
          </svg>
          <div style="font-size:12px">
            Upload a document to see the redacted output here.
          </div>
        </div>

        <!-- results -->
        <div class="output-panel" id="output-panel">
          <div class="stats-row" id="stats-row">
            <!-- pills injected by JS -->
          </div>
          <div class="text-out" id="text-out"></div>
          <div class="action-row">
            <button class="btn-sm" onclick="copyOutput()">Copy Text</button>
            <button class="btn-sm" onclick="downloadTxt()">Download TXT</button>
            <span style="margin-left:auto; font-size:11px; color:var(--muted)"
                  id="char-count"></span>
          </div>
        </div>

      </div>
    </div>

  </div><!-- /grid -->
</main>


</div><!-- /shell -->

<script>
let maskedText = "";

// ── File input ───────────────────────────────────────────────────────────────
const fileInput = document.getElementById("file-input");
const dropZone  = document.getElementById("drop-zone");
const runBtn    = document.getElementById("run-btn");
const fileName  = document.getElementById("file-name");

fileInput.addEventListener("change", () => {
  if (fileInput.files.length) {
    fileName.textContent = fileInput.files[0].name;
    runBtn.disabled = false;
  }
});

dropZone.addEventListener("dragover", e => {
  e.preventDefault();
  dropZone.classList.add("over");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("over"));
dropZone.addEventListener("drop", e => {
  e.preventDefault();
  dropZone.classList.remove("over");
  fileInput.files = e.dataTransfer.files;
  if (fileInput.files.length) {
    fileName.textContent = fileInput.files[0].name;
    runBtn.disabled = false;
  }
});

// ── Run ──────────────────────────────────────────────────────────────────────
async function runMasker() {
  const file = fileInput.files[0];
  if (!file) return;

  setLoading(true);
  clearOutput();

  const fd = new FormData();
  fd.append("file", file);

  try {
    const res  = await fetch("/mask", { method: "POST", body: fd });
    const data = await res.json();
    if (data.error) { showError(data.error); return; }
    renderOutput(data);
  } catch (e) {
    showError("Request failed: " + e.message);
  } finally {
    setLoading(false);
  }
}

// ── Render output ─────────────────────────────────────────────────────────────
function renderOutput(data) {
  maskedText = data.masked;

  // Stats pills
  const statsRow = document.getElementById("stats-row");
  statsRow.innerHTML = "";

  const sorted = Object.entries(data.entities_found)
    .sort((a, b) => b[1] - a[1]);

  sorted.forEach(([k, v]) => {
    const pill = document.createElement("div");
    pill.className = "stat-pill";
    pill.innerHTML = `<span>${v}</span>${k.replace(/_/g, " ")}`;
    statsRow.appendChild(pill);
  });

  const badge = document.createElement("div");
  badge.className = "total-badge";
  badge.textContent = `${data.total_redactions} total`;
  statsRow.appendChild(badge);

  // Highlighted text — wrap all [LABEL] patterns
  const textEl = document.getElementById("text-out");
  const safe   = escapeHtml(maskedText);
  const highlighted = safe.replace(
    /\[([A-Z][A-Z\s]+)\]/g,
    '<span class="redacted">[$1]</span>'
  );
  textEl.innerHTML = highlighted;

  document.getElementById("char-count").textContent =
    `${maskedText.length.toLocaleString()} characters`;

  document.getElementById("placeholder").style.display  = "none";
  document.getElementById("output-panel").style.display = "block";
}

function escapeHtml(t) {
  return t.replace(/&/g,"&amp;").replace(/</g,"&lt;")
          .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function setLoading(on) {
  document.getElementById("status-loading").style.display = on ? "flex" : "none";
  runBtn.disabled = on;
}
function showError(msg) {
  const el = document.getElementById("status-error");
  el.textContent = "Error: " + msg;
  el.style.display = "block";
}
function clearOutput() {
  document.getElementById("status-error").style.display = "none";
  document.getElementById("output-panel").style.display = "none";
  document.getElementById("placeholder").style.display  = "block";
}

function copyOutput() {
  navigator.clipboard.writeText(maskedText)
    .then(() => alert("Copied to clipboard."))
    .catch(() => alert("Copy failed — please select and copy manually."));
}
function downloadTxt() {
  const blob = new Blob([maskedText], { type: "text/plain" });
  const a    = document.createElement("a");
  a.href     = URL.createObjectURL(blob);
  a.download = "masked_output.txt";
  a.click();
}
</script>
</body>
</html>
"""

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/mask", methods=["POST"])
def mask():
    if "file" not in request.files:
        return jsonify({"error": "No file was uploaded."}), 400

    f     = request.files["file"]
    fname = f"{uuid.uuid4().hex}_{f.filename}"
    fpath = os.path.join(UPLOAD_DIR, fname)
    f.save(fpath)

    try:
        text   = extract_text(fpath)
        
        # Forward the text to our unified Privacy Guard API for masking!
        import requests
        chat_api_url = os.environ.get("CHAT_API_URL", "http://localhost:8000")
        response = requests.post(f"{chat_api_url}/mask_document", json={"text": text})
        
        if response.status_code == 200:
            result = response.json()
            return jsonify(result)
        else:
            return jsonify({"error": "Failed to communicate with main Privacy Guard API"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(fpath):
            os.remove(fpath)


@app.route("/health")
def health():
    return jsonify({"status": "ok",
                    "model": os.getenv("MODEL_TYPE", "bilstm")})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)