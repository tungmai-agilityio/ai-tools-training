"""scripts/ci_needs_tests.sh decides whether CI must run the full suite: docs-only changes skip it, any doubt runs it."""

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "ci_needs_tests.sh"
ZERO_SHA = "0" * 40


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _scope(tmp_path, files, base_arg=None):
    """Commit a base, then a change to `files` ({path: content}); return the script's output."""
    _git(tmp_path, "init", "-q", "-b", "develop")
    _git(tmp_path, "config", "user.email", "ci@example.com")
    _git(tmp_path, "config", "user.name", "CI")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "old.py").write_text("x = 1\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "change")
    base = "HEAD^1" if base_arg is None else base_arg
    run = subprocess.run(["bash", str(SCRIPT), base, "HEAD"], cwd=tmp_path, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    return run.stdout.strip()


@pytest.mark.parametrize("path", [
    "docs/a.md", "plans/tickets/T-1.md", "README.md", ".github/ISSUE_TEMPLATE/bug.md",
    ".claude/skills/pr/SKILL.md", "docs/references/api.md",
])
def test_docs_only_change_skips_the_full_run(tmp_path, path):
    assert _scope(tmp_path, {path: "text\n"}) == "full=false"


@pytest.mark.parametrize("path", [
    "app/x.py", ".claude/hooks/x.py", "scripts/x.py", "requirements-dev.txt", "render.yaml",
    ".github/workflows/tests.yml", "tests/test_x.py",
])
def test_code_or_config_change_runs_the_full_suite(tmp_path, path):
    assert _scope(tmp_path, {path: "x\n"}) == "full=true"


def test_workflow_change_mixed_with_docs_runs_the_full_suite(tmp_path):
    files = {".github/workflows/tests.yml": "x\n", "docs/a.md": "text\n"}
    assert _scope(tmp_path, files) == "full=true"


def test_rename_from_code_to_docs_runs_the_full_suite(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "develop")
    _git(tmp_path, "config", "user.email", "ci@example.com")
    _git(tmp_path, "config", "user.name", "CI")
    (tmp_path / "app").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "app" / "a.py").write_text("x = 1\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    _git(tmp_path, "mv", "app/a.py", "docs/a.md")
    _git(tmp_path, "commit", "-q", "-m", "rename")
    run = subprocess.run(["bash", str(SCRIPT), "HEAD^1", "HEAD"], cwd=tmp_path, capture_output=True, text=True)
    assert run.stdout.strip() == "full=true"


@pytest.mark.parametrize("base", ["", ZERO_SHA, "deadbeef" * 5])
def test_missing_or_unknown_base_runs_the_full_suite(tmp_path, base):
    assert _scope(tmp_path, {"docs/a.md": "text\n"}, base_arg=base) == "full=true"


def test_empty_diff_runs_the_full_suite(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "develop")
    _git(tmp_path, "config", "user.email", "ci@example.com")
    _git(tmp_path, "config", "user.name", "CI")
    (tmp_path / "a.txt").write_text("x\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    run = subprocess.run(["bash", str(SCRIPT), "HEAD", "HEAD"], cwd=tmp_path, capture_output=True, text=True)
    assert run.stdout.strip() == "full=true"
