"""The PreToolUse push guard: --force-with-lease is allowed on feature branches, everything else stays blocked."""

import json
import os
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
    "pip install -r requirements.txt",
    "pip install -r requirements-dev.txt",
]

BLOCKED_ANYWHERE = [
    "git checkout -b claude/foo",
    "git switch -c claude/foo",
    "git branch claude/foo",
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
    'ksh -c "git push --force origin feat/T-015"',
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
    "git push \\\n--force origin feat/T-015",
    "git push origin \\\n+feat/T-015",
    "git add .env",
    "pip install requests",
    "python3 -m pip install requests",
    'echo "$(pip install requests)"',
    'bash -c "pip install requests"',
    "pip3 install requests",
    "git -C . add .env",
    "git -c a=b add .env",
    "echo git\ngit push --force origin feat/T-015",
    "echo `git push --force origin feat/T-015`",
    "echo git\ngit -C . add .env",
    "echo foo\\\\\ngit push --force origin feat/T-015",
    "pip --quiet install requests",
    "pip3.11 install requests",
    "python -m pip --disable-pip-version-check install requests",
    "git -c alias.p=push p --force origin develop",
    "git -c alias.p=push p origin feat/T-015",
    "git config alias.p push",
    "git push $'--force' origin feat/T-015",
    "F=--force; git push $F origin feat/T-015",
    'git push "$(echo --force)" origin feat/T-015',
    "git push origin `echo --force` feat/T-015",
    "git add $'.env'",
    "pip install -r requirements.txt evilpkg",
    "pip install -r requirements-dev.txt evilpkg",
    "pip install -r /tmp/other.txt",
    "echo a#b; git push --force origin develop",
    "git $'push' --force origin develop",
    "git `echo push` --force origin develop",
    "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=alias.p GIT_CONFIG_VALUE_0=push git p --force origin develop",
    "git --config-env=alias.p=V p --force origin develop",
    "git push origin feat/T-015 # '\ngit push --force origin develop'",
    "echo x # '\npip --quiet install requests'",
    "git -c ALIAS.p=push p --force origin develop",
    "git config Alias.p push",
    "git config include.path /tmp/evil",
    "git -c include.path=/tmp/evil p --force origin develop",
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


def _run(cmd, cwd, project=None):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project if project is not None else cwd)}
    return subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps({"tool_input": {"command": cmd}}),
        capture_output=True, text=True, cwd=cwd, env=env,
    )


@pytest.mark.parametrize("cmd", [
    "pip install -r requirements.txt",
    "pip install -r requirements-dev.txt",
    "python -m pip install -r requirements.txt",
    "python3 -m pip install -r requirements-dev.txt",
])
def test_requirements_install_is_explicitly_allowed(tmp_path, cmd):
    run = _run(cmd, tmp_path)
    decision = json.loads(run.stdout)["hookSpecificOutput"]
    assert run.returncode == 0
    assert decision["permissionDecision"] == "allow" and decision["permissionDecisionReason"]


@pytest.mark.parametrize("cmd", [
    "pip install requests",
    "pip install -r requirements.txt evilpkg",
    "pip install -r requirements.txt && echo done",
    "pip install -r requirements.txt; rm -rf x",
    "pip install -r requirements.txt | tee out",
    "pip install -r requirements.txt # note",
    "pip install -r $(echo other.txt)",
    'echo "pip install -r requirements.txt"',
    "cat <<EOF\npip install -r requirements.txt\nEOF",
    "git status",
    "/tmp/evil/pip install -r requirements.txt",
    "./pip install -r requirements.txt",
    "pip install -r ./requirements.txt",
    "pip install -r ../requirements.txt",
    "/tmp/evil/python -m pip install -r requirements.txt",
])
def test_nothing_else_gets_an_allow(tmp_path, cmd):
    assert "allow" not in _run(cmd, tmp_path).stdout


@pytest.mark.parametrize("cmd", [
    "pip install requests",
    "git add .env",
    "git checkout -b claude/foo",
    "git push --force origin feat/T-015",
])
def test_every_block_names_the_route_to_approval(tmp_path, cmd):
    run = _run(cmd, _repo(tmp_path, "feat/T-015"))
    assert run.returncode == 2
    assert "Blocked:" in run.stderr and "ask a maintainer" in run.stderr


def test_no_allow_outside_the_project_root(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    assert "allow" not in _run("pip install -r requirements.txt", sub, project=tmp_path).stdout


def test_no_allow_without_a_project_dir(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    run = subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps({"tool_input": {"command": "pip install -r requirements.txt"}}),
        capture_output=True, text=True, cwd=tmp_path, env=env,
    )
    assert "allow" not in run.stdout


@pytest.mark.parametrize("shadow", ["pip.py", "pip"])
def test_no_allow_for_python_m_when_a_local_pip_shadows_it(tmp_path, shadow):
    (tmp_path / shadow).write_text("")
    assert "allow" not in _run("python -m pip install -r requirements.txt", tmp_path).stdout
