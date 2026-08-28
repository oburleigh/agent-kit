import subprocess
import sys
import unittest
from pathlib import Path

from scripts.ci_gate import passes_gate

ROOT = Path(__file__).resolve().parents[1]


class CiGateTest(unittest.TestCase):
    def test_irrelevant_validation_passes_when_heavy_jobs_are_skipped(self) -> None:
        self.assertTrue(passes_gate("success", "false", ("skipped",)))

    def test_relevant_validation_requires_every_heavy_job_to_succeed(self) -> None:
        self.assertTrue(passes_gate("success", "true", ("success", "success")))
        self.assertFalse(passes_gate("success", "true", ("success", "failure")))
        self.assertFalse(passes_gate("success", "true", ("success", "skipped")))

    def test_gate_fails_closed_for_scope_or_relevance_errors(self) -> None:
        self.assertFalse(passes_gate("failure", "false", ("skipped",)))
        self.assertFalse(passes_gate("success", "", ("skipped",)))
        self.assertFalse(passes_gate("success", "true", ()))

    def test_cli_returns_nonzero_when_a_required_job_fails(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/ci_gate.py",
                "success",
                "true",
                "success",
                "failure",
            ],
            cwd=ROOT,
            check=False,
        )

        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
