from __future__ import annotations

import pytest

from tools.wear_repo_policy import (
    PolicyError,
    classify_branch,
    validate_paths,
)


@pytest.mark.parametrize(
    ("branch", "component"),
    [
        ("codex/wrist-power-fix", "wrist"),
        ("wrist/power-fix", "wrist"),
        ("codex/ring-gesture-v1", "ring"),
        ("ring/gesture-v1", "ring"),
        ("codex/shared-contract-v2", "shared"),
        ("shared/contract-v2", "shared"),
        ("codex/gateway-bluez-reconnect", "gateway"),
        ("gateway/bluez-reconnect", "gateway"),
        ("codex/bootstrap-wear-layout", "bootstrap"),
    ],
)
def test_classify_branch(branch: str, component: str) -> None:
    assert classify_branch(branch) == component


def test_unknown_branch_is_rejected() -> None:
    with pytest.raises(PolicyError, match="无法识别组件"):
        classify_branch("feature/mixed-firmware")


def test_wrist_branch_accepts_only_wrist_tree() -> None:
    assert validate_paths(
        "wrist",
        ["wrist/flow-wrist/main/app_main.c", "wrist/flow-wrist/README.md"],
    ) == []
    assert validate_paths("wrist", ["ring/flow-ring/src/main.c"]) == [
        "ring/flow-ring/src/main.c"
    ]


def test_ring_branch_accepts_only_ring_tree() -> None:
    assert validate_paths(
        "ring",
        ["ring/README.md", "ring/flow-ring/docs/design.md"],
    ) == []
    assert validate_paths("ring", ["wrist/flow-wrist/main/app_main.c"]) == [
        "wrist/flow-wrist/main/app_main.c"
    ]


def test_shared_branch_accepts_only_repository_shared_paths() -> None:
    allowed = [
        ".github/workflows/component-boundary.yml",
        ".gitignore",
        "AGENTS.md",
        "README.md",
        "requirements-dev.txt",
        "contracts/ble-v1.md",
        "docs/REPOSITORY-WORKFLOW.md",
        "tests/test_wear_repo_policy.py",
        "tools/wear_repo_policy.py",
    ]
    assert validate_paths("shared", allowed) == []
    assert validate_paths("shared", ["wrist/flow-wrist/main/app_main.c"]) == [
        "wrist/flow-wrist/main/app_main.c"
    ]


def test_gateway_branch_accepts_only_gateway_tree() -> None:
    assert validate_paths(
        "gateway",
        ["hub-gateway/src/flow_wear_gateway/service.py"],
    ) == []
    assert validate_paths("gateway", ["ring/flow-ring/src/main.c"]) == [
        "ring/flow-ring/src/main.c"
    ]


def test_bootstrap_branch_allows_one_time_repository_reorganization() -> None:
    assert validate_paths(
        "bootstrap",
        [
            "README.md",
            "wrist/flow-wrist/main/app_main.c",
            "ring/README.md",
            ".github/workflows/component-boundary.yml",
        ],
    ) == []


def test_empty_and_absolute_paths_are_rejected() -> None:
    assert validate_paths("ring", ["", "/ring/flow-ring/main.c"]) == [
        "<empty>",
        "/ring/flow-ring/main.c",
    ]
