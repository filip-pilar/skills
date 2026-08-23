"""Structural guards for Supervise's handoff contract, not behavior evals."""

import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


class SuperviseHandoffContractStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL.read_text(encoding="utf-8")

    def test_material_content_precedes_status_and_compression(self):
        reconcile = self.skill.index("First establish the current material result")
        fix_content = self.skill.index("Fix this material content before choosing a")
        status = self.skill.index("Then begin with exactly one bold status label")
        compression = self.skill.index("Compress routine detail")

        self.assertLess(reconcile, fix_content)
        self.assertLess(fix_content, status)
        self.assertLess(status, compression)

    def test_material_qualifiers_are_evidence_anchored_and_skimmable(self):
        self.assertIn("Include only qualifiers supported by the supervised run", self.skill)
        self.assertIn("It remains material\nwhen it is outside the approved scope", self.skill)
        self.assertIn("make it skimmable", self.skill)
        self.assertIn("its practical consequence", self.skill)
        self.assertIn("must not remove or weaken any of it", self.skill)
        self.assertIn("Preserve the scale and relationship of material results", self.skill)

    def test_one_line_success_requires_no_material_qualifier(self):
        self.assertIn(
            "ends after one concise status line only\n"
            "when the reconciled material content contains no qualifier",
            self.skill,
        )


if __name__ == "__main__":
    unittest.main()
