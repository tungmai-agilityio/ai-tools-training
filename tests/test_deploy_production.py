"""scripts/deploy_production.py triggers the Render hook and verifies /health reports the commit (T-034)."""

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from scripts import deploy_production as deploy

SECRET = "SECRETVALUE"
COMMIT = "a" * 40
OLD = "b" * 40
ENV_KEYS = ("RENDER_DEPLOY_HOOK_URL", "APP_URL", "COMMIT_SHA", "TIMEOUT_SECONDS",
            "MAIN_SHA", "MAIN_AHEAD", "GITHUB_STEP_SUMMARY", "DEPLOY_LABEL", "ACTOR", "SUMMARY_HINT")


class _State:
    def __init__(self):
        self.hook_status = 200
        self.hook_body = {"deploy": {"id": "dep-1"}}
        self.health_status = 200
        self.health_queue = []
        self.index_status = 200
        self.calls = []
        self.url = ""


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        self.server.state.calls.append(("POST", self.path))
        body = json.dumps(self.server.state.hook_body).encode()
        code = self.server.state.hook_status
        self.send_response(code)
        if 300 <= code < 400:
            self.send_header("Location", "/collect")  # following this would resend the key
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        state = self.server.state
        state.calls.append(("GET", self.path))
        if self.path == "/health":
            if state.health_status != 200:
                self.send_response(state.health_status)
                self.end_headers()
                return
            body = state.health_queue.pop(0) if state.health_queue else {"status": "ok", "commit": None}
            self._send(200, body if isinstance(body, bytes) else json.dumps(body).encode())
        elif self.path == "/":
            self._send(state.index_status, b"")
        else:
            self._send(404, b"")

    def _send(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def render(monkeypatch):
    state = _State()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    server.daemon_threads = True
    server.state = state
    state.url = f"http://127.0.0.1:{server.server_address[1]}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(deploy, "VERIFY_DELAY", 0)
    yield state
    server.shutdown()
    thread.join()


def _env(monkeypatch, **values):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def _run(main, monkeypatch, render, summary, commit=COMMIT, env=None):
    monkeypatch.setattr(deploy, "_config",
                        lambda: (f"{render.url}/deploy/srv-test123?key={SECRET}", render.url, commit, 5))
    _env(monkeypatch, **(env or {}))
    return deploy.main(["--summary-file", str(summary)])


def test_hook_200_returns_the_deploy_id(render):
    status, deploy_id = deploy.trigger(f"{render.url}/deploy?key={SECRET}", COMMIT)

    assert (status, deploy_id) == (200, "dep-1")
    method, path = render.calls[-1]
    assert method == "POST"
    assert f"ref={COMMIT}" in path


def test_hook_202_is_accepted_without_a_deploy_id(render):
    render.hook_status = 202
    render.hook_body = {}

    assert deploy.trigger(f"{render.url}/deploy?key={SECRET}", COMMIT) == (202, "")


@pytest.mark.parametrize("code", [201, 302, 401, 500])
def test_hook_failure_fails_without_revealing_the_url(render, code, capsys):
    render.hook_status = code

    with pytest.raises(deploy.DeployError) as excinfo:
        deploy.trigger(f"{render.url}/deploy?key={SECRET}", COMMIT)

    printed = capsys.readouterr()
    text = f"{excinfo.value}{excinfo.value!r}{printed.out}{printed.err}"
    assert f"HTTP {code}" in str(excinfo.value)
    assert SECRET not in text
    assert ("GET", "/collect") not in render.calls  # a redirect is never followed


def test_a_control_character_in_the_hook_never_leaks(capsys):
    hook = f"https://hook.example/deploy?key={SECRET} bad"

    with pytest.raises(deploy.DeployError) as excinfo:
        deploy.trigger(hook, COMMIT)

    printed = capsys.readouterr()
    text = f"{excinfo.value}{excinfo.value!r}{printed.out}{printed.err}"
    assert "could not use the deploy hook URL" in str(excinfo.value)
    assert SECRET not in text


def test_trailing_slash_still_reaches_health(render):
    render.health_queue = [{"status": "ok", "commit": COMMIT}]

    assert deploy._probe(render.url + "/") == COMMIT
    assert ("GET", "/health") in render.calls


@pytest.mark.parametrize("body", [{"status": "ok"}, {"status": "ok", "commit": None}, b"not json"])
def test_probe_returns_none_when_the_commit_is_unreadable(render, body):
    render.health_queue = [body]

    assert deploy._probe(render.url) is None


def test_probe_returns_none_when_health_is_down(render):
    render.health_status = 503

    assert deploy._probe(render.url) is None


def test_probe_returns_none_when_nothing_listens():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    assert deploy._probe(f"http://127.0.0.1:{port}") is None


def test_poll_waits_until_the_new_commit_is_reported(render):
    render.health_queue = [{"commit": OLD}, {"commit": COMMIT}]

    assert deploy.wait_for_commit(render.url, COMMIT, timeout=2, interval=0.01) == COMMIT


def test_poll_times_out_naming_the_last_commit(render):
    render.health_queue = [{"commit": OLD}]

    with pytest.raises(deploy.DeployError) as excinfo:
        deploy.wait_for_commit(render.url, COMMIT, timeout=0.2, interval=0.02)

    assert "last seen: " + OLD in str(excinfo.value)


def test_verify_requires_200_from_both_paths(render):
    assert deploy.verify(render.url) == {"/": 200, "/health": 200}

    render.index_status = 500
    assert deploy.verify(render.url)["/"] == 500


def test_main_deploys_polls_and_verifies(render, monkeypatch, tmp_path, capsys):
    render.health_queue = [{"commit": OLD}, {"commit": COMMIT}, {"commit": COMMIT}]
    summary = tmp_path / "summary.md"

    assert _run(deploy.main, monkeypatch, render, summary,
                env={"MAIN_SHA": "c" * 40, "MAIN_AHEAD": "2"}) == 0

    text = summary.read_text()
    assert text.startswith("## Production deploy")  # the deploy default, unchanged by T-035
    assert "verified" in text
    assert COMMIT in text and "dep-1" in text and "2 commits ahead" in text
    assert render.url in text  # AC-4: the summary names the deployed URL
    assert "https://dashboard.render.com/web/srv-test123/deploys/dep-1" in text
    assert any(method == "POST" for method, _ in render.calls)
    assert SECRET not in text + capsys.readouterr().out


ROLLBACK_ENV = {
    "DEPLOY_LABEL": "Rollback (production)",
    "ACTOR": "maintainer",
    "SUMMARY_HINT": "Redeploy manually in Render, then revert the bad commit in a PR.",
}


def test_main_writes_a_rollback_summary(render, monkeypatch, tmp_path):
    render.health_queue = [{"commit": OLD}, {"commit": COMMIT}, {"commit": COMMIT}]
    summary = tmp_path / "summary.md"

    assert _run(deploy.main, monkeypatch, render, summary, env=ROLLBACK_ENV) == 0

    text = summary.read_text()
    assert text.startswith("## Rollback (production)")
    assert "| Started by | maintainer |" in text
    assert "dep-1" in text  # AC-3: the summary names the restored deploy id
    assert "https://dashboard.render.com/web/srv-test123/deploys/dep-1" in text
    assert ROLLBACK_ENV["SUMMARY_HINT"] in text
    assert SECRET not in text


def test_a_failed_rollback_summary_keeps_the_hint(render, monkeypatch, tmp_path):
    render.health_queue = [{"commit": COMMIT}]
    render.index_status = 500
    summary = tmp_path / "summary.md"

    assert _run(deploy.main, monkeypatch, render, summary, env=ROLLBACK_ENV) == 1

    text = summary.read_text()
    assert text.startswith("## Rollback (production)")
    assert "**Result:** failed" in text
    assert "/ 500" in text
    assert ROLLBACK_ENV["SUMMARY_HINT"] in text


def test_main_reports_a_commit_that_is_already_live(render, monkeypatch, tmp_path):
    render.health_queue = [{"commit": COMMIT}]
    summary = tmp_path / "summary.md"

    assert _run(deploy.main, monkeypatch, render, summary) == 0

    assert "already live" in summary.read_text()
    assert not any(method == "POST" for method, _ in render.calls)


def test_main_fails_when_the_site_is_unhealthy(render, monkeypatch, tmp_path):
    render.health_queue = [{"commit": COMMIT}]
    render.index_status = 500
    summary = tmp_path / "summary.md"

    assert _run(deploy.main, monkeypatch, render, summary) == 1

    text = summary.read_text()
    assert "**Result:** failed" in text
    assert "/ 500" in text
    assert render.url in text  # AC-4, TC-5: a red run names the URL it checked


@pytest.mark.parametrize("env,mention", [
    ({"RENDER_DEPLOY_HOOK_URL": f"http://hook.example/{SECRET}", "APP_URL": "https://app.example", "COMMIT_SHA": COMMIT},
     "RENDER_DEPLOY_HOOK_URL"),
    ({"RENDER_DEPLOY_HOOK_URL": "https://hook.example/x", "APP_URL": "", "COMMIT_SHA": COMMIT}, "APP_URL"),
    ({"RENDER_DEPLOY_HOOK_URL": "https://hook.example/x", "APP_URL": "https://app.example", "COMMIT_SHA": "abc"},
     "COMMIT_SHA"),
    ({"RENDER_DEPLOY_HOOK_URL": "https://hook.example/x", "APP_URL": "https://app.example", "COMMIT_SHA": COMMIT,
      "TIMEOUT_SECONDS": "10"}, "TIMEOUT_SECONDS"),
])
def test_main_rejects_bad_input_without_leaking_the_secret(monkeypatch, tmp_path, env, mention, capsys):
    _env(monkeypatch, **env)
    summary = tmp_path / "summary.md"

    assert deploy.main(["--summary-file", str(summary)]) == 1

    printed = capsys.readouterr()
    assert mention in summary.read_text()
    assert SECRET not in summary.read_text() + printed.out + printed.err
