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


@pytest.mark.parametrize("screen", ["book", "appointments", "today"])
def test_no_sideways_scroll_on_a_phone(client, page, screen):
    book(client, "2026-10-13T11:00:00-04:00")  # gives Today a timeline block
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(f"/#{screen}")
    page.wait_for_load_state("networkidle")
    if screen == "today":
        page.get_by_role("radio", name="Timeline").check()  # phones open in List; the wide timeline is the risk
    assert page.evaluate("document.documentElement.scrollWidth") <= 375
