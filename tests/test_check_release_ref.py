"""scripts/check_release_ref.sh resolves a ref and refuses anything that is not on main (T-034)."""

import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_release_ref.sh"


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def _repos(tmp_path):
    """A bare origin, a work clone that pushes to it, and a full clone acting as the runner checkout."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    work = tmp_path / "work"
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True)
    _git(work, "config", "user.email", "ci@example.com")
    _git(work, "config", "user.name", "CI")
    (work / "a.txt").write_text("x\n")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "base")
    _git(work, "tag", "v0.1.0")
    _git(work, "tag", "-a", "v0.2.0", "-m", "annotated")
    _git(work, "push", "-q", "origin", "main", "--tags")
    runner = tmp_path / "runner"
    subprocess.run(["git", "clone", "-q", str(origin), str(runner)], check=True)
    return work, runner


def _run(runner, ref):
    return subprocess.run(["bash", str(SCRIPT), ref], cwd=runner, capture_output=True, text=True)


def test_lightweight_tag_on_main_resolves_to_its_commit(tmp_path):
    work, runner = _repos(tmp_path)
    expected = _git(work, "rev-parse", "v0.1.0^{commit}")

    run = _run(runner, "v0.1.0")

    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == expected


def test_annotated_tag_is_peeled_to_its_commit(tmp_path):
    work, runner = _repos(tmp_path)
    expected = _git(work, "rev-parse", "v0.2.0^{commit}")
    tag_object = _git(work, "rev-parse", "v0.2.0")
    assert tag_object != expected

    run = _run(runner, "v0.2.0")

    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == expected


def test_commit_sha_on_main_is_accepted(tmp_path):
    work, runner = _repos(tmp_path)
    expected = _git(work, "rev-parse", "main")

    run = _run(runner, expected)

    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == expected


def test_commit_off_main_is_refused(tmp_path):
    work, runner = _repos(tmp_path)
    _git(work, "checkout", "-q", "-b", "feature")
    (work / "b.txt").write_text("y\n")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "off main")
    _git(work, "push", "-q", "origin", "feature")

    run = _run(runner, "feature")

    assert run.returncode == 1
    assert "not on main" in run.stderr


def test_unknown_ref_is_refused(tmp_path):
    _, runner = _repos(tmp_path)

    run = _run(runner, "does-not-exist")

    assert run.returncode == 1
    assert "unknown ref" in run.stderr


def test_option_like_ref_is_refused_without_running_anything(tmp_path):
    _, runner = _repos(tmp_path)
    marker = tmp_path / "MARK"

    run = _run(runner, f"--upload-pack=touch {marker}")

    assert run.returncode == 1
    assert "invalid ref" in run.stderr
    assert not marker.exists()


def test_padded_ref_is_trimmed(tmp_path):
    work, runner = _repos(tmp_path)
    expected = _git(work, "rev-parse", "v0.1.0^{commit}")

    run = _run(runner, " v0.1.0 ")

    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == expected
