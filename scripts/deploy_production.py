"""Trigger the Render deploy hook for one commit and verify it is live (T-034, T-035).

Inputs come from the environment so the hook URL stays a secret: RENDER_DEPLOY_HOOK_URL, APP_URL,
COMMIT_SHA, TIMEOUT_SECONDS, and optionally MAIN_SHA/MAIN_AHEAD for the summary. A rollback run also sets
DEPLOY_LABEL, ACTOR and SUMMARY_HINT. Nothing printed or raised here contains the hook URL.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from http import client as http_client
from urllib import error, parse, request

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
HOOK_TIMEOUT = 30
PROBE_TIMEOUT = 10
PROBE_INTERVAL = 20
VERIFY_RETRIES = 2
VERIFY_DELAY = 2
MIN_TIMEOUT = 60
MAX_TIMEOUT = 1800
USER_AGENT = "clinic-booking-deploy/1"
DEFAULT_LABEL = "Production deploy"
DEFAULT_HINT = ("Rollback: dispatch `Deploy Production` with an earlier tag or commit, or follow the rollback "
                "steps in `docs/deploy-render.md`.")


class DeployError(RuntimeError):
    """A deploy step failed. Messages never contain the hook URL."""


class _NoRedirect(request.HTTPRedirectHandler):
    """A deploy hook never redirects; following one would resend the secret key to another host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # the default error handler turns the 3xx into an HTTPError


_OPENER = request.build_opener(_NoRedirect())


def _is_https(url: str) -> bool:
    parts = parse.urlsplit(url)
    return parts.scheme == "https" and bool(parts.netloc)


