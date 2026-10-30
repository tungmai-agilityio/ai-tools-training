"""The Rollback workflow: no-reviewer environments, develop tooling, ref checked against the target branch (T-035)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "rollback.yml"
DEPLOY = ROOT / ".github" / "workflows" / "deploy-production.yml"


def test_workflow_is_manual_only():  # AC-1
    text = WORKFLOW.read_text()

    assert re.search(r"^on:\n  workflow_dispatch:\n", text, re.MULTILINE)
    for trigger in ("pull_request:", "push:", "schedule:", "workflow_run:", "release:"):
        assert trigger not in text


def test_inputs_choose_the_environment_and_the_ref():  # AC-1, AC-2
    text = WORKFLOW.read_text()

    assert "type: choice" in text
    assert "options: [staging, production]" in text
    assert re.search(r"^\s+environment:\s*$", text, re.MULTILINE)
    assert re.search(r"^\s+ref:\s*$", text, re.MULTILINE)
    assert text.count("required: true") == 2


def test_production_rollback_uses_the_no_reviewer_environment():  # AC-1
    text = WORKFLOW.read_text()

    assert "name: ${{ inputs.environment == 'production' && 'production-rollback' || 'staging' }}" in text
    assert "url: ${{ vars.APP_URL }}" in text


def test_workflow_is_read_only():  # AC-6
    text = WORKFLOW.read_text()

    assert text.count("permissions:") == 1
    assert re.search(r"^permissions:\n  contents: read\n", text, re.MULTILINE)
    assert "write" not in text


def test_workflow_runs_the_develop_tooling():  # AC-2
    text = WORKFLOW.read_text()

    assert re.search(r"^\s+ref:\s*develop\b", text, re.MULTILINE)
    assert "fetch-depth: 0" in text
    assert "persist-credentials: false" in text
    assert re.search(r"^\s+cancel-in-progress:\s*false\s*$", text, re.MULTILINE)


def test_rollback_has_its_own_queue_and_only_restores_earlier_production_commits():
    text = WORKFLOW.read_text()

    assert "group: rollback-${{ inputs.environment }}" in text  # a later deploy dispatch cannot cancel a rollback
    assert "is not an ancestor of the live commit" in text


def test_guard_uses_the_branch_for_the_chosen_environment():  # AC-2
    text = WORKFLOW.read_text()

    assert "BRANCH: ${{ inputs.environment == 'production' && 'main' || 'develop' }}" in text
    assert 'check_release_ref.sh "$REF" "$BRANCH"' in text


def test_workflow_uses_one_secret_and_names_the_actor():  # AC-1
    text = WORKFLOW.read_text()

    assert re.findall(r"secrets\.(\w+)", text) == ["RENDER_DEPLOY_HOOK_URL"]
    assert "ACTOR: ${{ github.actor }}" in text


def test_workflow_labels_the_run_a_rollback():  # AC-3
    text = WORKFLOW.read_text()

    assert "DEPLOY_LABEL: Rollback (${{ inputs.environment }})" in text


def test_deploy_workflow_still_requires_approval():  # AC-1, AC-6
    text = DEPLOY.read_text()

    assert re.search(r"^\s+name: production\s*$", text, re.MULTILINE)
