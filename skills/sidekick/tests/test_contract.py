import unittest
from pathlib import Path


SKILL = (Path(__file__).parents[1] / "SKILL.md").read_text()
NORMALIZED = " ".join(SKILL.split())


class SidekickContractTests(unittest.TestCase):
    def test_initial_and_materially_new_parent_summaries_use_the_opener(self):
        self.assertIn(
            "only for the initial Sidekick explanation and for a summary of "
            "materially new completed parent state",
            NORMALIZED,
        )
        self.assertLess(
            SKILL.index("`**Bottom line:**`"),
            SKILL.index("`**Needs from you:**`"),
        )

    def test_ordinary_follow_up_does_not_repeat_the_template(self):
        self.assertIn(
            "During ordinary follow-up discussion, answer the user's current "
            "message naturally.",
            NORMALIZED,
        )
        self.assertIn(
            "Do not repeat `**Bottom line:**` or `**Needs from you:**` merely "
            "to preserve a template",
            NORMALIZED,
        )

    def test_user_correction_gets_a_direct_response(self):
        self.assertIn(
            "If the user corrects a fact, acknowledge the correction directly "
            "and revise only the conclusions that depended on it.",
            NORMALIZED,
        )

    def test_later_blocker_can_surface_needs_from_you(self):
        self.assertIn(
            "Use `**Needs from you:**` outside a new-state summary only when a "
            "genuine blocking question or decision emerges.",
            NORMALIZED,
        )

    def test_non_blocking_work_is_not_promoted_into_a_decision(self):
        self.assertIn(
            "A backlog, recommendation, implementation detail, or safeguard "
            "is not automatically a user decision.",
            NORMALIZED,
        )

    def test_unchanged_refresh_does_not_restart_the_template(self):
        self.assertIn(
            "When a refresh finds no new completed response, say so briefly. "
            "Do not restart the summary template.",
            NORMALIZED,
        )

    def test_my_take_heading_is_optional(self):
        self.assertIn(
            "Keep a recommendation clearly attributable to Sidekick.",
            NORMALIZED,
        )
        self.assertIn(
            "Use `**My take:**` only when the heading genuinely improves "
            "scanning",
            NORMALIZED,
        )


if __name__ == "__main__":
    unittest.main()
