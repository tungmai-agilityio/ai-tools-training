"""Browser smoke test for the web app (T-011). Optional: needs requirements-dev.txt and
`playwright install chromium`; skipped otherwise, so plain `pytest` stays dependency-free."""
import contextlib
import os
import re
import socket
import threading
import time
from pathlib import Path

import pytest

# REQUIRE_BROWSER=1 (CI) turns every "browser not available" skip into a failure.
REQUIRE_BROWSER = os.environ.get("REQUIRE_BROWSER") == "1"
SHOTS = Path("test-artifacts/screenshots")
SIZES = {"desktop": (1280, 800), "phone": (375, 812)}
CSP_MARK = "Content Security Policy"

if not REQUIRE_BROWSER:
    pytest.importorskip("playwright.sync_api")
    pytest.importorskip("uvicorn")
from playwright import sync_api  # noqa: E402
import uvicorn  # noqa: E402

from tests.conftest import FIXED_NOW
from tests.helpers import book


@pytest.fixture
def base_url(client):  # `client` resets the store and freezes the clock (Tue 2026-10-13 10:00 NY)
    from app.main import app

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True


PASSWORD = "correct horse battery"  # tests.helpers.make_user default


@contextlib.contextmanager
def _browser_page(base_url, username):
    """A page signed in as `username` through POST /auth/login on the context's own cookie jar."""
    with sync_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:  # browser binary not installed
            if REQUIRE_BROWSER:
                pytest.fail(f"chromium not available: {e}")
            pytest.skip(f"chromium not available: {e}")
        # A browser far from New York: every time on screen must still be clinic time (NFR-2).
        context = browser.new_context(timezone_id="Asia/Ho_Chi_Minh", base_url=base_url)
        r = context.request.post("/auth/login", data={"username": username, "password": PASSWORD})
        assert r.ok, r.text()
        pg = context.new_page()
        pg.clock.set_fixed_time(FIXED_NOW)
        pg.csp_violations = []
        pg.on("console", lambda m: pg.csp_violations.append(m.text) if CSP_MARK in m.text else None)
        yield pg
        browser.close()
        assert not pg.csp_violations, f"CSP violation: {pg.csp_violations}"


@pytest.fixture
def page(base_url, client):  # `client` created the "testadmin" admin
    with _browser_page(base_url, "testadmin") as pg:
        yield pg


@pytest.fixture
def admin_page(base_url, anon_client):
    from tests.helpers import make_user

    make_user(username="admin1", role="admin")
    with _browser_page(base_url, "admin1") as pg:
        yield pg


@pytest.fixture
def staff_page(base_url, anon_client):
    from tests.helpers import make_user

    make_user(username="nurse1")
    with _browser_page(base_url, "nurse1") as pg:
        yield pg


@pytest.fixture
def snap(request):
    """snap(name): save <test>-<name>-desktop.png and -phone.png, masking password and token inputs."""
    SHOTS.mkdir(parents=True, exist_ok=True)

    def take(name):
        # the test's own page fixture (a second one would start a second Playwright in the same thread)
        page = request.getfixturevalue(next(f for f in ("page", "admin_page", "staff_page") if f in request.fixturenames))
        keep = page.viewport_size
        for label, (w, h) in SIZES.items():
            page.set_viewport_size({"width": w, "height": h})
            test = re.sub(r"\W+", "-", request.node.name).strip("-")
            page.screenshot(
                path=str(SHOTS / f"{test}-{name}-{label}.png"),
                animations="disabled",
                mask=[page.locator("input[type=password], input[name*=token i], input[id*=token i]")],
            )
        if keep:
            page.set_viewport_size(keep)

    return take


