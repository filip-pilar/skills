import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_NAMES = ("sidekick", "reply", "supervise")
MANUAL_SKILLS = ("devils-advocate", "gitprep", *SKILL_NAMES)


class SideOrchestrationMigrationTests(unittest.TestCase):
    def metadata(self, name: str) -> dict:
        path = REPO_ROOT / "skills" / name / "agents" / "openai.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_reviewed_skills_preserve_manual_invocation(self):
        for name in MANUAL_SKILLS:
            metadata = self.metadata(name)
            self.assertIs(metadata["policy"]["allow_implicit_invocation"], False)
            self.assertIn(f"${name}", metadata["interface"]["default_prompt"])

    def test_retired_packages_remain_archived_without_public_shims(self):
        for name in ("co-prompt", "side-mode", "side-draft", "side-run"):
            self.assertFalse((REPO_ROOT / "skills" / name).exists())

        for name in ("co-prompt", "reply", "sidekick"):
            self.assertTrue(
                (REPO_ROOT / "legacy" / "skills" / name / "SKILL.md").is_file()
            )


if __name__ == "__main__":
    unittest.main()