def _join(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + path


def _service_id(hook_url: str) -> str | None:
    """The Render service id in the hook URL (srv-...), used only to link the deploy in the summary."""
    try:
        path = parse.urlsplit(hook_url).path
    except ValueError:
        return None
    match = re.search(r"/deploy/(srv-[A-Za-z0-9]+)", path)
    return match.group(1) if match else None


def trigger(hook_url: str, commit: str) -> tuple[int, str]:
    """POST the deploy hook with `ref=<commit>`; return the HTTP status and the deploy id ("" when unknown)."""
    url = f"{hook_url}{'&' if '?' in hook_url else '?'}ref={parse.quote(commit, safe='')}"
    try:
        req = request.Request(url, data=b"", method="POST", headers={"User-Agent": USER_AGENT})
        with _OPENER.open(req, timeout=HOOK_TIMEOUT) as resp:
            status, body = resp.status, resp.read()
    except error.HTTPError as exc:
        raise DeployError(f"deploy hook returned HTTP {exc.code}") from None
    except (error.URLError, OSError, ValueError, http_client.InvalidURL):
        raise DeployError("could not use the deploy hook URL") from None
    if status not in (200, 202):
        raise DeployError(f"deploy hook returned HTTP {status}")
    deploy_id = ""
    try:
        deploy_id = str((json.loads(body).get("deploy") or {}).get("id") or "")
    except (ValueError, AttributeError):
        pass
    return status, deploy_id


def _probe(app_url: str) -> str | None:
    """The commit /health reports, or None when it cannot be read (still starting, old code, error)."""
    try:
        req = request.Request(_join(app_url, "/health"), headers={"User-Agent": USER_AGENT})
        with _OPENER.open(req, timeout=PROBE_TIMEOUT) as resp:
            if resp.status != 200:
                return None
            body = resp.read()
    except (error.HTTPError, error.URLError, OSError, ValueError, http_client.InvalidURL):
        return None
    try:
        payload = json.loads(body)
    except ValueError:
        return None
    commit = payload.get("commit") if isinstance(payload, dict) else None
    return commit if isinstance(commit, str) and commit else None


def wait_for_commit(app_url: str, commit: str, timeout: int, interval: int = PROBE_INTERVAL) -> str:
    """Poll /health until it reports `commit`. Free-plan cutover refuses connections and 502s, so every miss is retried."""
    deadline = time.monotonic() + timeout
    started = time.monotonic()
    last = None
    while True:
        seen = _probe(app_url)
        if seen:
            last = seen
        print(f"[{time.monotonic() - started:.0f}s] /health -> {seen or 'unavailable'}")
        if seen == commit:
            return seen
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise DeployError(
                f"/health did not report {commit} within {timeout}s (last seen: {last or 'no commit reported'})")
        time.sleep(min(interval, remaining))


def _status(url: str) -> int:
    try:
        req = request.Request(url, headers={"User-Agent": USER_AGENT})
        with _OPENER.open(req, timeout=PROBE_TIMEOUT) as resp:
            return resp.status
    except error.HTTPError as exc:
        return exc.code
    except (error.URLError, OSError, ValueError, http_client.InvalidURL):
        return 0


def verify(app_url: str, retries: int | None = None, delay: float | None = None) -> dict[str, int]:
    """GET / and /health; both must be exactly 200. Retries cover a 502 right after cutover."""
    retries = VERIFY_RETRIES if retries is None else retries
    delay = VERIFY_DELAY if delay is None else delay
    paths = ("/", "/health")
    for attempt in range(retries + 1):
        codes = {path: _status(_join(app_url, path)) for path in paths}
        if all(code == 200 for code in codes.values()) or attempt == retries:
            return codes
        time.sleep(delay)
    return codes  # unreachable; keeps type checkers happy


def _config() -> tuple[str, str, str, int]:
    hook = os.environ.get("RENDER_DEPLOY_HOOK_URL", "").strip()
    app_url = os.environ.get("APP_URL", "").strip()
    commit = os.environ.get("COMMIT_SHA", "").strip().lower()
    if not _is_https(hook):
        raise DeployError("RENDER_DEPLOY_HOOK_URL must be the production environment's https deploy hook URL")
    if not _is_https(app_url):
        raise DeployError("APP_URL must be an https URL in the production environment")
    if not COMMIT_RE.match(commit):
        raise DeployError("COMMIT_SHA must be a 40-character commit SHA")
    try:
        timeout = int(os.environ.get("TIMEOUT_SECONDS", str(MAX_TIMEOUT)))
    except ValueError:
        raise DeployError("TIMEOUT_SECONDS must be a whole number of seconds") from None
    if not MIN_TIMEOUT <= timeout <= MAX_TIMEOUT:
        raise DeployError(f"TIMEOUT_SECONDS must be between {MIN_TIMEOUT} and {MAX_TIMEOUT}")
    return hook, app_url.rstrip("/"), commit, timeout


def _summary(state: dict) -> str:
    rows = [("Target commit", f"`{state['target']}`" if state.get("target") else "unknown")]
    if state.get("app_url"):
        rows.append(("Service", state["app_url"]))
    if state.get("actor"):
        rows.append(("Started by", state["actor"]))
    if state.get("main_sha"):
        ahead = state.get("main_ahead")
        suffix = "" if ahead in (None, "", "0") else f" ({ahead} commits ahead)"
        rows.append(("main tip", f"`{state['main_sha']}`{suffix}"))
    if state.get("hook_status"):
        if state["deploy_id"]:
            rows.append(("Deploy hook", f"HTTP {state['hook_status']}, deploy `{state['deploy_id']}`"))
        elif state["hook_status"] == 202:
            rows.append(("Deploy hook", "HTTP 202 - another deploy was in progress; the hook may have been queued"))
        else:
            rows.append(("Deploy hook", f"HTTP {state['hook_status']}, deploy id unknown - see the Render Events tab"))
    if state.get("service_id"):
        service = f"https://dashboard.render.com/web/{state['service_id']}"
        if state.get("deploy_id"):
            rows.append(("Render deploy", f"{service}/deploys/{state['deploy_id']}"))
        else:
            rows.append(("Render events", f"{service}/events"))
    if state.get("before"):
        note = " - already live (no-op)" if state.get("already_live") else ""
        rows.append(("Before this run", f"`{state['before']}`{note}"))
    if state.get("codes"):
        rows.append(("`/` and `/health`", ", ".join(f"{path} {code}" for path, code in state["codes"].items())))
    if state.get("elapsed") is not None:
        rows.append(("Duration", f"{state['elapsed']:.0f}s"))
    lines = [f"## {state.get('label', DEFAULT_LABEL)}", "", f"**Result:** {state.get('result', 'failed')}", "",
             "| Item | Value |", "|---|---|"]
    lines += [f"| {key} | {value} |" for key, value in rows]
    if state.get("error"):
        lines += ["", f"**Failure:** {state['error']}"]
    lines += ["", state.get("hint", DEFAULT_HINT)]
    return "\n".join(lines) + "\n"


def _write_summary(path: str | None, text: str) -> None:
    target = path or os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        try:
            with open(target, "a", encoding="utf-8") as fh:
                fh.write(text)
            return
        except OSError:
            pass
    print(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-file", help="write the Markdown summary here instead of $GITHUB_STEP_SUMMARY")
    args = parser.parse_args(argv)

    state: dict = {}
    started = time.monotonic()
    result = 0
    state["label"] = os.environ.get("DEPLOY_LABEL", "").strip() or DEFAULT_LABEL
    state["actor"] = os.environ.get("ACTOR", "").strip() or None
    state["hint"] = os.environ.get("SUMMARY_HINT", "").strip() or DEFAULT_HINT
    try:
        hook, app_url, commit, timeout = _config()
        state["target"] = commit
        state["app_url"] = app_url
        state["service_id"] = _service_id(hook)
        state["main_sha"] = os.environ.get("MAIN_SHA", "").strip() or None
        state["main_ahead"] = os.environ.get("MAIN_AHEAD", "").strip() or None
        before = _probe(app_url)
        state["before"] = before
        if before == commit:
            state["already_live"] = True
            state["result"] = "already live - nothing deployed (no-op)"
            print(f"commit {commit} is already live; skipping the deploy hook")
        else:
            print(f"triggering the deploy hook for {commit}")
            state["hook_status"], state["deploy_id"] = trigger(hook, commit)
            print(f"deploy hook returned HTTP {state['hook_status']}")
            print(f"waiting up to {timeout}s for /health to report {commit}")
            wait_for_commit(app_url, commit, timeout)
            state["result"] = "verified"
        state["codes"] = verify(app_url)
        unhealthy = {path: code for path, code in state["codes"].items() if code != 200}
        if unhealthy:
            raise DeployError("unhealthy after deploy: " + ", ".join(f"{path} {code}" for path, code in unhealthy.items()))
        print(f"deploy verified: {commit} is live")
    except DeployError as exc:
        result = 1
        state["error"] = str(exc)
        state["result"] = "failed"
        print(f"deploy failed: {exc}", file=sys.stderr)
    finally:
        state["elapsed"] = time.monotonic() - started
        _write_summary(args.summary_file, _summary(state))
    return result


if __name__ == "__main__":
    sys.exit(main())
