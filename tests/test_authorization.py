"""Every clinic route needs a session; admin routes need the admin role (T-021)."""
import pytest

from app.main import app
from tests.helpers import book

PUBLIC = {"/health", "/auth/login", "/auth/logout"}
ADMIN_ONLY = [
    ("POST", "/holidays"), ("DELETE", "/holidays/2026-10-14"), ("POST", "/doctors/1/time-off"),
    ("DELETE", "/doctors/1/time-off/1"), ("DELETE", "/appointments/1"), ("GET", "/reports/revenue"),
    ("GET", "/users"), ("POST", "/users"), ("PATCH", "/users/1"),
]


def _protected_routes():
    """Every documented route except the public ones (the OpenAPI schema lists all included routers)."""
    paths = app.openapi()["paths"]
    return sorted((m.upper(), p) for p, ops in paths.items() if p not in PUBLIC for m in ops)


@pytest.mark.parametrize("method,path", _protected_routes())
def test_every_protected_route_refuses_no_session(anon_client, method, path):  # TC-1
    url = path.replace("{appointment_id}", "1").replace("{doctor_id}", "1").replace("{day}", "2026-10-14")
    url = url.replace("{time_off_id}", "1").replace("{user_id}", "1")
    assert anon_client.request(method, url, json={}).status_code == 401


def test_public_routes_need_no_session(anon_client):  # AC-6
    assert anon_client.get("/health").status_code == 200
    assert anon_client.get("/").status_code == 200
    assert anon_client.get("/static/app.js").status_code == 200
    assert anon_client.get("/docs").status_code == 200


def test_staff_can_book_and_cancel(staff_client):  # TC-2
    r = book(staff_client, "2026-10-14T09:00:00-04:00")
    assert r.status_code == 201
    assert staff_client.post(f"/appointments/{r.json()['id']}/cancel").status_code == 200


@pytest.mark.parametrize("method,path", ADMIN_ONLY)
def test_staff_gets_403_on_admin_routes(staff_client, method, path):  # TC-3
    assert staff_client.request(method, path, json={}).status_code == 403


def test_admin_can_use_admin_routes(client):  # TC-4
    assert client.get("/reports/revenue", params={"from": "2026-10-14", "to": "2026-10-14"}).status_code == 200
    assert client.post("/holidays", json={"date": "2026-12-25", "name": "Xmas"}).status_code == 201


def test_old_admin_token_and_bearer_headers_are_ignored(anon_client, client):  # TC-5
    appt_id = book(client, "2026-10-14T09:00:00-04:00").json()["id"]
    for headers in ({"X-Admin-Token": "anything"}, {"Authorization": "Bearer anything"}):
        assert anon_client.delete(f"/appointments/{appt_id}", headers=headers).status_code == 401


def test_foreign_origin_on_unsafe_method_is_refused(staff_client):  # TC-6
    r = staff_client.post("/appointments", json={}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    assert staff_client.get("/appointments").json()["total"] == 0


def test_same_origin_or_no_origin_is_allowed(staff_client):
    assert book(staff_client, "2026-10-14T09:00:00-04:00").status_code == 201
    r = staff_client.post("/appointments/1/cancel", headers={"Origin": "https://testserver"})
    assert r.status_code == 200
    # a different port is a different origin
    assert staff_client.post("/appointments/1/cancel", headers={"Origin": "https://testserver:8443"}).status_code == 403


def test_every_response_carries_the_csp_header(anon_client):  # TC-7
    expect = "script-src 'self'; object-src 'none'; base-uri 'self'"
    assert anon_client.get("/health").headers["content-security-policy"] == expect
    assert anon_client.get("/doctors").headers["content-security-policy"] == expect  # also on a 401


def test_index_has_no_inline_script(anon_client):
    import re

    html = anon_client.get("/").text
    assert not re.search(r"<script(?![^>]*\bsrc=)", html)
    assert not re.search(r"\son[a-z]+=", html)


def test_old_admin_token_name_is_gone_from_the_source():  # TC-8
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    old = ("ADMIN" + "_TOKEN", "X-Admin" + "-Token", "x_admin" + "_token")
    files = [*(root / "app").rglob("*.py"), *(root / "app/static").glob("*.*"), *(root / "scripts").rglob("*.py"), root / ".env.example"]
    hits = [str(f) for f in files if f.is_file() and any(n.lower() in f.read_text(errors="ignore").lower() for n in old)]
    assert not hits


def test_non_ascii_session_cookie_is_401_not_500(anon_client):
    r = anon_client.get("/doctors", headers={"Cookie": "clinic_session=1.0.9.é".encode("utf-8")})
    assert r.status_code == 401


def test_validation_errors_never_echo_a_password(client):
    r = client.post("/users", json={"username": "x", "password": "short-pw-1", "role": "staff"})
    assert r.status_code == 422 and "short-pw-1" not in r.text and "input" not in r.text
    r = client.post("/auth/change-password", json={"current_password": "a", "new_password": "short-pw-2"})
    assert r.status_code == 422 and "short-pw-2" not in r.text


def test_swagger_page_is_not_blocked_by_the_script_policy(anon_client):
    assert "content-security-policy" not in anon_client.get("/docs").headers
    assert anon_client.get("/health").headers["content-security-policy"]
