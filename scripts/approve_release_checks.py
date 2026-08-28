import argparse
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable, Sequence


REQUIRED_WORKFLOWS = ("Validation",)
DEFAULT_DELAYS = (2, 4, 8, 15, 30, 30, 30, 30, 30, 30)


class GitHubAPIError(RuntimeError):
    pass


def github_api(endpoint: str, method: str = "GET") -> object:
    command = ["gh", "api"]
    if method != "GET":
        command.extend(["--method", method])
    command.append(endpoint)
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "gh api failed"
        raise GitHubAPIError(message)
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


def _retry(
    operation: Callable[[], object],
    *,
    sleep: Callable[[float], None],
    delays: Sequence[float],
) -> object:
    for attempt in range(len(delays) + 1):
        try:
            return operation()
        except GitHubAPIError:
            if attempt == len(delays):
                raise
            sleep(delays[attempt])
    raise AssertionError("retry loop exited unexpectedly")


def _release_number_from_output(release_prs: str) -> int | None:
    if not release_prs.strip():
        return None
    try:
        pull_requests = json.loads(release_prs)
    except json.JSONDecodeError as error:
        raise RuntimeError("Release Please returned invalid pull request data") from error
    if not pull_requests:
        return None
    if len(pull_requests) != 1 or not isinstance(pull_requests[0].get("number"), int):
        raise RuntimeError("Expected one grouped Release Please pull request")
    return pull_requests[0]["number"]


def _find_open_release_number(repository: str, api: Callable[..., object]) -> int | None:
    pulls = api(f"repos/{repository}/pulls?state=open&base=main&per_page=100")
    candidates = [
        pull
        for pull in pulls
        if pull.get("user", {}).get("login") == "github-actions[bot]"
        and pull.get("base", {}).get("ref") == "main"
        and pull.get("head", {}).get("ref") == "release-please--branches--main"
    ]
    if len(candidates) > 1:
        raise RuntimeError("Found more than one open Release Please pull request")
    return candidates[0]["number"] if candidates else None


def _needs_approval(run: dict) -> bool:
    return run.get("conclusion") == "action_required"


def _approve_run(
    *,
    repository: str,
    run_id: int,
    api: Callable[..., object],
    sleep: Callable[[float], None],
    delays: Sequence[float],
) -> None:
    run_endpoint = f"repos/{repository}/actions/runs/{run_id}"
    for attempt in range(len(delays) + 1):
        try:
            run = api(run_endpoint)
            if not _needs_approval(run):
                return
            api(f"{run_endpoint}/approve", method="POST")
            return
        except GitHubAPIError:
            if attempt == len(delays):
                raise
            sleep(delays[attempt])
    raise AssertionError("approval loop exited unexpectedly")


def reconcile(
    *,
    repository: str,
    release_prs: str,
    api: Callable[..., object] = github_api,
    sleep: Callable[[float], None] = time.sleep,
    delays: Sequence[float] = DEFAULT_DELAYS,
) -> list[int]:
    def retry(operation: Callable[[], object]) -> object:
        return _retry(operation, sleep=sleep, delays=delays)

    release_number = _release_number_from_output(release_prs)
    if release_number is None:
        release_number = retry(lambda: _find_open_release_number(repository, api))
    if release_number is None:
        print("No open Release Please pull request needs reconciliation.")
        return []

    pull_request = retry(lambda: api(f"repos/{repository}/pulls/{release_number}"))
    release_branch = pull_request["head"]["ref"]
    release_head = pull_request["head"]["sha"]
    runs_endpoint = (
        f"repos/{repository}/actions/runs?event=pull_request"
        f"&branch={release_branch}&per_page=100"
    )
    expected_names = set(REQUIRED_WORKFLOWS)

    for attempt in range(len(delays) + 1):
        try:
            response = api(runs_endpoint)
            matching_runs = [
                run
                for run in response["workflow_runs"]
                if run.get("head_sha") == release_head
                and run.get("name") in expected_names
            ]
            if {run["name"] for run in matching_runs} == expected_names:
                approval_ids = sorted(
                    {run["id"] for run in matching_runs if _needs_approval(run)}
                )
                for run_id in approval_ids:
                    _approve_run(
                        repository=repository,
                        run_id=run_id,
                        api=api,
                        sleep=sleep,
                        delays=delays,
                    )
                print(
                    f"Reconciled native checks for release pull request #{release_number} "
                    f"at {release_head}."
                )
                return approval_ids
        except GitHubAPIError:
            if attempt == len(delays):
                raise

        if attempt < len(delays):
            sleep(delays[attempt])

    raise RuntimeError(
        f"Native pull request checks did not appear for release head {release_head}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Approve native checks on the open Release Please pull request."
    )
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY"),
        required="GITHUB_REPOSITORY" not in os.environ,
    )
    parser.add_argument(
        "--release-prs",
        default=os.environ.get("RELEASE_PRS", ""),
    )
    arguments = parser.parse_args(argv)

    try:
        reconcile(
            repository=arguments.repository,
            release_prs=arguments.release_prs,
        )
    except (GitHubAPIError, KeyError, RuntimeError, TypeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
