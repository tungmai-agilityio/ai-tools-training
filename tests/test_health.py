"""`/health` reports the commit Render is running, so a deploy can be verified (T-034)."""

import importlib

import pytest

from app import config


def test_health_reports_the_running_commit(anon_client, monkeypatch):  # AC-3a
    monkeypatch.setattr(config, "RENDER_GIT_COMMIT", "a" * 40)

    body = anon_client.get("/health").json()

    assert body["commit"] == "a" * 40


def test_health_commit_is_null_when_unset(anon_client, monkeypatch):  # AC-3a
    monkeypatch.setattr(config, "RENDER_GIT_COMMIT", None)

    body = anon_client.get("/health").json()

    assert body["commit"] is None
    assert body["status"] == "ok"
    assert body["timezone"] == "America/New_York"


def test_health_exposes_only_status_timezone_and_commit(anon_client, monkeypatch):  # AC-3a
    monkeypatch.setattr(config, "RENDER_GIT_COMMIT", "a" * 40)

    assert set(anon_client.get("/health").json()) == {"status", "timezone", "commit"}


def test_settings_read_the_render_commit(monkeypatch):
    try:
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("RENDER_GIT_COMMIT", "b" * 40)
            importlib.reload(config)
            assert config.RENDER_GIT_COMMIT == "b" * 40
    finally:
        importlib.reload(config)  # env is restored by now; reload so other tests see it


def test_settings_treat_an_empty_commit_as_unset(monkeypatch):
    try:
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("RENDER_GIT_COMMIT", "")
            importlib.reload(config)
            assert config.RENDER_GIT_COMMIT is None
    finally:
        importlib.reload(config)
