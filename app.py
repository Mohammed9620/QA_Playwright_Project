import os
import re
import json
import subprocess
import threading
import time
import uuid
from datetime import datetime
from flask import Flask, render_template, request, send_file, Response, jsonify

app = Flask(__name__)

# ──────────────────────────────────────────────
#  Scan type → pytest file mapping
# ──────────────────────────────────────────────
SCAN_MAP = {
    "login":      [("main_test.py",       "Login Test")],
    "bruteforce": [("test_credentials.py","Credential Bruteforce Probe")],
    "api":        [("test_api.py",        "API Health Check")],
    "auth":       [("test_auth.py",       "Broken Authentication Check")],
    "full": [
        ("main_test.py",        "Login Test"),
        ("test_credentials.py", "Credential Bruteforce Probe"),
        ("test_api.py",         "API Health Check"),
        ("test_auth.py",        "Broken Authentication Check"),
    ],
}

SCAN_LABELS = {
    "login":      "Login Test",
    "bruteforce": "Credential Bruteforce Probe",
    "api":        "API Health Check",
    "auth":       "Broken Authentication Check",
    "full":       "Full Scan",
}

# Metadata for the sidebar test suites (icon hint, test count per file)
SUITE_META = {
    "login":      {"icon": "login",  "tests": 2, "file": "main_test.py"},
    "bruteforce": {"icon": "key",    "tests": 1, "file": "test_credentials.py"},
    "api":        {"icon": "api",    "tests": 2, "file": "test_api.py"},
    "auth":       {"icon": "shield", "tests": 3, "file": "test_auth.py"},
}

REPORT_PATH = os.path.join(os.path.dirname(__file__), "report.html")

# In-memory store for finished scan results keyed by session id
_scan_results: dict[str, dict] = {}
_scan_lock = threading.Lock()


def parse_pytest_summary(output: str) -> dict:
    """Extract total / passed / failed counts from pytest terminal output."""
    summary = {"total": 0, "passed": 0, "failed": 0, "error": 0, "raw": ""}

    for line in output.splitlines():
        if re.search(r"\d+ (passed|failed|error)", line, re.IGNORECASE):
            summary["raw"] = line.strip()
            m_failed = re.search(r"(\d+) failed",  line, re.IGNORECASE)
            m_passed = re.search(r"(\d+) passed",  line, re.IGNORECASE)
            m_error  = re.search(r"(\d+) error",   line, re.IGNORECASE)
            summary["failed"] = int(m_failed.group(1)) if m_failed else 0
            summary["passed"] = int(m_passed.group(1)) if m_passed else 0
            summary["error"]  = int(m_error.group(1))  if m_error  else 0
            summary["total"]  = summary["passed"] + summary["failed"] + summary["error"]
            break

    return summary


