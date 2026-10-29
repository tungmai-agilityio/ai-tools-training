"""Production deploys only on demand: auto-deploy off in render.yaml and a single gated workflow (T-034)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "deploy-production.yml"


def _web_services(text):
    """Split render.yaml into its web-service blocks, keyed by service name."""
    blocks = re.split(r"^\s*-\s*type:\s*web\s*$", text, flags=re.MULTILINE)[1:]
    services = {}
    for block in blocks:
        name = re.search(r"^\s*name:\s*(\S+)\s*$", block, flags=re.MULTILINE)
        services[name.group(1)] = block
    return services


def test_production_does_not_deploy_on_push():  # AC-1
    services = _web_services((ROOT / "render.yaml").read_text())

    assert re.search(r"^\s*autoDeploy:\s*false\b", services["clinic-booking"], re.MULTILINE)
    assert re.search(r"^\s*branch:\s*main\s*$", services["clinic-booking"], re.MULTILINE)


def test_staging_keeps_auto_deploy():  # AC-1
    services = _web_services((ROOT / "render.yaml").read_text())

    assert re.search(r"^\s*autoDeploy:\s*true\b", services["clinic-booking-stag"], re.MULTILINE)
    assert re.search(r"^\s*branch:\s*develop\s*$", services["clinic-booking-stag"], re.MULTILINE)


def test_workflow_has_only_the_manual_trigger():  # AC-5
    text = WORKFLOW.read_text()

    assert re.search(r"^on:\n  workflow_dispatch:\n", text, re.MULTILINE)
    for trigger in ("pull_request:", "push:", "schedule:", "workflow_run:", "release:"):
        assert trigger not in text
    assert "required: true" in text


def test_workflow_is_read_only():  # AC-5
    text = WORKFLOW.read_text()

    assert text.count("permissions:") == 1
    assert re.search(r"^permissions:\n  contents: read\n", text, re.MULTILINE)
    assert "write" not in text


def test_workflow_gates_on_the_production_environment():  # AC-2
    text = WORKFLOW.read_text()

    assert re.search(r"^\s*environment:\n\s*name: production\s*$", text, re.MULTILINE)


def test_workflow_uses_one_production_secret():  # AC-5, TC-7
    text = WORKFLOW.read_text()

    assert re.findall(r"secrets\.(\w+)", text) == ["RENDER_DEPLOY_HOOK_URL"]


def test_workflow_runs_from_main_not_the_deployed_ref():
    text = WORKFLOW.read_text()

    assert "ref: ${{ inputs.ref }}" not in text  # an older tag would have no deploy script
    assert re.search(r"^\s*ref:\s*main\b", text, re.MULTILINE)  # the production environment allows only main
    assert "fetch-depth: 0" in text
    assert "persist-credentials: false" in text
    assert re.search(r"^\s*cancel-in-progress:\s*false\s*$", text, re.MULTILINE)
