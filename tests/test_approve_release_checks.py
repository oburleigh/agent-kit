import unittest

from scripts import approve_release_checks


class FakeAPI:
    def __init__(self, responses):
        self.responses = {
            (method, endpoint): list(values)
            for (method, endpoint), values in responses.items()
        }
        self.calls = []

    def __call__(self, endpoint, method="GET"):
        self.calls.append((method, endpoint))
        values = self.responses[(method, endpoint)]
        value = values.pop(0) if len(values) > 1 else values[0]
        if isinstance(value, Exception):
            raise value
        return value


class ReleaseCheckApprovalTest(unittest.TestCase):
    def test_reconciles_only_action_required_runs_on_the_exact_head(self) -> None:
        runs_endpoint = (
            "repos/oburleigh/agent-kit/actions/runs?"
            "event=pull_request&branch=release-please--branches--main&per_page=100"
        )
        api = FakeAPI(
            {
                ("GET", "repos/oburleigh/agent-kit/pulls/6"): [
                    {
                        "head": {
                            "ref": "release-please--branches--main",
                            "sha": "release-head",
                        }
                    }
                ],
                ("GET", runs_endpoint): [
                    {"workflow_runs": []},
                    {
                        "workflow_runs": [
                            {
                                "id": 10,
                                "name": "Validation",
                                "head_sha": "release-head",
                                "status": "completed",
                                "conclusion": "action_required",
                            },
                            {
                                "id": 13,
                                "name": "Validation",
                                "head_sha": "other-head",
                                "status": "completed",
                                "conclusion": "action_required",
                            },
                            {
                                "id": 14,
                                "name": "Unrelated workflow",
                                "head_sha": "release-head",
                                "status": "completed",
                                "conclusion": "action_required",
                            },
                        ]
                    },
                ],
                ("GET", "repos/oburleigh/agent-kit/actions/runs/10"): [
                    {
                        "id": 10,
                        "status": "completed",
                        "conclusion": "action_required",
                    }
                ],
                ("POST", "repos/oburleigh/agent-kit/actions/runs/10/approve"): [{}],
            }
        )
        sleeps = []

        approved = approve_release_checks.reconcile(
            repository="oburleigh/agent-kit",
            release_prs='[{"number": 6}]',
            api=api,
            sleep=sleeps.append,
            delays=(2, 4),
        )

        self.assertEqual(approved, [10])
        self.assertEqual(sleeps, [2])
        self.assertNotIn(
            ("POST", "repos/oburleigh/agent-kit/actions/runs/13/approve"),
            api.calls,
        )

    def test_lost_approval_response_is_success_after_state_recheck(self) -> None:
        runs_endpoint = (
            "repos/oburleigh/agent-kit/actions/runs?"
            "event=pull_request&branch=release-please--branches--main&per_page=100"
        )
        approval_run = {
            "id": 10,
            "name": "Validation",
            "head_sha": "release-head",
            "status": "completed",
            "conclusion": "action_required",
        }
        api = FakeAPI(
            {
                ("GET", "repos/oburleigh/agent-kit/pulls/6"): [
                    {
                        "head": {
                            "ref": "release-please--branches--main",
                            "sha": "release-head",
                        }
                    }
                ],
                ("GET", runs_endpoint): [
                    {
                        "workflow_runs": [
                            approval_run,
                            {
                                "id": 11,
                                "name": "Python scaffold",
                                "head_sha": "release-head",
                                "status": "queued",
                                "conclusion": None,
                            },
                            {
                                "id": 12,
                                "name": "TypeScript scaffold",
                                "head_sha": "release-head",
                                "status": "queued",
                                "conclusion": None,
                            },
                        ]
                    }
                ],
                ("GET", "repos/oburleigh/agent-kit/actions/runs/10"): [
                    approval_run,
                    {
                        "id": 10,
                        "status": "queued",
                        "conclusion": None,
                    },
                ],
                ("POST", "repos/oburleigh/agent-kit/actions/runs/10/approve"): [
                    approve_release_checks.GitHubAPIError("response lost")
                ],
            }
        )
        sleeps = []

        approved = approve_release_checks.reconcile(
            repository="oburleigh/agent-kit",
            release_prs='[{"number": 6}]',
            api=api,
            sleep=sleeps.append,
            delays=(2, 4),
        )

        self.assertEqual(approved, [10])
        self.assertEqual(
            api.calls.count(
                ("POST", "repos/oburleigh/agent-kit/actions/runs/10/approve")
            ),
            1,
        )

    def test_recovers_the_existing_open_release_pull_request(self) -> None:
        pulls_endpoint = (
            "repos/oburleigh/agent-kit/pulls?state=open&base=main&per_page=100"
        )
        api = FakeAPI(
            {
                ("GET", pulls_endpoint): [
                    [
                        {
                            "number": 7,
                            "user": {"login": "someone"},
                            "base": {"ref": "main"},
                            "head": {"ref": "feature"},
                        },
                        {
                            "number": 6,
                            "user": {"login": "github-actions[bot]"},
                            "base": {"ref": "main"},
                            "head": {"ref": "release-please--branches--main"},
                        },
                    ]
                ],
                ("GET", "repos/oburleigh/agent-kit/pulls/6"): [
                    {
                        "head": {
                            "ref": "release-please--branches--main",
                            "sha": "release-head",
                        }
                    }
                ],
                (
                    "GET",
                    "repos/oburleigh/agent-kit/actions/runs?"
                    "event=pull_request&branch=release-please--branches--main&per_page=100",
                ): [
                    {
                        "workflow_runs": [
                            {
                                "id": index,
                                "name": name,
                                "head_sha": "release-head",
                                "status": "queued",
                                "conclusion": None,
                            }
                            for index, name in enumerate(
                                approve_release_checks.REQUIRED_WORKFLOWS,
                                start=1,
                            )
                        ]
                    }
                ],
            }
        )

        approved = approve_release_checks.reconcile(
            repository="oburleigh/agent-kit",
            release_prs="",
            api=api,
            sleep=lambda _: None,
            delays=(0,),
        )

        self.assertEqual(approved, [])

    def test_retries_transient_api_failures(self) -> None:
        runs_endpoint = (
            "repos/oburleigh/agent-kit/actions/runs?"
            "event=pull_request&branch=release-please--branches--main&per_page=100"
        )
        complete_runs = {
            "workflow_runs": [
                {
                    "id": index,
                    "name": name,
                    "head_sha": "release-head",
                    "status": "queued",
                    "conclusion": None,
                }
                for index, name in enumerate(
                    approve_release_checks.REQUIRED_WORKFLOWS,
                    start=1,
                )
            ]
        }
        api = FakeAPI(
            {
                ("GET", "repos/oburleigh/agent-kit/pulls/6"): [
                    approve_release_checks.GitHubAPIError("temporary"),
                    {
                        "head": {
                            "ref": "release-please--branches--main",
                            "sha": "release-head",
                        }
                    },
                ],
                ("GET", runs_endpoint): [
                    approve_release_checks.GitHubAPIError("temporary"),
                    complete_runs,
                ],
            }
        )
        sleeps = []

        approved = approve_release_checks.reconcile(
            repository="oburleigh/agent-kit",
            release_prs='[{"number": 6}]',
            api=api,
            sleep=sleeps.append,
            delays=(2, 4, 8),
        )

        self.assertEqual(approved, [])
        self.assertEqual(sleeps, [2, 2])

    def test_no_open_release_pull_request_is_a_noop(self) -> None:
        api = FakeAPI(
            {
                (
                    "GET",
                    "repos/oburleigh/agent-kit/pulls?state=open&base=main&per_page=100",
                ): [[]]
            }
        )

        approved = approve_release_checks.reconcile(
            repository="oburleigh/agent-kit",
            release_prs="",
            api=api,
            sleep=lambda _: None,
            delays=(0,),
        )

        self.assertEqual(approved, [])

    def test_fails_if_all_required_workflows_never_appear(self) -> None:
        runs_endpoint = (
            "repos/oburleigh/agent-kit/actions/runs?"
            "event=pull_request&branch=release-please--branches--main&per_page=100"
        )
        api = FakeAPI(
            {
                ("GET", "repos/oburleigh/agent-kit/pulls/6"): [
                    {
                        "head": {
                            "ref": "release-please--branches--main",
                            "sha": "release-head",
                        }
                    }
                ],
                ("GET", runs_endpoint): [{"workflow_runs": []}],
            }
        )

        with self.assertRaisesRegex(RuntimeError, "did not appear"):
            approve_release_checks.reconcile(
                repository="oburleigh/agent-kit",
                release_prs='[{"number": 6}]',
                api=api,
                sleep=lambda _: None,
                delays=(0, 0),
            )


if __name__ == "__main__":
    unittest.main()
