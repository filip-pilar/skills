import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class SideOrchestrationMigrationTests(unittest.TestCase):
    def read_skill(self, name: str) -> str:
        return (REPO_ROOT / "skills" / name / "SKILL.md").read_text()

    def test_public_packages_have_permanent_manual_identities(self):
        for name in ("sidekick", "reply", "supervise"):
            package = REPO_ROOT / "skills" / name
            skill = (package / "SKILL.md").read_text()
            metadata = (package / "agents" / "openai.yaml").read_text()

            self.assertIn(f"name: {name}\n", skill)
            self.assertIn(f"${name}", metadata)
            self.assertIn("allow_implicit_invocation: false", metadata)

    def test_reply_and_supervise_share_one_current_prompt(self):
        reply = self.read_skill("reply")
        supervise = self.read_skill("supervise")

        self.assertIn("`Current reply`", reply)
        self.assertIn("`Current reply`", supervise)
        self.assertIn("fresh `$reply`", supervise)
        self.assertIn("explicit `$supervise`", reply)

    def test_sidekick_does_not_promote_backlogs_into_decisions(self):
        sidekick = self.read_skill("sidekick")

        self.assertLess(
            sidekick.index("`**Bottom line:**`"),
            sidekick.index("`**Needs from you:**`"),
        )
        self.assertIn("is not automatically a user decision", sidekick)
        self.assertIn("normally stop after those two lines", sidekick)
        self.assertIn("Do not reproduce the parent's report", sidekick)

    def test_reply_distinguishes_sequence_from_review_gate(self):
        reply = self.read_skill("reply")

        self.assertIn("Do not add a planning phase", reply)
        self.assertIn("ordered steps in one prompt", reply)
        self.assertIn("Preserve a pause when the user explicitly asked", reply)

    def test_supervise_respects_scope_and_uses_meaningful_stop_conditions(self):
        supervise = self.read_skill("supervise")

        self.assertIn("asks only for a plan does not permit implementation", supervise)
        self.assertIn("one\n  continuous job", supervise)
        self.assertIn("while it has a concrete reason to\nmake progress", supervise)
        self.assertIn("Do not stop merely because a fixed\nnumber", supervise)
        self.assertIn("repeatedly makes no material progress", supervise)
        self.assertIn("never an exhausted\nattempt count", supervise)
        self.assertNotIn("at most two corrective follow-ups", supervise)
        self.assertIn("do not retry", supervise)

    def test_supervise_final_status_is_semantically_calibrated(self):
        supervise = self.read_skill("supervise")

        for label in (
            "`**Done:**`",
            "`**Partly done:**`",
            "`**Blocked:**`",
            "`**Delivery uncertain:**`",
        ):
            self.assertIn(label, supervise)
        self.assertIn("re-read the parent's newest\ncompleted response", supervise)
        self.assertIn("Make that line type-accurate", supervise)
        self.assertIn("materially change the user's\nunderstanding", supervise)
        self.assertIn("A genuinely routine success", supervise)
        self.assertIn("current material\nresult across the whole supervised run", supervise)
        self.assertIn("do not revive findings, failures, or\nblockers", supervise)
        self.assertIn("stop without\ngranting it", supervise)
        self.assertIn("materially different picture", supervise)
        self.assertIn("Do not invoke Sidekick", supervise)

    def test_retired_packages_are_archived_without_public_shims(self):
        for name in ("co-prompt", "side-mode", "side-draft", "side-run"):
            self.assertFalse((REPO_ROOT / "skills" / name).exists())

        for name in ("co-prompt", "reply", "sidekick"):
            self.assertTrue(
                (REPO_ROOT / "legacy" / "skills" / name / "SKILL.md").is_file()
            )

        legacy_readme = (REPO_ROOT / "legacy" / "README.md").read_text()
        self.assertIn("not supported", legacy_readme)
        self.assertIn("absorbed into Sidekick", legacy_readme)

    def test_readme_documents_the_manual_sequence(self):
        readme = (REPO_ROOT / "README.md").read_text()

        self.assertIn("All three\norchestration skills are manual-only", readme)
        self.assertLess(readme.index("`$sidekick`"), readme.index("`$reply`"))
        self.assertLess(readme.index("`$reply`"), readme.index("`$supervise`"))


if __name__ == "__main__":
    unittest.main()
