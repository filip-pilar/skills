import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_NAMES = ("sidekick", "reply", "supervise")


class SideOrchestrationMigrationTests(unittest.TestCase):
    def skill_text(self, name: str) -> str:
        return (REPO_ROOT / "skills" / name / "SKILL.md").read_text(
            encoding="utf-8"
        )

    def metadata(self, name: str) -> dict:
        path = REPO_ROOT / "skills" / name / "agents" / "openai.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def workflow_text(self) -> str:
        path = REPO_ROOT / "docs" / "side-orchestration-workflow.md"
        return path.read_text(encoding="utf-8")

    def test_all_three_public_skills_are_manual_only(self):
        for name in SKILL_NAMES:
            metadata = self.metadata(name)
            self.assertIs(metadata["policy"]["allow_implicit_invocation"], False)
            self.assertIn(f"${name}", metadata["interface"]["default_prompt"])

    def test_reply_keeps_one_clean_fenced_text_presentation(self):
        reply = " ".join(self.skill_text("reply").split())

        self.assertRegex(reply, r"exactly one fenced `text` block")
        self.assertRegex(reply, r"containing only the proposed parent prompt")
        self.assertNotIn("Current reply", reply)

    def test_workflow_has_no_retired_format_authorization_parser(self):
        supervise = self.skill_text("supervise")
        metadata = yaml.safe_dump(self.metadata("supervise"))
        combined = f"{supervise}\n{metadata}\n{self.workflow_text()}"

        for retired_contract in (
            "Current reply",
            "newest earlier assistant response labeled",
            "contains exactly one fenced",
            "label, heading, fence, or adjacency pattern",
            "fresh Reply merely to satisfy formatting",
        ):
            self.assertNotIn(retired_contract, combined)

    def test_supervise_uses_progress_based_correction_conditions(self):
        supervise = " ".join(self.skill_text("supervise").split())
        combined = f"{supervise}\n{self.workflow_text()}"

        self.assertIn(
            "continue correcting while a concrete path to completion remains",
            supervise,
        )
        self.assertIn("repeated lack of material progress", supervise)
        for retired_limit in (
            "at most two corrective follow-ups",
            "up to two corrections",
            "arbitrary follow-up count",
            "exhausted attempt count",
        ):
            self.assertNotIn(retired_limit, combined)

    def test_retired_packages_remain_archived_without_public_shims(self):
        for name in ("co-prompt", "side-mode", "side-draft", "side-run"):
            self.assertFalse((REPO_ROOT / "skills" / name).exists())

        for name in ("co-prompt", "reply", "sidekick"):
            self.assertTrue(
                (REPO_ROOT / "legacy" / "skills" / name / "SKILL.md").is_file()
            )


if __name__ == "__main__":
    unittest.main()
