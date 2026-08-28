import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CodeOwnersTest(unittest.TestCase):
    def test_oburleigh_owns_the_repository(self) -> None:
        codeowners = (ROOT / ".github/CODEOWNERS").read_text(encoding="utf-8")

        self.assertEqual(codeowners, "* @oburleigh\n")


if __name__ == "__main__":
    unittest.main()
