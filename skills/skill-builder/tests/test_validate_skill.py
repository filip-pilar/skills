from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "skill-builder" / "scripts" / "validate_skill.py"


class MetadataValidationTests(unittest.TestCase):
    def validate(
        self,
        *,
        description: str,
        implicit: bool | None,
        default_prompt: str,
        short_description: str = "Validate sample metadata behavior",
        reference: str | None = None,
        reference_linked: bool = True,
        chained_reference: bool = False,
        binary_asset: bool = False,
        escaped_symlink: bool = False,
        bundled_evals: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "sample"
            agents_dir = skill_dir / "agents"
            agents_dir.mkdir(parents=True)
            skill_text = textwrap.dedent(
                f"""\
                    ---
                    name: sample
                    description: {description}
                    ---

                    # Sample

                    Follow the runtime workflow.
                    """
            )
            if reference is not None and reference_linked:
                skill_text += "\nRead [status](references/status.md).\n"
            if binary_asset and reference_linked:
                skill_text += "\nLoad `assets/payload.bin`.\n"
            (skill_dir / "SKILL.md").write_text(skill_text, encoding="utf-8")
            metadata = (
                "interface:\n"
                '  display_name: "Sample"\n'
                f'  short_description: "{short_description}"\n'
                f'  default_prompt: "{default_prompt}"\n'
            )
            if implicit is not None:
                metadata += f"\npolicy:\n  allow_implicit_invocation: {str(implicit).lower()}\n"
            (agents_dir / "openai.yaml").write_text(metadata, encoding="utf-8")
            if reference is not None:
                references = skill_dir / "references"
                references.mkdir()
                (references / "status.md").write_text(reference, encoding="utf-8")
                if chained_reference:
                    (references / "details.md").write_text(
                        "Return to [status](status.md).\n",
                        encoding="utf-8",
                    )
            if bundled_evals:
                evals = skill_dir / "evals"
                evals.mkdir()
                (evals / "answer-key.md").write_text("Expected output.\n", encoding="utf-8")
            if binary_asset:
                assets = skill_dir / "assets"
                assets.mkdir()
                (assets / "payload.bin").write_bytes(b"\x00\xff\x00\xff")
            if escaped_symlink:
                outside = Path(temp_dir) / "outside.txt"
                outside.write_text("outside\n", encoding="utf-8")
                references = skill_dir / "references"
                references.mkdir(exist_ok=True)
                (references / "outside.txt").symlink_to(outside)
            return subprocess.run(
                [sys.executable, str(VALIDATOR), str(skill_dir)],
                check=False,
                capture_output=True,
                text=True,
            )

    def test_clean_manual_only_metadata_passes(self) -> None:
        result = self.validate(
            description="Formatter for supplied notes.",
            implicit=False,
            default_prompt="Use $sample to format these notes.",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_manual_description_rejects_explicit_command(self) -> None:
        result = self.validate(
            description="Formatter for supplied notes. Use $sample explicitly.",
            implicit=False,
            default_prompt="Use $sample to format these notes.",
        )
        self.assertIn("description must not contain $skill commands", result.stdout)

    def test_manual_description_rejects_reentry_behavior(self) -> None:
        result = self.validate(
            description="Formatter for supplied notes. A bare invocation refreshes the result.",
            implicit=False,
            default_prompt="Use $sample to format these notes.",
        )
        self.assertIn("must not encode invocation or re-entry behavior", result.stdout)

    def test_manual_description_rejects_policy_label(self) -> None:
        result = self.validate(
            description="Manual-only formatter for supplied notes.",
            implicit=False,
            default_prompt="Use $sample to format these notes.",
        )
        self.assertIn("description must not restate invocation policy", result.stdout)

    def test_manual_description_rejects_generic_invocation_instruction(self) -> None:
        result = self.validate(
            description="Formatter for supplied notes. Invoke this skill explicitly.",
            implicit=False,
            default_prompt="Use $sample to format these notes.",
        )
        self.assertIn("must not encode invocation or re-entry behavior", result.stdout)

    def test_manual_description_rejects_trigger_instruction(self) -> None:
        result = self.validate(
            description="Formatter for supplied notes. Use only when the user asks for formatting.",
            implicit=False,
            default_prompt="Use $sample to format these notes.",
        )
        self.assertIn("must not encode invocation or re-entry behavior", result.stdout)

    def test_manual_default_prompt_requires_explicit_command(self) -> None:
        result = self.validate(
            description="Formatter for supplied notes.",
            implicit=False,
            default_prompt="Format these supplied notes.",
        )
        self.assertIn("manual-only default_prompt must mention $sample", result.stdout)

    def test_implicit_default_prompt_need_not_repeat_command(self) -> None:
        result = self.validate(
            description="Format supplied notes when the user requests a compact summary.",
            implicit=True,
            default_prompt="Format these supplied notes.",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_policy_defaults_to_implicit(self) -> None:
        result = self.validate(
            description="Use this skill when the user requests a compact note summary.",
            implicit=None,
            default_prompt="Format these supplied notes.",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_short_description_rejects_skill_command(self) -> None:
        result = self.validate(
            description="Formatter for supplied notes.",
            implicit=False,
            default_prompt="Use $sample to format these notes.",
            short_description="Use $sample to format notes now",
        )
        self.assertIn("short_description must summarize capability", result.stdout)

    def test_short_description_rejects_invocation_policy(self) -> None:
        result = self.validate(
            description="Formatter for supplied notes.",
            implicit=False,
            default_prompt="Use $sample to format these notes.",
            short_description="Manual-only formatter for notes",
        )
        self.assertIn("not invocation policy or instructions", result.stdout)

    def test_todo_status_is_not_an_unresolved_placeholder(self) -> None:
        result = self.validate(
            description="Format supplied notes when the user requests a compact summary.",
            implicit=True,
            default_prompt="Format these supplied notes.",
            reference="Status: TODO | IN PROGRESS | DONE\n",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_bracketed_todo_remains_invalid(self) -> None:
        result = self.validate(
            description="Format supplied notes when the user requests a compact summary.",
            implicit=True,
            default_prompt="Format these supplied notes.",
            reference="[TODO: replace this reference]\n",
        )
        self.assertIn("unresolved TODO placeholder", result.stdout)

    def test_unreferenced_bundled_resource_is_rejected(self) -> None:
        result = self.validate(
            description="Format supplied notes when the user requests a compact summary.",
            implicit=True,
            default_prompt="Format these supplied notes.",
            reference="Supporting instructions.\n",
            reference_linked=False,
        )
        self.assertIn("bundled resource is not reachable from SKILL.md", result.stdout)

    def test_transitively_referenced_resource_passes(self) -> None:
        result = self.validate(
            description="Format supplied notes when the user requests a compact summary.",
            implicit=True,
            default_prompt="Format these supplied notes.",
            reference="Read [details](details.md).\n",
            chained_reference=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_orphan_reference_cycle_is_rejected(self) -> None:
        result = self.validate(
            description="Format supplied notes when the user requests a compact summary.",
            implicit=True,
            default_prompt="Format these supplied notes.",
            reference="Read [details](details.md).\n",
            reference_linked=False,
            chained_reference=True,
        )
        self.assertIn("references/status.md: bundled resource is not reachable", result.stdout)
        self.assertIn("references/details.md: bundled resource is not reachable", result.stdout)

    def test_referenced_binary_resource_passes(self) -> None:
        result = self.validate(
            description="Format supplied notes when the user requests a compact summary.",
            implicit=True,
            default_prompt="Format these supplied notes.",
            binary_asset=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unreferenced_binary_resource_is_rejected(self) -> None:
        result = self.validate(
            description="Format supplied notes when the user requests a compact summary.",
            implicit=True,
            default_prompt="Format these supplied notes.",
            binary_asset=True,
            reference_linked=False,
        )
        self.assertIn("assets/payload.bin: bundled resource is not reachable", result.stdout)

    def test_symlink_cannot_escape_skill_directory(self) -> None:
        result = self.validate(
            description="Format supplied notes when the user requests a compact summary.",
            implicit=True,
            default_prompt="Format these supplied notes.",
            escaped_symlink=True,
        )
        self.assertIn("symlink escapes the skill directory", result.stdout)

    def test_bundled_evaluation_directory_is_rejected(self) -> None:
        result = self.validate(
            description="Format supplied notes when the user requests a compact summary.",
            implicit=True,
            default_prompt="Format these supplied notes.",
            bundled_evals=True,
        )
        self.assertIn("evaluation directory must live outside", result.stdout)


if __name__ == "__main__":
    unittest.main()