# ──────────────────────────────────────────────
#  Routes
# ──────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/stream_scan")
def stream_scan():
    """
    Server-Sent Events endpoint.
    Query params: url, scan_type, session_id,
                  scan_strategy, username, password,
                  user_locator, pass_locator, login_locator
    Streams real-time log lines and progress events, then a final 'done' event.
    """
    target_url     = request.args.get("url", "").strip()
    scan_type      = request.args.get("scan_type", "login").strip()
    session_id     = request.args.get("session_id", str(uuid.uuid4()))
    scan_strategy  = request.args.get("scan_strategy", "external").strip()
    auth_username  = request.args.get("username", "").strip()
    auth_password  = request.args.get("password", "").strip()
    user_locator   = request.args.get("user_locator", "").strip()
    pass_locator   = request.args.get("pass_locator", "").strip()
    login_locator  = request.args.get("login_locator", "").strip()

    if not target_url:
        def err():
            yield "data: " + json.dumps({"type": "error", "message": "No target URL provided."}) + "\n\n"
        return Response(err(), mimetype="text/event-stream")

    if scan_type not in SCAN_MAP:
        def err():
            yield "data: " + json.dumps({"type": "error", "message": f"Unknown scan type: {scan_type}"}) + "\n\n"
        return Response(err(), mimetype="text/event-stream")

    test_files = SCAN_MAP[scan_type]

    def generate():
        current_env = os.environ.copy()
        current_env["TARGET_URL"] = target_url

        # Pass authenticated scan credentials if provided
        if scan_strategy == "authenticated" and auth_username:
            current_env["TEST_USER"] = auth_username
            current_env["TEST_PASS"] = auth_password
        if user_locator:
            current_env["USER_LOCATOR"] = user_locator
        if pass_locator:
            current_env["PASS_LOCATOR"] = pass_locator
        if login_locator:
            current_env["LOGIN_LOCATOR"] = login_locator

        total_passed = 0
        total_failed = 0
        total_error  = 0
        report_generated = False

        # Emit a 'start' event listing all files that will run
        yield "data: " + json.dumps({
            "type": "start",
            "files": [{"file": f, "label": lbl} for f, lbl in test_files],
        }) + "\n\n"

        for i, (test_file, label) in enumerate(test_files):
            is_last = (i == len(test_files) - 1)
            file_start_time = time.monotonic()

            # Build command — only attach the HTML reporter on the last file
            cmd = ["python", "-m", "pytest", test_file, "-v", "-s"]
            if is_last:
                cmd += [f"--html={REPORT_PATH}", "--self-contained-html"]

            try:
                # Use Popen for line-by-line streaming instead of subprocess.run
                proc = subprocess.Popen(
                    cmd,
                    env=current_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,  # line-buffered
                )

                output_lines = []
                for raw_line in proc.stdout:
                    line = raw_line.rstrip("\n").rstrip("\r")
                    output_lines.append(line)

                    # Stream each line as a 'log' SSE event with timestamp
                    if line.strip():  # skip blank lines
                        now = datetime.now()
                        yield "data: " + json.dumps({
                            "type": "log",
                            "file": test_file,
                            "label": label,
                            "line": line,
                            "timestamp": now.strftime("%H:%M:%S.") + now.strftime("%f")[:3],
                        }) + "\n\n"

                proc.wait(timeout=300)
                output = "\n".join(output_lines)
                summary = parse_pytest_summary(output)

                total_passed += summary["passed"]
                total_failed += summary["failed"]
                total_error  += summary["error"]

                status = "passed" if summary["failed"] == 0 and summary["error"] == 0 else "failed"
                elapsed_s = round(time.monotonic() - file_start_time, 1)
                if is_last:
                    report_generated = os.path.exists(REPORT_PATH)

                yield "data: " + json.dumps({
                    "type":      "progress",
                    "file":      test_file,
                    "label":     label,
                    "status":    status,
                    "passed":    summary["passed"],
                    "failed":    summary["failed"],
                    "error":     summary["error"],
                    "elapsed_s": elapsed_s,
                }) + "\n\n"

            except subprocess.TimeoutExpired:
                if proc and proc.poll() is None:
                    proc.kill()
                yield "data: " + json.dumps({
                    "type":   "progress",
                    "file":   test_file,
                    "label":  label,
                    "status": "timeout",
                    "passed": 0,
                    "failed": 0,
                    "error":  1,
                }) + "\n\n"
                total_error += 1

            except Exception as exc:
                yield "data: " + json.dumps({
                    "type":    "progress",
                    "file":    test_file,
                    "label":   label,
                    "status":  "error",
                    "message": str(exc),
                    "passed":  0,
                    "failed":  0,
                    "error":   1,
                }) + "\n\n"
                total_error += 1

        # Store final result so the frontend can fetch it
        final = {
            "scan_label":     SCAN_LABELS.get(scan_type, scan_type),
            "target_url":     target_url,
            "report_exists":  report_generated,
            "summary": {
                "total":  total_passed + total_failed + total_error,
                "passed": total_passed,
                "failed": total_failed,
                "error":  total_error,
            },
        }
        with _scan_lock:
            _scan_results[session_id] = final

        yield "data: " + json.dumps({
            "type":       "done",
            "session_id": session_id,
            **final,
        }) + "\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/scan_result/<session_id>")
def scan_result(session_id):
    """Return the stored scan result for a given session (used as fallback)."""
    with _scan_lock:
        data = _scan_results.get(session_id)
    if not data:
        return jsonify({"error": "No result found for this session."}), 404
    return jsonify(data)


@app.route("/results")
def results():
    """Render the results page; data comes from query-string params set by JS."""
    summary = {
        "total":  int(request.args.get("total",  0)),
        "passed": int(request.args.get("passed", 0)),
        "failed": int(request.args.get("failed", 0)),
        "error":  int(request.args.get("error",  0)),
    }
    return render_template(
        "results.html",
        scan_label=request.args.get("scan_label", "Scan"),
        target_url=request.args.get("target_url", ""),
        summary=summary,
        report_exists=request.args.get("report_exists", "0") == "1",
    )


