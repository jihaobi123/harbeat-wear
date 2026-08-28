from __future__ import annotations

import pytest

from tools.auto_merge_component_pr import evaluate_merge, latest_check_conclusions


@pytest.mark.parametrize(
    ("branch", "component_check"),
    [
        ("codex/wrist-power-fix", "wrist-host"),
        ("codex/ring-gesture-v1", "ring-ci"),
    ],
)
def test_component_pr_merges_only_with_all_required_checks(
    branch: str,
    component_check: str,
) -> None:
    decision = evaluate_merge(
        branch=branch,
        base="main",
        draft=False,
        internal=True,
        mergeable=True,
        checks={
            "component-boundary": "success",
            "contracts": "success",
            component_check: "success",
        },
    )
    assert decision.merge is True
    assert decision.reason == "all required checks passed"


@pytest.mark.parametrize("conclusion", ["failure", "cancelled", "timed_out", "pending"])
def test_non_successful_check_blocks_merge(conclusion: str) -> None:
    decision = evaluate_merge(
        branch="codex/wrist-power-fix",
        base="main",
        draft=False,
        internal=True,
        mergeable=True,
        checks={
            "component-boundary": "success",
            "contracts": "success",
            "wrist-host": conclusion,
        },
    )
    assert decision.merge is False
    assert "wrist-host" in decision.reason


def test_missing_check_blocks_merge() -> None:
    decision = evaluate_merge(
        branch="codex/ring-gesture-v1",
        base="main",
        draft=False,
        internal=True,
        mergeable=True,
        checks={"component-boundary": "success", "contracts": "success"},
    )
    assert decision.merge is False
    assert decision.reason == "required check ring-ci is missing or not successful"


@pytest.mark.parametrize(
    "branch",
    [
        "codex/shared-contract-v2",
        "codex/gateway-bluez-reconnect",
        "codex/bootstrap-wear-layout",
        "feature/mixed-firmware",
    ],
)
def test_non_component_branches_never_auto_merge(branch: str) -> None:
    decision = evaluate_merge(
        branch=branch,
        base="main",
        draft=False,
        internal=True,
        mergeable=True,
        checks={},
    )
    assert decision.merge is False


@pytest.mark.parametrize(
    ("base", "draft", "internal", "mergeable", "reason"),
    [
        ("release", False, True, True, "base branch is not main"),
        ("main", True, True, True, "draft pull request"),
        ("main", False, False, True, "external pull request"),
        ("main", False, True, False, "pull request is not mergeable"),
    ],
)
def test_pr_state_can_block_auto_merge(
    base: str,
    draft: bool,
    internal: bool,
    mergeable: bool,
    reason: str,
) -> None:
    decision = evaluate_merge(
        branch="codex/ring-gesture-v1",
        base=base,
        draft=draft,
        internal=internal,
        mergeable=mergeable,
        checks={
            "component-boundary": "success",
            "contracts": "success",
            "ring-ci": "success",
        },
    )
    assert decision.merge is False
    assert decision.reason == reason


def test_latest_completed_check_wins() -> None:
    checks = latest_check_conclusions(
        [
            {
                "name": "ring-ci",
                "status": "completed",
                "conclusion": "failure",
                "completed_at": "2026-08-28T01:00:00Z",
            },
            {
                "name": "ring-ci",
                "status": "completed",
                "conclusion": "success",
                "completed_at": "2026-08-28T01:02:00Z",
            },
            {
                "name": "contracts",
                "status": "in_progress",
                "conclusion": None,
                "completed_at": None,
            },
        ]
    )
    assert checks == {"ring-ci": "success", "contracts": "pending"}
