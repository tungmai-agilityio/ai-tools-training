"""Browser smoke test for the web app (T-011). Optional: needs requirements-dev.txt and
`playwright install chromium`; skipped otherwise, so plain `pytest` stays dependency-free."""
import socket
import threading
import time

import pytest

sync_api = pytest.importorskip("playwright.sync_api")
uvicorn = pytest.importorskip("uvicorn")

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
def page(base_url):
    with sync_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:  # browser binary not installed
            pytest.skip(f"chromium not available: {e}")
        # A browser far from New York: every time on screen must still be clinic time (NFR-2).
        context = browser.new_context(timezone_id="Asia/Ho_Chi_Minh", base_url=base_url)
        pg = context.new_page()
        pg.clock.set_fixed_time(FIXED_NOW)
        yield pg
        browser.close()


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


@pytest.mark.parametrize("screen", ["book", "appointments", "today", "revenue"])
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


def test_wrong_admin_token_clears_field_and_result(client, page, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "ADMIN_TOKEN", "s3cret")
    page.goto("/#revenue")
    page.fill("#rev-token", "s3cret")
    page.get_by_role("button", name="Run report").click()
    sync_api.expect(page.locator("#rev-results")).to_contain_text("$0.00")
    page.fill("#rev-token", "wrong")
    page.press("#rev-token", "Enter")  # Enter submits the form
    sync_api.expect(page.locator("#rev-results")).to_contain_text("Admin token not accepted")
    sync_api.expect(page.locator("#rev-results")).not_to_contain_text("$0.00")
    sync_api.expect(page.locator("#rev-token")).to_have_value("")
    sync_api.expect(page.locator("#rev-token")).to_be_focused()
    sync_api.expect(page.locator("#rev-from")).to_have_value("2026-10-01")
    storage = page.evaluate("[Object.keys(localStorage), Object.keys(sessionStorage), location.href]")
    assert "wrong" not in str(storage) and "s3cret" not in str(storage)
