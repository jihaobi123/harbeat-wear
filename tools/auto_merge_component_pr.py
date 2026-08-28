"""Safely squash-merge internal Wrist and Ring pull requests after CI."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

from tools.wear_repo_policy import PolicyError, classify_branch


@dataclass(frozen=True)
class MergeDecision:
    merge: bool
    reason: str


_REQUIRED_CHECKS = {
    "wrist": ("component-boundary", "contracts", "wrist-host"),
    "ring": ("component-boundary", "contracts", "ring-ci"),
}


def evaluate_merge(
    branch: str,
    base: str,
    draft: bool,
    internal: bool,
    mergeable: bool,
    checks: Mapping[str, str],
) -> MergeDecision:
    """Decide whether one pull request is eligible for automatic merge."""

    try:
        component = classify_branch(branch)
    except PolicyError:
        return MergeDecision(False, "branch is not a recognized component branch")

    if component not in _REQUIRED_CHECKS:
        return MergeDecision(False, f"{component} pull requests require manual merge")
    if base != "main":
        return MergeDecision(False, "base branch is not main")
    if draft:
        return MergeDecision(False, "draft pull request")
    if not internal:
        return MergeDecision(False, "external pull request")
    if not mergeable:
        return MergeDecision(False, "pull request is not mergeable")

    for name in _REQUIRED_CHECKS[component]:
        if checks.get(name) != "success":
            return MergeDecision(
                False,
                f"required check {name} is missing or not successful",
            )
    return MergeDecision(True, "all required checks passed")


def latest_check_conclusions(check_runs: Iterable[Mapping[str, Any]]) -> dict[str, str]:
    """Collapse GitHub check runs to the newest state for each stable job name."""

    newest: dict[str, tuple[str, str]] = {}
    for run in check_runs:
        name = str(run.get("name", ""))
        if not name:
            continue
        status = str(run.get("status", ""))
        conclusion = run.get("conclusion")
        value = str(conclusion) if status == "completed" and conclusion else "pending"
        timestamp = str(
            run.get("completed_at")
            or run.get("started_at")
            or run.get("created_at")
            or "9999"
        )
        previous = newest.get(name)
        if previous is None or timestamp >= previous[0]:
            newest[name] = (timestamp, value)
    return {name: value for name, (_, value) in newest.items()}


class GitHubApi:
    def __init__(self, repository: str, token: str) -> None:
        self.repository = repository
        self.token = token
        self.base_url = f"https://api.github.com/repos/{repository}"

    def request(
        self,
        method: str,
        path: str,
        payload: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "harbeat-wear-component-auto-merge",
            },
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, dict):
            raise RuntimeError("GitHub API returned a non-object response")
        return data

    def get_pull_request(self, number: int) -> Mapping[str, Any]:
        return self.request("GET", f"/pulls/{number}")

    def get_check_runs(self, sha: str) -> list[Mapping[str, Any]]:
        encoded_sha = urllib.parse.quote(sha, safe="")
        data = self.request("GET", f"/commits/{encoded_sha}/check-runs?per_page=100")
        check_runs = data.get("check_runs", [])
        if not isinstance(check_runs, list):
            raise RuntimeError("GitHub API check_runs is not a list")
        return [run for run in check_runs if isinstance(run, dict)]

    def squash_merge(self, number: int, sha: str, title: str) -> Mapping[str, Any]:
        return self.request(
            "PUT",
            f"/pulls/{number}/merge",
            {
                "sha": sha,
                "merge_method": "squash",
                "commit_title": title,
            },
        )


def _load_event(path: str) -> Mapping[str, Any]:
    with open(path, encoding="utf-8") as handle:
        event = json.load(handle)
    if not isinstance(event, dict):
        raise RuntimeError("workflow event is not a JSON object")
    return event


def _first_pr_number(event: Mapping[str, Any]) -> Optional[int]:
    workflow_run = event.get("workflow_run", {})
    if not isinstance(workflow_run, dict):
        return None
    if workflow_run.get("conclusion") != "success":
        return None
    pull_requests = workflow_run.get("pull_requests", [])
    if not isinstance(pull_requests, list) or not pull_requests:
        return None
    first = pull_requests[0]
    if not isinstance(first, dict) or not isinstance(first.get("number"), int):
        return None
    return int(first["number"])


def main() -> int:
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not event_path or not token or not repository:
        print("auto-merge configuration missing", file=sys.stderr)
        return 2

    try:
        event = _load_event(event_path)
        number = _first_pr_number(event)
        if number is None:
            print("auto-merge skipped: workflow did not yield a successful pull request")
            return 0

        api = GitHubApi(repository, token)
        pull = api.get_pull_request(number)
        head = pull.get("head", {})
        base = pull.get("base", {})
        if not isinstance(head, dict) or not isinstance(base, dict):
            raise RuntimeError("pull request head/base payload is invalid")

        head_repo = head.get("repo", {})
        internal = isinstance(head_repo, dict) and head_repo.get("full_name") == repository
        sha = str(head.get("sha", ""))
        checks = latest_check_conclusions(api.get_check_runs(sha)) if sha else {}
        decision = evaluate_merge(
            branch=str(head.get("ref", "")),
            base=str(base.get("ref", "")),
            draft=bool(pull.get("draft", False)),
            internal=internal,
            mergeable=pull.get("mergeable") is True,
            checks=checks,
        )
        if not decision.merge:
            print(f"auto-merge skipped: {decision.reason}")
            return 0

        title = f"{pull.get('title', 'component update')} (#{number})"
        result = api.squash_merge(number, sha, title)
        if result.get("merged") is not True:
            print(f"auto-merge failed: {result.get('message', 'unknown response')}")
            return 1
        print(f"auto-merge completed: pull request #{number}")
        return 0
    except (OSError, RuntimeError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        print(f"auto-merge error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