def test_booking_shows_summary_then_fee_toast_in_clinic_time(page):
    page.goto("/")
    page.fill("#doctor", "Dr. James Carter")
    page.fill("#patient", "Alice Johnson")
    page.get_by_role("button", name="Wed 14 Oct, 9:00 AM").click()  # tomorrow is selected by default
    summary = page.locator("#summary")
    sync_api.expect(summary).to_contain_text("Alice Johnson Insured")
    sync_api.expect(summary).to_contain_text("Wed 14 Oct, 9:00 AM")
    page.get_by_role("button", name="Confirm booking").click()
    sync_api.expect(page.locator(".cb-toast--ok")).to_contain_text("Booked #1, Wed 14 Oct, 9:00 AM")
    sync_api.expect(page.locator(".cb-toast--ok")).to_contain_text("Fee $120.00")  # 150.00 - 20% insured


@pytest.mark.parametrize("screen", ["book", "appointments", "today", "revenue", "account", "users"])
def test_no_sideways_scroll_on_a_phone(client, page, screen):
    book(client, "2026-10-13T11:00:00-04:00")  # gives Today a timeline block
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(f"/#{screen}")
    page.wait_for_load_state("networkidle")
    if screen == "today":
        page.get_by_role("radio", name="Timeline").check()  # phones open in List; the wide timeline is the risk
    assert page.evaluate("document.documentElement.scrollWidth") <= 375


def test_revenue_screen_defaults_to_current_clinic_month_and_sends_no_request(page):
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    page.goto("/")
    page.get_by_role("link", name="Revenue").click()
    sync_api.expect(page.locator("#screen-revenue")).to_be_visible()
    sync_api.expect(page.get_by_role("link", name="Revenue")).to_have_attribute("aria-current", "page")
    sync_api.expect(page.locator("#rev-from")).to_have_value("2026-10-01")  # clinic time, not the browser's Ho Chi Minh
    sync_api.expect(page.locator("#rev-to")).to_have_value("2026-10-13")
    page.wait_for_load_state("networkidle")
    assert not [u for u in requests if "/reports/revenue" in u]


def _run_revenue(page, frm="2026-10-12", to="2026-10-16"):
    page.goto("/#revenue")
    page.fill("#rev-from", frm)
    page.fill("#rev-to", to)
    page.get_by_role("button", name="Run report").click()
    return page.get_by_role("img", name=re.compile("Stacked bars of revenue per day"))


def test_revenue_chart_shows_a_bar_per_day_and_the_table_behind_a_toggle(client, page, snap):  # T-032 TC-1, TC-4
    for start, patient in (("2026-10-14T09:00:00-04:00", 1), ("2026-10-15T09:00:00-04:00", 2)):
        appt = book(client, start, patient_id=patient).json()["id"]
        client.post(f"/appointments/{appt}/check-in")
        client.post(f"/appointments/{appt}/complete")
    chart = _run_revenue(page)
    sync_api.expect(chart).to_be_visible()
    sync_api.expect(chart.locator(".c-cons")).to_have_count(2)
    sync_api.expect(chart).to_have_attribute("aria-label", re.compile(r"\$120\.00.*\$150\.00"))
    page.get_by_text("Show as table").click()
    sync_api.expect(page.locator("#rev-results details")).to_contain_text("Wed, 14 Oct 2026")
    snap("chart")


def test_revenue_chart_uses_the_dark_penalty_colour_in_the_dark_theme(page, snap):  # T-032 TC-6
    row = {"date": "2026-10-13", "consultation_cents": 30000, "penalty_cents": 4200, "total_cents": 34200}
    totals = {"consultation_cents": 30000, "penalty_cents": 4200, "total_cents": 34200}
    page.route("**/reports/revenue*", lambda route: route.fulfill(json={
        "from_date": "2026-10-12", "to_date": "2026-10-16", "totals": totals, "by_doctor": [], "by_day": [row]}))
    chart = _run_revenue(page)
    sync_api.expect(chart.locator(".c-pen")).to_have_css("fill", "rgb(180, 83, 9)")  # light: #b45309
    page.get_by_role("radio", name="Dark").check(force=True)  # the sidebar Theme control (its input is visually hidden)
    sync_api.expect(chart.locator(".c-pen")).to_have_css("fill", "rgb(240, 163, 94)")  # dark: #f0a35e
    snap("chart-dark")


