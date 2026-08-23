import re
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).parents[1]
SKILL = (SKILL_DIR / "SKILL.md").read_text()
METADATA = (SKILL_DIR / "agents" / "openai.yaml").read_text()


def section(start: str, end: str | None = None) -> str:
    body = SKILL.split(start, 1)[1]
    return body.split(end, 1)[0] if end else body


SUMMARY = section("## Summarize a new parent state", "## Discuss without taking over")
DISCUSSION = section("## Discuss without taking over")
REFRESH_NORMALIZED = " ".join(
    section("## Read the right parent", "## Summarize a new parent state").split()
)
SUMMARY_NORMALIZED = " ".join(SUMMARY.split())
DISCUSSION_NORMALIZED = " ".join(DISCUSSION.split())
STATE_RULES = re.findall(r"(?ms)^- (.+?)(?=^- |\n\n|\Z)", SUMMARY)


def state_rule(fragment: str) -> str:
    rule = next(rule for rule in STATE_RULES if fragment in rule)
    return " ".join(rule.split())


class SidekickContractTests(unittest.TestCase):
    def test_state_model_routes_each_parent_state(self):
        active_unblocked = state_rule("active, unblocked")
        active_blocked = state_rule("cannot continue")
        completed_with_follow_up = state_rule("completed request")
        genuinely_finished = state_rule("genuinely finished")

        self.assertIn("no extra heading", active_unblocked)
        self.assertNotIn("**Needs from you:**", active_unblocked)
        self.assertIn("**Needs from you:**", active_blocked)
        self.assertIn("**To continue:**", completed_with_follow_up)
        self.assertIn("stops after the bottom line", genuinely_finished)
        self.assertNotIn("Nothing right now", SKILL)

    def test_work_type_and_scope_boundary_cannot_sound_implemented(self):
        self.assertIn("actual work type, current state, and boundary", SUMMARY_NORMALIZED)
        for work_type in ("audit", "diagnosis", "review", "plan", "recommendation"):
            self.assertIn(work_type, SUMMARY_NORMALIZED)
        self.assertIn("implementation did not", SUMMARY_NORMALIZED)
        self.assertIn(
            "nothing was implemented", SUMMARY_NORMALIZED
        )
        self.assertIn("nothing to implement", SUMMARY_NORMALIZED)
        self.assertIn("boundary in its own direct sentence", SUMMARY_NORMALIZED)
        self.assertIn("stage the parent explicitly states", SUMMARY_NORMALIZED)
        self.assertIn("do not invent or infer a separate implementation track", SUMMARY_NORMALIZED)

    def test_completed_analysis_surfaces_one_continuation_decision(self):
        self.assertIn("one genuine next-scope decision", SUMMARY_NORMALIZED)
        self.assertIn(
            "separate approvals or imply that the user has approved them",
            SUMMARY_NORMALIZED,
        )
        self.assertIn("clearly attributable to Sidekick", SUMMARY_NORMALIZED)
        self.assertIn(
            "identifies material actionable work has meaningful follow-up",
            SUMMARY_NORMALIZED,
        )

    def test_compression_preserves_scale_priority_and_independent_work(self):
        for concept in (
            "finding count",
            "named priority tiers and their membership",
            "finite list of independently actionable findings",
            "recommended order",
            "name each one at least once",
            "never replace distinct findings with a category label",
        ):
            self.assertIn(concept, SUMMARY_NORMALIZED)
        self.assertNotRegex(SKILL, r"at most\s+\w+\s+(?:plain\s+)?themes")

    def test_semantic_fidelity_gate_protects_decision_critical_meaning(self):
        for concept in (
            "material findings",
            "unfinished work",
            "risks",
            "explicit deferrals",
            "verification gaps",
            "recommendations",
            "next steps",
        ):
            self.assertIn(concept, SUMMARY_NORMALIZED)
        self.assertIn("materially different picture", SUMMARY_NORMALIZED)
        self.assertIn("restore the missing context", SUMMARY_NORMALIZED)

    def test_refresh_correction_and_discussion_boundaries_remain_intact(self):
        self.assertIn("no new completed response", SKILL)
        self.assertIn("Do not restart the summary template", REFRESH_NORMALIZED)
        self.assertIn("answer the user's current message naturally", DISCUSSION_NORMALIZED)
        self.assertIn("acknowledge the correction directly", DISCUSSION_NORMALIZED)
        self.assertIn(
            "what the parent reported, what you think, and what the user has decided",
            DISCUSSION_NORMALIZED,
        )
        self.assertIn("never one complete parent-ready prompt", DISCUSSION_NORMALIZED)
        self.assertIn("never send anything", DISCUSSION_NORMALIZED)

    def test_metadata_frames_results_open_work_and_user_choice(self):
        self.assertIn('short_description: "Understand parent results, open work, and choices"', METADATA)
        default_prompt = next(
            line for line in METADATA.splitlines() if "default_prompt:" in line
        )
        for concept in ("completed", "remains", "decision", "next move"):
            self.assertIn(concept, default_prompt)
        self.assertIn("allow_implicit_invocation: false", METADATA)


if __name__ == "__main__":
    unittest.main()
