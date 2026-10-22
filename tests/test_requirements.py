"""Offline policy checks for the two narrow requirements maintenance changes."""
import ast
import os
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(os.environ.get("RAP_SOURCE_ROOT", str(Path(__file__).resolve().parents[1])))


def requirement_lines():
    return [line.split("#", 1)[0].strip() for line in
            (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line.split("#", 1)[0].strip()]


class RequirementsPolicyTests(unittest.TestCase):
    def test_future_has_patched_minimum(self):
        lines = [line for line in requirement_lines() if re.match(r"^future(?:[<>=!~ ]|$)", line)]
        self.assertEqual(len(lines), 1)
        minimum = re.fullmatch(r"future\s*>=\s*(\d+)\.(\d+)\.(\d+)", lines[0])
        self.assertIsNotNone(minimum, "future must declare a minimum patched release")
        version = tuple(int(part) for part in minimum.groups())
        self.assertGreaterEqual(version, (0, 18, 3))
        self.assertLessEqual(version, (0, 18, 3), "do not force a larger migration in this patch")

    def test_uses_canonical_scikit_learn_distribution(self):
        lines = requirement_lines()
        self.assertIn("scikit-learn", lines)
        self.assertNotIn("sklearn", lines)

    def test_legacy_transformers_api_pin_is_unchanged(self):
        self.assertIn("transformers==2.1.1", requirement_lines())

    def test_other_requirements_are_unchanged(self):
        other = [line for line in requirement_lines()
                 if not re.match(r"^future(?:[<>=!~ ]|$)", line)
                 and line not in ("sklearn", "scikit-learn")]
        self.assertEqual(other, ["transformers==2.1.1", "torch", "numpy", "tqdm", "keras", "pypinyin", "thulac"])

    def test_no_duplicate_distributions(self):
        names = [re.split(r"[<>=!~ ]", line, maxsplit=1)[0].lower().replace("_", "-")
                 for line in requirement_lines()]
        self.assertEqual(len(names), len(set(names)))

    def test_test_file_supports_python36_grammar(self):
        kwargs = {"feature_version": (3, 6)} if sys.version_info >= (3, 8) else {}
        source = Path(__file__)
        ast.parse(source.read_text(encoding="utf-8"), filename=str(source), **kwargs)


if __name__ == "__main__":
    unittest.main()
