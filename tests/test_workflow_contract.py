from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def _read(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def test_workflows_expose_stable_check_names() -> None:
    expected = {
        "component-boundary.yml": "name: component-boundary",
        "contracts.yml": "name: contracts",
        "wrist-host.yml": "name: wrist-host",
        "ring-ci.yml": "name: ring-ci",
    }
    for filename, marker in expected.items():
        assert marker in _read(filename)


def test_component_boundary_runs_the_shared_policy() -> None:
    workflow = _read("component-boundary.yml")
    assert "git diff --name-only" in workflow
    assert "tools/wear_repo_policy.py validate" in workflow
    assert '"$GITHUB_HEAD_REF"' in workflow


def test_ring_ci_requires_tests_once_firmware_exists() -> None:
    workflow = _read("ring-ci.yml")
    assert "ring/flow-ring/CMakeLists.txt" in workflow
    assert "ring/flow-ring/tests/host/run.sh" in workflow
    assert "test -x" in workflow


def test_auto_merge_uses_trusted_workflow_run_code() -> None:
    workflow = _read("component-auto-merge.yml")
    assert "workflow_run:" in workflow
    assert "pull_request_target" not in workflow
    assert "contents: write" in workflow
    assert "pull-requests: write" in workflow
    assert "tools/auto_merge_component_pr.py" in workflow
    assert "github.event.repository.default_branch" in workflow
    assert "github.event.workflow_run.head_sha" not in workflow


def test_auto_merge_listens_to_every_required_workflow() -> None:
    workflow = _read("component-auto-merge.yml")
    for name in ("component-boundary", "contracts", "wrist-host", "ring-ci"):
        assert f'"{name}"' in workflow
