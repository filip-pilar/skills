import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = SKILL_ROOT / "scripts" / "wdyt.py"
SPEC = importlib.util.spec_from_file_location("wdyt_runtime", RUNTIME_PATH)
assert SPEC and SPEC.loader
wdyt = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wdyt
SPEC.loader.exec_module(wdyt)


def answer_fixture():
    return {
        "protocolVersion": "wdyt-answer/2",
        "verdict": "Run the reversible pilot.",
        "confidence": "high",
        "rationale": [
            {
                "point": "It tests the load-bearing assumption.",
                "evidence": [
                    {"kind": "context", "ref": "objective"},
                    {"kind": "inference", "ref": None},
                ],
            }
        ],
        "risks": ["The pilot may be too small."],
        "unknowns": ["Production traffic shape is unknown."],
        "nextStep": "Run the pilot for one day.",
        "decisionPrompt": None,
    }


def capabilities(optional=("--model", "--effort")):
    return wdyt.Capabilities(
        binary="/usr/local/bin/claude",
        version="arbitrary future Claude Code",
        missing_flags=(),
        supported_optional_flags=tuple(optional),
        official_signal=True,
    )


class RuntimeTests(unittest.TestCase):
    def test_any_explicit_model_is_passed_through(self):
        request = wdyt.validate_request(
            {
                "model": "future-model/name with spaces",
                "repository": "off",
                "lifecycle": "ephemeral",
            }
        )
        self.assertEqual(request.model, "future-model/name with spaces")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings, mcp = wdyt.write_private_inputs(root, None)
            args = wdyt.build_claude_args(
                capabilities(), request, None, settings, mcp
            )
        model_index = args.index("--model")
        self.assertEqual(args[model_index + 1], "future-model/name with spaces")
        self.assertNotIn("--fallback-model", args)

    def test_default_model_omits_model_and_optional_tuning(self):
        request = wdyt.validate_request({"repository": "off"})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings, mcp = wdyt.write_private_inputs(root, None)
            args = wdyt.build_claude_args(
                capabilities(optional=()), request, None, settings, mcp
            )
        self.assertNotIn("--model", args)
        self.assertNotIn("--effort", args)
        self.assertNotIn("--include-partial-messages", args)
        self.assertNotIn("--prompt-suggestions", args)

    def test_only_fresh_and_ephemeral_are_valid(self):
        self.assertEqual(
            wdyt.validate_request({"lifecycle": "fresh"}).lifecycle, "fresh"
        )
        self.assertEqual(
            wdyt.validate_request({"lifecycle": "ephemeral"}).lifecycle,
            "ephemeral",
        )
        with self.assertRaisesRegex(wdyt.WdytError, "only fresh and ephemeral"):
            wdyt.validate_request({"lifecycle": "continue"})

    def test_renderer_is_deterministic(self):
        request = wdyt.validate_request(
            {
                "model": "alias",
                "mode": "advise",
                "repository": "off",
                "lifecycle": "fresh",
            }
        )
        turn = wdyt.Turn(
            request=request,
            version="any",
            used_model="resolved-model",
            answer=answer_fixture(),
            tools=["StructuredOutput"],
            tool_calls=[],
            usage={},
            model_usage={},
            cost_usd=None,
        )
        self.assertEqual(
            wdyt.render_turn(turn),
            """WDYT · Claude Code · resolved-model · advise · fresh
Context: state · repo off
Disclosure: Anthropic via Claude Code · task context + no repo
Model: alias → resolved-model

Run the reversible pilot.

Why
1. It tests the load-bearing assumption. [objective]

Watch
• Risk: The pilot may be too small.
• Unknown: Production traffic shape is unknown.

Next
Run the pilot for one day.

Confidence: high""",
        )

    def test_successful_events_accept_arbitrary_used_model(self):
        request = wdyt.validate_request({"repository": "off"})
        init = {
            "type": "system",
            "subtype": "init",
            "model": "unlisted-new-model",
            "tools": ["StructuredOutput"],
            "mcp_servers": [],
            "plugins": [],
            "skills": [],
            "slash_commands": [],
        }
        assistant = {
            "type": "assistant",
            "message": {
                "model": "unlisted-new-model",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "StructuredOutput",
                        "input": answer_fixture(),
                    }
                ],
            },
        }
        result = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "structured_output": answer_fixture(),
        }
        stdout = "\n".join(json.dumps(event) for event in (init, assistant, result))
        turn = wdyt.validate_turn(
            request, capabilities(), None, 0, stdout, ""
        )
        self.assertEqual(turn.used_model, "unlisted-new-model")

    def test_answer_validator_matches_discriminated_evidence_schema(self):
        answer = answer_fixture()
        self.assertEqual(wdyt.validate_answer(answer), answer)

        inference_with_ref = json.loads(json.dumps(answer))
        inference_with_ref["rationale"][0]["evidence"][1]["ref"] = "objective"
        with self.assertRaisesRegex(wdyt.WdytError, "inference evidence"):
            wdyt.validate_answer(inference_with_ref)

        repository_without_ref = json.loads(json.dumps(answer))
        repository_without_ref["rationale"][0]["evidence"][0] = {
            "kind": "repository",
            "ref": None,
        }
        with self.assertRaisesRegex(wdyt.WdytError, "must be a string"):
            wdyt.validate_answer(repository_without_ref)

    def test_unexpected_tool_fails_closed(self):
        request = wdyt.validate_request({"repository": "off"})
        init = {
            "type": "system",
            "subtype": "init",
            "model": "model",
            "tools": ["StructuredOutput", "Bash"],
        }
        result = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "structured_output": answer_fixture(),
        }
        stdout = "\n".join(json.dumps(event) for event in (init, result))
        with self.assertRaisesRegex(wdyt.WdytError, "registered tools"):
            wdyt.validate_turn(request, capabilities(), None, 0, stdout, "")

    def test_symlink_escape_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repository = base / "repo"
            repository.mkdir()
            outside = base / "outside.txt"
            outside.write_text("secret")
            (repository / "escape").symlink_to(outside)
            with self.assertRaisesRegex(wdyt.WdytError, "out-of-root"):
                wdyt.validate_tool_paths(
                    [{"name": "Read", "input": {"file_path": "escape"}}],
                    repository.resolve(),
                )

    def test_grep_regex_is_not_validated_as_a_filesystem_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary).resolve()
            wdyt.validate_tool_paths(
                [
                    {
                        "name": "Grep",
                        "input": {
                            "pattern": r"/usr/bin/env|a/\.\./b",
                            "path": ".",
                        },
                    }
                ],
                repository,
            )

    def test_grep_path_and_glob_still_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary).resolve()
            with self.assertRaisesRegex(wdyt.WdytError, "out-of-root"):
                wdyt.validate_tool_paths(
                    [
                        {
                            "name": "Grep",
                            "input": {"pattern": "safe", "path": "../outside"},
                        }
                    ],
                    repository,
                )
            with self.assertRaisesRegex(wdyt.WdytError, "escaping pattern"):
                wdyt.validate_tool_paths(
                    [
                        {
                            "name": "Grep",
                            "input": {"pattern": "safe", "glob": "../*.py"},
                        }
                    ],
                    repository,
                )


if __name__ == "__main__":
    unittest.main()
