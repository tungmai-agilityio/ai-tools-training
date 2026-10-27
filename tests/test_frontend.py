import shutil
import subprocess

import pytest


def test_index_page_is_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Clinic Booking" in r.text


def test_patients_endpoint_lists_seed_patients(client):
    body = client.get("/patients").json()
    assert [p["id"] for p in body] == [1, 2, 3]
    assert body[0]["insured"] is True


def test_index_page_offers_reschedule_for_scheduled_appointments(client):
    page = client.get("/static/app.js").text
    assert 'btn("reschedule", "Reschedule")' in page
    assert "/reschedule`" in page


def test_reschedule_picker_offers_the_appointments_own_slots(client):
    # free_slots() counts the appointment being moved as busy; the page must add its own starts back.
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")  # ponytail: JS check needs node; no JS test runner in this repo
    page = client.get("/static/app.js").text
    start = page.index("function withOwnSlots")
    fn = page[start:page.index("\n}\n", start) + 2]
    script = 'const CLINIC_TZ = "America/New_York";\n' + fn + """
const appt = { start: "2026-10-14T14:00:00Z", duration_minutes: 60 };  // Wed 10:00-11:00 NY
const got = withOwnSlots(["2026-10-14T13:00:00+00:00", "2026-10-14T15:00:00+00:00"], appt, "2026-10-14");
const want = ["2026-10-14T13:00:00Z", "2026-10-14T14:00:00Z", "2026-10-14T14:30:00Z", "2026-10-14T15:00:00Z"];
if (JSON.stringify(got.map((s) => new Date(s).toISOString().replace(".000", ""))) !== JSON.stringify(want)) throw new Error(JSON.stringify(got));
if (withOwnSlots(["x"], appt, "2026-10-15").length !== 1) throw new Error("added slots on another day");
if (withOwnSlots(["x"], null, "2026-10-14").length !== 1) throw new Error("added slots outside reschedule mode");
"""
    r = subprocess.run([node, "-e", script], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def _node():
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")  # ponytail: JS check needs node; no JS test runner in this repo
    return node


def _run_js(client, names, body):
    """Run page functions (by 'function name' marker) plus `body` in node; fail with node's stderr."""
    page = client.get("/static/app.js").text
    fns = ""
    for marker in names:
        start = page.index(marker)
        end = page.index("\n", start) if marker.startswith("const") else page.index("\n}\n", start) + 2
        fns += page[start:end] + "\n"
    r = subprocess.run([_node(), "-e", fns + body], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_index_page_has_a_revenue_screen(client):
    html = client.get("/").text
    page = client.get("/static/app.js").text
    assert 'href="#revenue"' in html
    assert 'id="screen-revenue"' in html
    assert '"revenue"' in page.split("const SCREENS = ", 1)[1].split("\n", 1)[0]
    assert "sessionStorage" not in page
    assert all("cb-theme" in line for line in page.splitlines() if "localStorage" in line)


def test_revenue_range_check_allows_366_days_and_rejects_367(client):
    _run_js(client, ["const keyDate", "function revenueRangeError"], """
const ok = (a, b) => { if (revenueRangeError(a, b)) throw new Error(`${a}..${b}: ${revenueRangeError(a, b)}`); };
const bad = (a, b) => { if (!revenueRangeError(a, b)) throw new Error(`${a}..${b} accepted`); };
bad("", "2026-10-13"); bad("2026-10-13", ""); bad("2026-10-13", "12345-01-01"); bad("12345-01-01", "2026-10-13"); bad("2026-10-14", "2026-10-13");
ok("2026-10-13", "2026-10-13");
ok("2028-01-01", "2028-12-31");   // 366 days inclusive (leap year)
bad("2028-01-01", "2029-01-01");  // 367 days inclusive
ok("2027-03-01", "2028-02-29");   // 366 days inclusive, spans a leap day
bad("2027-03-01", "2028-03-01");
ok("2026-03-08", "2027-03-08");   // 366 days inclusive; keys are noon UTC, so DST cannot matter
bad("2026-03-08", "2027-03-09");
""")


def test_api_sends_caller_headers_with_json_content_type(client):
    _run_js(client, ["async function api"], """
let sent;
globalThis.fetch = async (path, o) => { sent = o; return { ok: true, status: 200, json: async () => ({}) }; };
(async () => {
  await api("/x", { method: "POST", body: "{}", headers: { "X-Test": "t" } });
  if (JSON.stringify(sent.headers) !== JSON.stringify({ "Content-Type": "application/json", "X-Test": "t" })) throw new Error(JSON.stringify(sent.headers));
  await api("/x");
  if (JSON.stringify(sent.headers) !== "{}") throw new Error(JSON.stringify(sent.headers));
  await api("/x", { headers: { "X-Test": "t" } });
  if (JSON.stringify(sent.headers) !== JSON.stringify({ "X-Test": "t" })) throw new Error(JSON.stringify(sent.headers));
})().catch((e) => { console.error(e); process.exit(1); });
""")


def test_api_error_carries_http_status(client):
    _run_js(client, ["async function api"], """
globalThis.fetch = async () => ({ ok: false, status: 403, statusText: "Forbidden", json: async () => ({ detail: "Administrator required" }) });
(async () => {
  try { await api("/x"); } catch (e) {
    if (e.status !== 403 || e.message !== "403 · Administrator required") throw new Error(e.status + " " + e.message);
    return;
  }
  throw new Error("did not throw");
})().catch((e) => { console.error(e); process.exit(1); });
""")


def test_revenue_report_renders_server_totals_and_escapes_doctor_names(client):
    _run_js(client, ["function esc", "const money", "const CLINIC_TZ", "const fmtDay", "const fmtTime", "const fmtWhen", "const keyDate", "const fmtKey", "function renderRevenue"], """
globalThis.document = { createElement: () => ({ set textContent(v) { this.innerHTML = String(v).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); } }) };
const out = {};
globalThis.$ = () => out;
const row = { consultation_cents: 39997, penalty_cents: 0, total_cents: 39997 };
renderRevenue({ from: "2026-10-01", to: "2026-10-13", at: Date.UTC(2026, 9, 13, 14), data: {
  totals: row, by_doctor: [{ ...row, doctor_name: "<b>x</b>" }], by_day: [{ ...row, date: "2026-10-13" }] } });
const html = out.innerHTML;
if (!html.includes("$399.97")) throw new Error("total not shown");
if (html.includes("<b>x</b>") || !html.includes("&lt;b&gt;x&lt;/b&gt;")) throw new Error("doctor name not escaped");
""")