def get_report_theme_css():
    """Return a <style> block + theme toggle script to inject into report.html."""
    return '''
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
/* ── Report Theme Override ── */
:root {
    --r-bg: #0d1117;
    --r-surface: #161b22;
    --r-border: #30363d;
    --r-text: #e6edf3;
    --r-text-muted: #8b949e;
    --r-success: #3fb950;
    --r-danger: #f85149;
    --r-warning: #d29922;
    --r-accent: #58a6ff;
    --r-font: 'Inter', system-ui, sans-serif;
    --r-mono: 'JetBrains Mono', monospace;
}
[data-theme="light"] {
    --r-bg: #ffffff;
    --r-surface: #f6f8fa;
    --r-border: #d1d9e0;
    --r-text: #1f2328;
    --r-text-muted: #636c76;
    --r-success: #1a7f37;
    --r-danger: #cf222e;
    --r-warning: #9a6700;
    --r-accent: #0969da;
}
body {
    font-family: var(--r-font) !important;
    font-size: 14px !important;
    background: var(--r-bg) !important;
    color: var(--r-text) !important;
    padding: 24px 32px !important;
    min-width: auto !important;
}
h1 { font-size: 20px !important; font-weight: 700 !important; color: var(--r-text) !important; margin-bottom: 4px !important; }
h2 { font-size: 15px !important; font-weight: 600 !important; color: var(--r-text) !important; }
p { color: var(--r-text-muted) !important; font-size: 13px !important; }
a { color: var(--r-accent) !important; }
table { border-collapse: collapse !important; }
#environment td { padding: 8px 12px !important; border: 1px solid var(--r-border) !important; color: var(--r-text) !important; font-size: 13px !important; }
#environment tr:nth-child(odd) { background: var(--r-surface) !important; }
#environment tr:nth-child(even) { background: var(--r-bg) !important; }
span.passed, .passed .col-result { color: var(--r-success) !important; }
span.failed, .failed .col-result, span.error, .error .col-result { color: var(--r-danger) !important; }
span.skipped, .skipped .col-result, span.xfailed, .xfailed .col-result { color: var(--r-warning) !important; }
#results-table { border: 1px solid var(--r-border) !important; color: var(--r-text) !important; font-size: 13px !important; }
#results-table th, #results-table td { padding: 8px 12px !important; border: 1px solid var(--r-border) !important; }
#results-table th { background: var(--r-surface) !important; font-weight: 600 !important; color: var(--r-text) !important; }
.logwrapper { background: var(--r-surface) !important; border: 1px solid var(--r-border) !important; border-radius: 4px !important; }
.logwrapper .log { font-family: var(--r-mono) !important; font-size: 12px !important; color: var(--r-text) !important; background: var(--r-surface) !important; border: none !important; padding: 12px !important; }
.logwrapper .log .error { color: var(--r-danger) !important; }
.logwrapper .logexpander { background: var(--r-bg) !important; color: var(--r-text-muted) !important; border-color: var(--r-border) !important; font-size: 12px !important; }
.logwrapper .logexpander:hover { color: var(--r-text) !important; border-color: var(--r-text-muted) !important; }
.summary__data { flex: none !important; }
.controls { flex-wrap: wrap !important; gap: 8px !important; }
.filters, .collapse { flex-wrap: wrap !important; }
.filters span { color: var(--r-text-muted) !important; font-size: 13px !important; }
.filters button, .collapse button { color: var(--r-accent) !important; font-size: 13px !important; }
.summary__reload__button { background-color: var(--r-success) !important; border-radius: 4px !important; }
.sortable.desc:after { border-color: var(--r-success) transparent transparent !important; }
.sortable.asc:after { border-color: transparent transparent var(--r-success) !important; }
.collapsible td:not(.col-links):hover::after { color: var(--r-text-muted) !important; }
.col-result:hover::after, .col-result.collapsed:hover::after { font-size: 11px !important; color: var(--r-text-muted) !important; }
#environment-header h2:hover::after, #environment-header.collapsed h2:hover::after { color: var(--r-text-muted) !important; font-size: 11px !important; }
/* Theme toggle button */
.report-theme-toggle { position: fixed; top: 16px; right: 16px; z-index: 9999; background: var(--r-surface); border: 1px solid var(--r-border); color: var(--r-text-muted); width: 36px; height: 36px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 16px; transition: all 0.2s; }
.report-theme-toggle:hover { color: var(--r-text); border-color: var(--r-text-muted); }
</style>
<script>
(function() {
    var saved = localStorage.getItem("qa-theme") || "dark";
    document.documentElement.setAttribute("data-theme", saved);
    document.addEventListener("DOMContentLoaded", function() {
        var btn = document.createElement("button");
        btn.className = "report-theme-toggle";
        btn.innerHTML = saved === "dark" ? "☀️" : "🌙";
        btn.title = "Toggle theme";
        btn.onclick = function() {
            var current = document.documentElement.getAttribute("data-theme");
            var next = current === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", next);
            localStorage.setItem("qa-theme", next);
            btn.innerHTML = next === "dark" ? "☀️" : "🌙";
        };
        document.body.appendChild(btn);
    });
})();
</script>
'''


@app.route("/view_report")
def view_report():
    """Serve report.html with injected theme CSS (opens in new tab)."""
    if not os.path.exists(REPORT_PATH):
        return "<h2>No report found. Please run a scan first.</h2>", 404

    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # Inject theme CSS and toggle script before </head>
    theme_css = get_report_theme_css()
    html = html.replace("</head>", theme_css + "\n</head>")

    return html


@app.route("/download_report")
def download_report():
    """Force-download report.html."""
    if not os.path.exists(REPORT_PATH):
        return "<h2>No report found. Please run a scan first.</h2>", 404
    return send_file(REPORT_PATH, as_attachment=True, download_name="qa_report.html")


if __name__ == "__main__":
    app.run(debug=True, threaded=True)