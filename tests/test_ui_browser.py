"""Browser smoke test for the web app (T-011). Optional: needs requirements-dev.txt and
`playwright install chromium`; skipped otherwise, so plain `pytest` stays dependency-free."""
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


@pytest.fixture
def page(base_url, client):  # `client` is signed in as an admin; hand its session cookie to the browser
    with sync_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:  # browser binary not installed
            if REQUIRE_BROWSER:
                pytest.fail(f"chromium not available: {e}")
            pytest.skip(f"chromium not available: {e}")
        # A browser far from New York: every time on screen must still be clinic time (NFR-2).
        context = browser.new_context(timezone_id="Asia/Ho_Chi_Minh", base_url=base_url)
        from app import config

        context.add_cookies([{"name": config.SESSION_COOKIE, "value": client.cookies.get(config.SESSION_COOKIE), "url": base_url}])
        pg = context.new_page()
        pg.clock.set_fixed_time(FIXED_NOW)
        pg.csp_violations = []
        pg.on("console", lambda m: pg.csp_violations.append(m.text) if CSP_MARK in m.text else None)
        yield pg
        browser.close()
        assert not pg.csp_violations, f"CSP violation: {pg.csp_violations}"


@pytest.fixture
def snap(page, request):
    """snap(name): save <test>-<name>-desktop.png and -phone.png, masking password and token inputs."""
    SHOTS.mkdir(parents=True, exist_ok=True)

    def take(name):
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
