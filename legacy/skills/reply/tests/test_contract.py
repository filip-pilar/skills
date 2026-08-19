import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]


class ReplyInstructionContractTests(unittest.TestCase):
    """Deterministic checks for instruction text and repository wiring only."""

    @classmethod
    def setUpClass(cls):
        cls.skill = (SKILL_ROOT / "SKILL.md").read_text()

    def test_instruction_carries_decision_not_unneeded_side_reasoning(self):
        self.assertIn("Carry only that decision", self.skill)
        self.assertIn("minimum Side-only context", self.skill)
        self.assertIn("reasoning, rationale, jargon, diagnoses", self.skill)
        self.assertIn("not why the Side assistant thinks it will work", self.skill)
        self.assertIn(
            "unless the user explicitly adopted that material and the parent "
            "genuinely needs it",
            self.skill,
        )

    def test_experimental_content_stays_tentative_and_in_user_tone(self):
        self.assertIn("keep experimental ideas tentative", self.skill)
        self.assertIn("Match the user's tone, directness, and register", self.skill)
        self.assertIn("do not imitate the Side assistant", self.skill)
        self.assertIn("Reference unchanged parent-known context briefly", self.skill)

    def test_approval_does_not_legitimize_unsupported_content(self):
        self.assertIn("Draft approval authorizes sending that draft only", self.skill)
        self.assertIn(
            "it does not make unsupported, unendorsed, or overclaimed content valid",
            self.skill,
        )
        self.assertNotIn("Exact-draft approval is the final attribution", self.skill)

    def test_paid_authorization_requires_user_authorized_maximum_spend(self):
        self.assertIn("explicit user-authorized maximum spend", self.skill)
        self.assertIn("exact target, allowed count", self.skill)
        self.assertIn("ask one focused question rather than inventing it", self.skill)

    def test_repository_check_runs_reply_instruction_checks(self):
        check_repo = (REPO_ROOT / "scripts" / "check-repo").read_text()
        self.assertIn('"$skills_dir/reply/tests"', check_repo)


if __name__ == "__main__":
    unittest.main()
