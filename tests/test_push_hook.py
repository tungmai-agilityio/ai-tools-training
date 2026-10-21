"""The PreToolUse push guard: --force-with-lease is allowed on feature branches, everything else stays blocked."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "block-forbidden-command.py"


def _repo(tmp_path, branch):
    subprocess.run(["git", "init", "-q", "-b", branch], cwd=tmp_path, check=True)
    return tmp_path


def _blocked(cmd, cwd):
    run = subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps({"tool_input": {"command": cmd}}),
        capture_output=True, text=True, cwd=cwd,
    )
    assert run.returncode in (0, 2), run.stderr
    return run.returncode == 2


ALLOWED_ON_FEATURE = [
    "git push -u origin feat/T-015",
    "git push --force-with-lease origin feat/T-015",
    "git push --force-with-lease",
    "git push --force-with-lease origin HEAD",
    "git push --force-with-lease origin feat/develop-docs",
    "git push origin develop",
    "git status && git push -u origin feat/T-015",
    'gh pr create --body "never git push --force or git push -f"',
]

BLOCKED_ANYWHERE = [
    "git push --force origin feat/T-015",
    "git push -f origin feat/T-015",
    "git push -uf origin feat/T-015",
    "git push -fu origin feat/T-015",
    "git push origin +feat/T-015",
    "git push --force-with-lease origin develop",
    "git push origin develop --force-with-lease",
    "git push origin +develop",
    "git push origin +HEAD:develop",
    "git push --force-with-lease origin HEAD:develop",
    "git push --force-with-lease origin HEAD:refs/heads/develop",
    "git push --force-with-lease origin main",
    "git -C . push --force-with-lease origin develop",
    "git status && git push --force-with-lease origin develop",
    "git push --mirror origin",
    'eval "git push --force origin feat/T-015"',
    'bash -e -c "git push --force origin feat/T-015"',
    "bash -c -- 'git push --force origin feat/T-015'",
    "echo hi\ngit push --force origin 'feat/T-015\nmore",
    "git -c core.editor=true push --force origin feat/T-015",
    "git push --force-with-lease origin HEAD:heads/develop",
    "git push --force-with-lease origin HEAD:refs/develop",
    '/usr/bin/git push --force origin feat/T-015',
    'bash -c "git push --force origin feat/T-015"',
    "sh -c 'git push --force-with-lease origin develop'",
    "git push --force origin 'feat/T-015",
    "git push origin feat/T-015 gitlab",
    "git add .env",
    "pip install requests",
]


@pytest.mark.parametrize("cmd", ALLOWED_ON_FEATURE)
def test_allowed_on_a_feature_branch(tmp_path, cmd):
    assert not _blocked(cmd, _repo(tmp_path, "feat/T-015"))


@pytest.mark.parametrize("cmd", BLOCKED_ANYWHERE)
def test_blocked_on_a_feature_branch(tmp_path, cmd):
    assert _blocked(cmd, _repo(tmp_path, "feat/T-015"))


@pytest.mark.parametrize("cmd", [
    "git push --force-with-lease",
    "git push --force-with-lease origin HEAD",
    "git push --force-with-lease origin",
])
def test_lease_with_implicit_target_is_blocked_on_develop(tmp_path, cmd):
    assert _blocked(cmd, _repo(tmp_path, "develop"))


def test_lease_with_implicit_target_is_blocked_outside_a_repo(tmp_path):
    assert _blocked("git push --force-with-lease", tmp_path)
