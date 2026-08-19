import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class SideOrchestrationMigrationTests(unittest.TestCase):
    def test_public_packages_have_permanent_manual_identities(self):
        for name in ("sidekick", "reply", "babysit"):
            package = REPO_ROOT / "skills" / name
            skill = (package / "SKILL.md").read_text()
            metadata = (package / "agents" / "openai.yaml").read_text()

            self.assertIn(f"name: {name}\n", skill)
            self.assertIn(f"${name}", metadata)
            self.assertIn("allow_implicit_invocation: false", metadata)

    def test_reply_and_babysit_share_one_artifact_identity(self):
        reply = (REPO_ROOT / "skills" / "reply" / "SKILL.md").read_text()
        babysit = (REPO_ROOT / "skills" / "babysit" / "SKILL.md").read_text()
        normalized_babysit = " ".join(babysit.split())

        self.assertIn("`Current reply`", reply)
        self.assertIn("`Current reply`", normalized_babysit)
        self.assertIn("fresh `$reply`", babysit)
        self.assertNotIn("side-draft", reply + babysit)

    def test_human_facing_format_contracts_are_stable(self):
        sidekick = (REPO_ROOT / "skills" / "sidekick" / "SKILL.md").read_text()
        reply = (REPO_ROOT / "skills" / "reply" / "SKILL.md").read_text()
        babysit = (REPO_ROOT / "skills" / "babysit" / "SKILL.md").read_text()

        self.assertLess(sidekick.index("`**Bottom line:**`"), sidekick.index("`**Needs from you:**`"))
        self.assertLess(sidekick.index("`**Needs from you:**`"), sidekick.index("`**Why it matters:**`"))
        self.assertIn("stop after those two sections\nby default", sidekick)
        self.assertIn("Do not\nuse bullets to summarize a long parent list", sidekick)

        self.assertIn("output only the label `Current reply`", reply)
        self.assertIn("exactly one fenced `text` block", reply)

        for label in (
            "`**Done:**`",
            "`**Partly done:**`",
            "`**Blocked:**`",
            "`**Delivery uncertain:**`",
            "`**Checked:**`",
            "`**Still open:**`",
            "`**Needs from you:**`",
        ):
            self.assertIn(label, babysit)
        self.assertIn("Every final user-facing response begins", babysit)
        self.assertIn("A normal\ncompleted run ends after that line. It has no bullets", babysit)

    def test_retired_packages_are_archived_without_public_shims(self):
        for name in ("co-prompt", "side-mode", "side-draft", "side-run"):
            self.assertFalse((REPO_ROOT / "skills" / name).exists())

        for name in ("co-prompt", "reply", "sidekick"):
            self.assertTrue((REPO_ROOT / "legacy" / "skills" / name / "SKILL.md").is_file())

        legacy_readme = (REPO_ROOT / "legacy" / "README.md").read_text()
        self.assertIn("not supported", legacy_readme)
        self.assertIn("absorbed into Sidekick", legacy_readme)

    def test_readme_documents_the_manual_sequence(self):
        readme = (REPO_ROOT / "README.md").read_text()

        self.assertIn("All three\norchestration skills are manual-only", readme)
        self.assertLess(readme.index("`$sidekick`"), readme.index("`$reply`"))
        self.assertLess(readme.index("`$reply`"), readme.index("`$babysit`"))


if __name__ == "__main__":
    unittest.main()
