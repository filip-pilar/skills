import importlib.util
import io
import json
import os
import subprocess
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
    def test_interactive_prompt_reader_returns_after_first_line(self):
        expected = "Review only the relevant files."

        class InteractiveStdinBuffer:
            def isatty(self):
                return True

            def readline(self, size):
                self.size = size
                return expected.encode("utf-8") + b"\n"

            def read(self, size):
                raise AssertionError("interactive input must not wait for EOF")

        class InteractiveStdin:
            buffer = InteractiveStdinBuffer()

        self.assertEqual(wdyt.read_stdin_prompt(InteractiveStdin()), expected)
        self.assertEqual(
            InteractiveStdin.buffer.size,
            wdyt.MAX_PROMPT_BYTES + 2,
        )

    def test_piped_prompt_reader_accepts_eof_without_trailing_newline(self):
        prompt = io.BytesIO(b"Give an independent view.")
        self.assertEqual(
            wdyt.read_stdin_prompt(prompt),
            "Give an independent view.",
        )

    def test_piped_prompt_reader_reads_to_eof_and_normalizes_multiline(self):
        first_line = b"Review the transport.\n"

        class PipedStdinBuffer:
            def isatty(self):
                return False

            def readline(self, size):
                self.readline_size = size
                return first_line

            def read(self, size):
                self.read_size = size
                return (
                    b"  Inspect only\t relevant files.  \r\n"
                    b"Judge correctness.\n"
                )

        class PipedStdin:
            buffer = PipedStdinBuffer()

        self.assertEqual(
            wdyt.read_stdin_prompt(PipedStdin()),
            "Review the transport. Inspect only relevant files. Judge correctness.",
        )
        self.assertEqual(
            PipedStdin.buffer.readline_size,
            wdyt.MAX_PROMPT_BYTES + 2,
        )
        self.assertEqual(
            PipedStdin.buffer.read_size,
            wdyt.MAX_PROMPT_INPUT_BYTES + 1 - len(first_line),
        )

    def test_prompt_reader_rejects_oversized_context(self):
        prompt = io.BytesIO(b"x" * (wdyt.MAX_PROMPT_BYTES + 1) + b"\n")
        with self.assertRaisesRegex(wdyt.WdytError, "summarize.*short question"):
            wdyt.read_stdin_prompt(prompt)

    def test_runtime_delivers_normalized_prompt_to_claude_stdin(self):
        expected = (
            "Review the transport. Inspect only relevant files. Judge correctness."
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_claude = root / "claude"
            help_output = "Claude Code\n" + "\n".join(sorted(wdyt.REQUIRED_FLAGS))
            fake_claude.write_text(
                f"""#!{sys.executable}
import json
import sys

if "--version" in sys.argv:
    print("Claude Code fake 1.0")
    raise SystemExit
if "--help" in sys.argv:
    print({help_output!r})
    raise SystemExit

task = sys.stdin.read()
answer = {answer_fixture()!r}
answer["verdict"] = task
init = {{
    "type": "system",
    "subtype": "init",
    "model": "fake-model",
    "tools": ["StructuredOutput"],
    "mcp_servers": [],
    "plugins": [],
    "skills": [],
    "slash_commands": [],
}}
result = {{
    "type": "result",
    "subtype": "success",
    "is_error": False,
    "structured_output": answer,
}}
print(json.dumps(init))
print(json.dumps(result))
"""
            )
            fake_claude.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{root}{os.pathsep}{environment.get('PATH', '')}"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNTIME_PATH),
                    "run",
                    "--repository",
                    "off",
                ],
                input=(
                    "Review the transport.\n"
                    "  Inspect only\t relevant files.  \n"
                    "Judge correctness.\n"
                ),
                text=True,
                capture_output=True,
                env=environment,
                timeout=10,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(f"\n{expected}\n", completed.stdout)
        self.assertEqual(completed.stderr, "")

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

    def test_claude_schema_removes_unsupported_constraints(self):
        original = wdyt.load_schema()
        transformed = wdyt.schema_for_claude(original)

        self.assertEqual(transformed["$id"], "wdyt-answer/2")
        self.assertEqual(
            transformed["properties"]["protocolVersion"]["const"],
            "wdyt-answer/2",
        )
        serialized = json.dumps(transformed)
        for keyword in wdyt.CLAUDE_SCHEMA_UNSUPPORTED_CONSTRAINTS:
            self.assertNotIn(f'"{keyword}"', serialized)
        self.assertIn("maxLength", json.dumps(original))
        self.assertIn(
            "maximum 600 characters",
            transformed["properties"]["verdict"]["description"],
        )
        self.assertIn(
            "maximum 5 items",
            transformed["properties"]["rationale"]["description"],
        )

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

    def test_run_parser_accepts_launch_controls_without_request_json(self):
        parsed = wdyt.build_parser().parse_args(
            [
                "run",
                "--model",
                "claude-opus-5",
                "--mode",
                "review",
                "--depth",
                "standard",
                "--repository",
                "read",
                "--lifecycle",
                "fresh",
            ]
        )
        self.assertEqual(parsed.model, "claude-opus-5")
        self.assertEqual(parsed.repository, "read")

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
Context: minimal · repo off
Disclosure: Anthropic via Claude Code · short task + no repo
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

    def test_nonzero_exit_reports_sanitized_result_metadata(self):
        stdout = json.dumps(
            {
                "type": "result",
                "subtype": "error_max_structured_output_retries",
                "is_error": True,
                "errors": ["private provider detail"],
            }
        )
        with self.assertRaisesRegex(
            wdyt.WdytError,
            "error_max_structured_output_retries.*errors=1",
        ) as raised:
            wdyt.validate_turn(
                wdyt.validate_request({"repository": "off"}),
                capabilities(),
                None,
                1,
                stdout,
                "",
            )
        self.assertNotIn("private provider detail", str(raised.exception))

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
