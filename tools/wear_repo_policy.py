"""Branch naming and path boundaries for the HarBeat Wear monorepo."""

from __future__ import annotations

import argparse
from pathlib import PurePosixPath
from typing import Iterable, Sequence


class PolicyError(ValueError):
    """Raised when a branch cannot be routed to one repository component."""


_BRANCH_PREFIXES: tuple[tuple[str, str], ...] = (
    ("codex/bootstrap-", "bootstrap"),
    ("codex/wrist-", "wrist"),
    ("wrist/", "wrist"),
    ("codex/ring-", "ring"),
    ("ring/", "ring"),
    ("codex/shared-", "shared"),
    ("shared/", "shared"),
    ("codex/gateway-", "gateway"),
    ("gateway/", "gateway"),
)

_SHARED_PREFIXES = (".github/", "contracts/", "docs/", "tests/", "tools/")
_SHARED_ROOT_FILES = {
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "requirements-dev.txt",
}


def classify_branch(branch: str) -> str:
    """Return the component selected by a repository branch name."""

    for prefix, component in _BRANCH_PREFIXES:
        if branch.startswith(prefix) and len(branch) > len(prefix):
            return component
    raise PolicyError(
        "无法识别组件分支。使用 codex/wrist-*、codex/ring-*、"
        "codex/shared-*、codex/gateway-* 或 codex/bootstrap-*。"
    )


def _valid_relative_path(path: str) -> bool:
    if not path or path.startswith("/"):
        return False
    parts = PurePosixPath(path).parts
    return bool(parts) and ".." not in parts and "." not in parts


def _path_allowed(component: str, path: str) -> bool:
    if component == "bootstrap":
        return True
    if component == "wrist":
        return path.startswith("wrist/")
    if component == "ring":
        return path.startswith("ring/")
    if component == "gateway":
        return path.startswith("hub-gateway/")
    if component == "shared":
        return path in _SHARED_ROOT_FILES or path.startswith(_SHARED_PREFIXES)
    raise PolicyError(f"未知组件：{component}")


def validate_paths(component: str, paths: Iterable[str]) -> list[str]:
    """Return changed paths that fall outside a component boundary."""

    violations: list[str] = []
    for raw_path in paths:
        path = raw_path.strip()
        if not _valid_relative_path(path):
            violations.append(path or "<empty>")
            continue
        if not _path_allowed(component, path):
            violations.append(path)
    return violations


def _read_paths(path: str) -> list[str]:
    with open(path, encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate changed paths")
    validate.add_argument("--branch", required=True)
    validate.add_argument("--files-from", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        component = classify_branch(args.branch)
        violations = validate_paths(component, _read_paths(args.files_from))
    except (OSError, PolicyError) as exc:
        print(f"component policy error: {exc}")
        return 2

    print(f"component={component}")
    if not violations:
        print("component paths: OK")
        return 0

    print("component path violations:")
    for path in violations:
        print(f"- {path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
