import re
import unittest
from dataclasses import dataclass


@dataclass(frozen=True)
class ReportingScenario:
    required_concepts: dict[str, tuple[str, ...]]


def missing_concepts(report: str, scenario: ReportingScenario) -> list[str]:
    normalized = " ".join(report.lower().split())
    return [
        concept
        for concept, alternatives in scenario.required_concepts.items()
        if not any(re.search(pattern, normalized) for pattern in alternatives)
    ]


DESIGN_ASSESSMENT = ReportingScenario(
    required_concepts={
        "assessment, not implementation": (
            r"assessment .{0,80}(?:no|not) implement",
            r"(?:no|not) implement.{0,80}assessment",
        ),
        "systemic redesign": (r"systemic redesign", r"version[- ]?2 redesign"),
        "several incompatibilities": (
            r"(?:several|multiple|three) incompatibilit",
            r"incompatibilit.{0,120}incompatibilit",
        ),
        "staged recommendation": (
            r"recommend.{0,100}stage",
            r"staged.{0,100}recommend",
        ),
    }
)


CONFIGURATION_CLEANUP = ReportingScenario(
    required_concepts={
        "successful mutations": (r"(?:updated|removed|cleanup|mutations?) succeeded",),
        "unresolved indexed-history mismatch with scale": (
            r"(?:indexed|history).{0,80}mismatch.{0,80}(?:across|entries|records|large|material)",
            r"(?:across|entries|records|large|material).{0,80}(?:indexed|history).{0,80}mismatch",
        ),
        "unsafe or unsupported repair": (r"(?:unsafe|unsupported).{0,80}repair",),
        "recommended escalation": (r"recommend.{0,80}escalat", r"escalat.{0,80}recommend"),
        "explicitly deferred work": (r"(?:explicitly )?defer",),
    }
)


TRIVIAL_SUCCESS = ReportingScenario(
    required_concepts={
        "implementation": (r"implement", r"updated", r"changed"),
        "verification": (r"verif", r"check.{0,30}pass", r"test.{0,30}pass"),
    }
)


class SuperviseReportingSemanticsTests(unittest.TestCase):
    def assert_semantically_complete(self, report: str, scenario: ReportingScenario) -> None:
        self.assertEqual([], missing_concepts(report, scenario))

    def test_complex_assessment_cannot_collapse_to_one_minor_bug(self):
        underreported = (
            "**Done:** The parent revised the architecture and proposed an order. "
            "**Checked:** A sequence filename mismatch is real."
        )
        self.assertGreaterEqual(len(missing_concepts(underreported, DESIGN_ASSESSMENT)), 3)

        handoff = (
            "**Done:** The design assessment is complete; no implementation occurred. "
            "It found a systemic redesign is required, including three incompatibilities. "
            "**Recommended next step:** Follow the staged recommendation: freeze the "
            "version-2 contracts, prove the offline path, then add the provider adapter."
        )
        self.assert_semantically_complete(handoff, DESIGN_ASSESSMENT)

    def test_cleanup_preserves_material_unresolved_history_problem(self):
        underreported = "**Done:** The configuration cleanup succeeded and checks passed."
        self.assertGreaterEqual(
            len(missing_concepts(underreported, CONFIGURATION_CLEANUP)), 4
        )

        handoff = (
            "**Partly done:** The requested removals and configuration cleanup succeeded, "
            "but an indexed-history mismatch remains across hundreds of records. "
            "Direct repair is unsafe and unsupported. **Recommended next step:** Escalate "
            "to the owning system before repair. The unrelated migration was explicitly deferred."
        )
        self.assert_semantically_complete(handoff, CONFIGURATION_CLEANUP)

    def test_trivial_verified_change_remains_one_line(self):
        handoff = "**Done:** Updated the label and verified the focused test passes."
        self.assert_semantically_complete(handoff, TRIVIAL_SUCCESS)
        self.assertNotIn("\n", handoff)
        self.assertLess(len(handoff), 100)


if __name__ == "__main__":
    unittest.main()
