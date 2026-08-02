import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


class WdytLaunchContractTests(unittest.TestCase):
    def test_dedicated_launcher_is_executable_and_fail_closed(self):
        launcher = SKILL_ROOT / "scripts" / "wdyt"
        self.assertTrue(os.access(launcher, os.X_OK))
        text = launcher.read_text()
        self.assertIn("/usr/bin/python3 -I", text)
        self.assertIn('"$@"', text)
        self.assertNotIn("eval ", text)
        self.assertNotIn("sh -c", text)
        self.assertIn("launcher must be invoked by absolute path", text)
        self.assertIn("launcher must be a regular installed file", text)

        completed = subprocess.run(
            [str(launcher), "shell"],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("invalid choice", completed.stderr)

    def test_dedicated_launcher_rejects_symlink_entrypoint(self):
        launcher = SKILL_ROOT / "scripts" / "wdyt"
        with tempfile.TemporaryDirectory() as temporary:
            linked = Path(temporary) / "wdyt"
            linked.symlink_to(launcher)
            completed = subprocess.run(
                [str(linked), "doctor"],
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("not a symlink", completed.stderr)

    def test_skill_requires_direct_launcher_without_reusable_rule(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text()
        invocation = (
            SKILL_ROOT / "references" / "invocation-and-context.md"
        ).read_text()
        self.assertIn("<skill-root>/scripts/wdyt doctor", skill)
        self.assertIn("<skill-root>/scripts/wdyt run", skill)
        self.assertNotIn("python3 <skill-root>", f"{skill}\n{invocation}")
        self.assertIn("Never request or propose a reusable", skill)

    def test_answer_schema_discriminates_evidence_references(self):
        schema = json.loads(
            (SKILL_ROOT / "assets" / "wdyt-answer-2.schema.json").read_text()
        )
        self.assertEqual(schema["$id"], "wdyt-answer/2")
        self.assertEqual(schema["properties"]["protocolVersion"]["type"], "string")
        evidence = schema["properties"]["rationale"]["items"]["properties"][
            "evidence"
        ]["items"]
        branches = evidence["oneOf"]
        inference = next(
            branch
            for branch in branches
            if branch["properties"]["kind"].get("const") == "inference"
        )
        sourced = next(
            branch
            for branch in branches
            if branch["properties"]["kind"].get("enum")
            == ["context", "repository"]
        )
        self.assertEqual(inference["required"], ["kind", "ref"])
        self.assertEqual(inference["properties"]["ref"]["type"], "null")
        self.assertEqual(sourced["required"], ["kind", "ref"])
        self.assertEqual(sourced["properties"]["ref"]["type"], "string")
        self.assertEqual(sourced["properties"]["ref"]["minLength"], 1)

    def test_prompt_uses_current_protocols_and_remains_advisory(self):
        prompt = (SKILL_ROOT / "assets" / "wdyt-adviser-3.txt").read_text()
        self.assertIn("short task supplied on stdin", prompt)
        self.assertIn("wdyt-answer/2", prompt)
        self.assertIn("You advise; you do not execute.", prompt)
        self.assertIn("Never use logical `/repo` as a literal tool path.", prompt)

    def test_launch_uses_short_plain_text_instead_of_context_envelope(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text()
        invocation = (
            SKILL_ROOT / "references" / "invocation-and-context.md"
        ).read_text()
        runtime = (SKILL_ROOT / "scripts" / "wdyt.py").read_text()
        combined = f"{skill}\n{invocation}\n{runtime}"
        self.assertIn("one short", combined)
        self.assertNotIn("wdyt-context/3", combined)
        self.assertNotIn("build_context_envelope", runtime)

    def test_contract_is_feature_detected_and_model_agnostic(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text()
        cli_contract = (SKILL_ROOT / "references" / "claude-cli.md").read_text()
        package_text = f"{skill}\n{cli_contract}"

        self.assertIn("scripts/wdyt", package_text)
        self.assertIn("wdyt.py", package_text)
        self.assertIn("feature-detect", package_text)
        self.assertRegex(
            cli_contract.lower(), r"any\s+explicit non-empty model string"
        )
        self.assertNotIn("accepted candidate", package_text.lower())
        self.assertNotRegex(package_text, r"Claude Code `\d+\.\d+\.\d+`")
        self.assertNotIn("model allowlist", cli_contract.lower())

    def test_unimplemented_session_surface_is_absent(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text().lower()
        invocation = (
            SKILL_ROOT / "references" / "invocation-and-context.md"
        ).read_text().lower()

        self.assertFalse((SKILL_ROOT / "references" / "sessions.md").exists())
        self.assertNotIn("$wdyt continue", skill)
        self.assertNotIn("$wdyt continue", invocation)
        self.assertIn("only fresh and ephemeral", skill)

    def test_launch_package_has_no_codex_adviser_surface(self):
        package_text = "\n".join(
            path.read_text()
            for path in SKILL_ROOT.rglob("*")
            if path.is_file() and path.suffix in {".md", ".txt", ".yaml", ".json"}
        ).lower()
        self.assertNotIn("codex cli", package_text)
        self.assertNotIn("openai via", package_text)
        self.assertNotIn("codex backend", package_text)


if __name__ == "__main__":
    unittest.main()