def test_revenue_chart_on_a_long_range_scrolls_inside_its_card_not_the_page(page):  # T-032 TC-5
    days = [{"date": f"2026-09-{d:02d}", "consultation_cents": 15000, "penalty_cents": 3000 if d % 3 == 0 else 0,
             "total_cents": 18000 if d % 3 == 0 else 15000} for d in range(1, 21)]
    totals = {"consultation_cents": 300000, "penalty_cents": 18000, "total_cents": 318000}
    page.route("**/reports/revenue*", lambda route: route.fulfill(json={
        "from_date": "2026-09-01", "to_date": "2026-09-30", "totals": totals, "by_doctor": [], "by_day": days}))
    page.set_viewport_size({"width": 375, "height": 812})
    chart = _run_revenue(page, "2026-09-01", "2026-09-30")
    sync_api.expect(chart.locator(".c-cons")).to_have_count(20)
    sync_api.expect(chart.locator(".c-tot")).to_have_count(0)
    assert page.evaluate("document.documentElement.scrollWidth") <= 375


def test_revenue_without_money_shows_no_chart_only_the_empty_state(client, page):  # T-032 TC-3
    page.goto("/#revenue")
    page.get_by_role("button", name="Run report").click()
    sync_api.expect(page.locator("#rev-results")).to_contain_text("No revenue in this range")
    sync_api.expect(page.get_by_role("img", name=re.compile("Stacked bars"))).to_have_count(0)


def test_staff_opening_revenue_sees_administrators_only(page):
    page.route("**/reports/revenue*", lambda route: route.fulfill(status=403, json={"detail": "Administrator required"}))
    page.goto("/#revenue")
    page.get_by_role("button", name="Run report").click()
    sync_api.expect(page.locator("#rev-results")).to_contain_text("Administrators only")
    sync_api.expect(page.locator("#rev-from")).to_have_value("2026-10-01")
    storage = page.evaluate("[Object.keys(localStorage), Object.keys(sessionStorage)]")
    assert "clinic_session" not in str(storage)


def _signed_out(page):
    page.context.clear_cookies()
    page.goto("/")


def test_no_session_shows_only_the_login_form(page, snap):  # T-022 TC-1
    _signed_out(page)
    sync_api.expect(page.get_by_role("heading", name="Sign in")).to_be_visible()
    sync_api.expect(page.locator(".cb-sidebar")).to_be_hidden()
    snap("login")


def test_wrong_password_shows_a_generic_error_without_a_status_code(page, snap):  # TC-2
    _signed_out(page)
    page.fill("#login-user", "nobody")
    page.fill("#login-pass", "not a real password")
    page.get_by_role("button", name="Sign in").click()
    sync_api.expect(page.locator("#login-msg")).to_have_text("Wrong username or password.")
    sync_api.expect(page.locator("#login-pass")).to_have_value("")
    snap("wrong-password")


def test_staff_sees_no_admin_items(client, page, base_url, snap):  # TC-3
    from tests.helpers import make_user

    make_user(username="nurse1")
    _signed_out(page)
    page.fill("#login-user", "nurse1")
    page.fill("#login-pass", "correct horse battery")
    page.get_by_role("button", name="Sign in").click()
    sync_api.expect(page.get_by_role("link", name="Book")).to_be_visible()
    sync_api.expect(page.get_by_role("link", name="Revenue")).to_be_hidden()
    sync_api.expect(page.get_by_role("link", name="Users")).to_be_hidden()
    snap("staff-menu")


def test_a_401_returns_to_the_login_form(page, snap):  # TC-4
    page.goto("/#appointments")
    sync_api.expect(page.get_by_role("button", name="Refresh")).to_be_visible()
    page.context.clear_cookies()  # after the screen loaded, or its own load already hits the 401
    page.get_by_role("button", name="Refresh").click()
    sync_api.expect(page.get_by_role("heading", name="Sign in")).to_be_visible()
    snap("back-to-login")


