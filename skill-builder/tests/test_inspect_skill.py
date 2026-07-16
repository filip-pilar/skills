from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INSPECTOR = REPO_ROOT / "skill-builder" / "scripts" / "inspect_skill.py"


class InspectorTests(unittest.TestCase):
    def run_inspector(self, skill_dir: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INSPECTOR), str(skill_dir), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )

    def make_skill(self, root: Path) -> Path:
        skill_dir = root / "sample"
        references = skill_dir / "references"
        references.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("alpha beta\n", encoding="utf-8")
        (references / "guide.md").write_text("gamma delta epsilon\n", encoding="utf-8")
        return skill_dir

    def test_selected_reference_is_counted_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = self.make_skill(Path(temp_dir))
            result = self.run_inspector(
                skill_dir,
                "--load",
                "references/guide.md",
                "--load",
                "references/guide.md",
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("- words: 5", result.stdout)
        self.assertIn("- files: SKILL.md, references/guide.md", result.stdout)

    def test_loading_root_does_not_double_count_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = self.make_skill(Path(temp_dir))
            result = self.run_inspector(skill_dir, "--load", "SKILL.md")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("- words: 2", result.stdout)
        self.assertIn("- files: SKILL.md", result.stdout)

    def test_missing_loaded_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = self.make_skill(Path(temp_dir))
            result = self.run_inspector(skill_dir, "--load", "references/missing.md")

        self.assertEqual(result.returncode, 2)
        self.assertIn("loaded path is not a file", result.stderr)

    def test_loaded_path_cannot_escape_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = self.make_skill(root)
            (root / "outside.md").write_text("outside\n", encoding="utf-8")
            result = self.run_inspector(skill_dir, "--load", "../outside.md")

        self.assertEqual(result.returncode, 2)
        self.assertIn("loaded path escapes the skill directory", result.stderr)

    def test_uncountable_loaded_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = self.make_skill(Path(temp_dir))
            binary = skill_dir / "assets" / "sample.bin"
            binary.parent.mkdir()
            binary.write_bytes(b"\x00\x01")
            result = self.run_inspector(skill_dir, "--load", "assets/sample.bin")

        self.assertEqual(result.returncode, 2)
        self.assertIn("loaded path is not countable text", result.stderr)


if __name__ == "__main__":
    unittest.main()