def test_an_inline_script_is_reported_as_a_csp_violation(page):
    page.goto("/")
    page.evaluate("document.body.insertAdjacentHTML('beforeend', '<img src=x onerror=alert(1)>')")
    page.wait_for_timeout(200)
    assert page.csp_violations, "the CSP check did not see an inline handler"
    page.csp_violations.clear()  # expected here; the teardown check would otherwise fail this test



@pytest.mark.parametrize("role", ["staff", "admin"])
def test_each_role_signs_in_through_the_login_form(page, role, snap):  # T-027 TC-2
    from tests.helpers import make_user

    make_user(username=f"{role}-form", role=role)
    _signed_out(page)
    page.fill("#login-user", f"{role}-form")
    page.fill("#login-pass", PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    sync_api.expect(page.get_by_role("link", name="Book")).to_be_visible()
    for link in ("Revenue", "Users"):
        check = sync_api.expect(page.get_by_role("link", name=link))
        check.to_be_visible() if role == "admin" else check.to_be_hidden()
    snap(f"header-{role}")


def test_staff_page_is_signed_in_without_admin_items(staff_page):  # TC-1
    staff_page.goto("/")
    sync_api.expect(staff_page.get_by_role("link", name="Book")).to_be_visible()
    sync_api.expect(staff_page.get_by_role("link", name="Users")).to_be_hidden()


def test_admin_page_is_signed_in_with_admin_items(admin_page):  # TC-1
    admin_page.goto("/")
    sync_api.expect(admin_page.get_by_role("link", name="Users")).to_be_visible()


def test_sign_out_returns_to_the_login_form(admin_page, snap):
    from app import config

    admin_page.goto("/")
    admin_page.locator("#signout-side").click()
    sync_api.expect(admin_page.get_by_role("heading", name="Sign in")).to_be_visible()
    assert config.SESSION_COOKIE not in [c["name"] for c in admin_page.context.cookies()]
    admin_page.reload()
    sync_api.expect(admin_page.get_by_role("heading", name="Sign in")).to_be_visible()  # the server session is gone too


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_a_cross_origin_write_is_refused_for_every_unsafe_method(admin_page, base_url, method):  # TC-4
    # The app has no CSRF token: SameSite=Strict plus an Origin check (app/main.py) is the defence.
    api = admin_page.context.request
    refused = api.fetch("/appointments/999", method=method, headers={"Origin": "http://evil.example"})
    assert refused.status == 403 and "Cross-origin" in refused.json()["detail"]
    same = api.fetch("/appointments/999", method=method, headers={"Origin": base_url})
    assert same.status != 403  # a same-origin write reaches the route (404 or 405 for this id)


def test_the_session_cookie_is_locked_down_and_no_credential_is_stored(admin_page):  # TC-5
    from app import config

    admin_page.goto("/#users")
    cookie = next(c for c in admin_page.context.cookies() if c["name"] == config.SESSION_COOKIE)
    assert cookie["httpOnly"] and cookie["sameSite"] == "Strict"
    assert config.SESSION_COOKIE not in admin_page.evaluate("document.cookie")
    stored = admin_page.evaluate("[Object.entries(localStorage), Object.entries(sessionStorage)]")
    assert cookie["value"] not in str(stored) and PASSWORD not in str(stored)
    assert not re.search(r"pass|token|session|secret", str(stored), re.I)


def test_user_management_panel_screenshot_masks_the_password(admin_page, snap):  # TC-6
    admin_page.goto("/#users")
    admin_page.fill("#user-pass", PASSWORD)
    sync_api.expect(admin_page.get_by_role("heading", name="Add user")).to_be_visible()
    snap("users")


@pytest.mark.parametrize("screen,button", [("account", "Change password"), ("users", "Add user")])
def test_form_submit_buttons_keep_their_natural_width(page, screen, button):
    page.goto(f"/#{screen}")
    box = page.locator(f"#screen-{screen}").get_by_role("button", name=button).bounding_box()
    assert box["width"] < 200  # was a full grid column (~220px+) when the button sat inside .cb-fields


def test_phone_tab_bar_keeps_the_appointments_name(page):
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto("/")
    sync_api.expect(page.get_by_role("link", name="Appointments", exact=True)).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth") <= 375
