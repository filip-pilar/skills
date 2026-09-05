import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


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


def write_capability_probe(root: Path) -> Path:
    fake_claude = root / "claude"
    help_output = "Claude Code\n" + "\n".join(sorted(wdyt.REQUIRED_FLAGS))
    fake_claude.write_text(
        f"""#!{sys.executable}
import json
import os
import sys

mode = os.environ.get("WDYT_FAKE_MODE", "ok")
if "--version" in sys.argv:
    if mode == "bad-version":
        raise SystemExit(1)
    print("Claude Code fake 1.0")
    raise SystemExit
if "--help" in sys.argv:
    if mode == "bad-help":
        raise SystemExit(1)
    print({help_output!r})
    raise SystemExit
if sys.argv[1:] == ["auth", "status", "--json"]:
    if mode == "malformed-auth":
        print("{{")
    elif mode == "incomplete-auth":
        print("{{}}")
    elif mode == "logged-out":
        print(json.dumps({{
            "loggedIn": False,
            "authMethod": "none",
            "apiProvider": "firstParty",
        }}))
    else:
        print(json.dumps({{
            "loggedIn": True,
            "authMethod": "oauth",
            "apiProvider": "firstParty",
        }}))
    raise SystemExit
raise SystemExit(2)
"""
    )
    fake_claude.chmod(0o755)
    return fake_claude


class RuntimeTests(unittest.TestCase):
    def test_detect_capabilities_exercises_external_failure_surfaces(self):
        with patch.object(wdyt.shutil, "which", return_value=None):
            with self.assertRaisesRegex(wdyt.WdytError, "not found on PATH"):
                wdyt.detect_capabilities()

        cases = (
            ("bad-version", "usable version", "runtime_failure"),
            ("bad-help", "print-mode help failed", "runtime_failure"),
            (
                "malformed-auth",
                "malformed authentication status",
                "authentication_status_unavailable",
            ),
            (
                "incomplete-auth",
                "incomplete authentication status",
                "authentication_status_unavailable",
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            fake_claude = write_capability_probe(Path(temporary))
            for mode, message, category in cases:
                with (
                    self.subTest(mode=mode),
                    patch.object(wdyt.shutil, "which", return_value=str(fake_claude)),
                    patch.dict(os.environ, {"WDYT_FAKE_MODE": mode}, clear=False),
                    self.assertRaisesRegex(wdyt.WdytError, message) as raised,
                ):
                    wdyt.detect_capabilities()
                self.assertEqual(raised.exception.category, category)

    def test_detect_capabilities_distinguishes_sandbox_auth_and_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            fake_claude = write_capability_probe(Path(temporary))
            cases = (
                (
                    "logged-out",
                    {
                        "WDYT_FAKE_MODE": "logged-out",
                        "CODEX_SANDBOX": "seatbelt",
                        "CODEX_SANDBOX_NETWORK_DISABLED": "0",
                    },
                    False,
                    True,
                ),
                (
                    "logged-in-network-blocked",
                    {
                        "WDYT_FAKE_MODE": "ok",
                        "CODEX_SANDBOX": "seatbelt",
                        "CODEX_SANDBOX_NETWORK_DISABLED": "1",
                    },
                    True,
                    True,
                ),
                (
                    "logged-in-network-available",
                    {
                        "WDYT_FAKE_MODE": "ok",
                        "CODEX_SANDBOX": "seatbelt",
                        "CODEX_SANDBOX_NETWORK_DISABLED": "0",
                    },
                    True,
                    False,
                ),
                (
                    "escalated-stale-network-marker",
                    {
                        "WDYT_FAKE_MODE": "ok",
                        "CODEX_SANDBOX": "",
                        "CODEX_SANDBOX_NETWORK_DISABLED": "1",
                    },
                    True,
                    False,
                ),
            )
            for name, environment, authenticated, escalation_required in cases:
                with (
                    self.subTest(name=name),
                    patch.object(wdyt.shutil, "which", return_value=str(fake_claude)),
                    patch.dict(os.environ, environment, clear=False),
                ):
                    detected = wdyt.detect_capabilities()
                self.assertEqual(detected.authenticated, authenticated)
                self.assertEqual(
                    detected.sandbox_access_required,
                    escalation_required,
                )

    def test_detect_capabilities_rejects_alternate_provider_routing(self):
        with tempfile.TemporaryDirectory() as temporary:
            fake_claude = write_capability_probe(Path(temporary))
            with (
                patch.object(wdyt.shutil, "which", return_value=str(fake_claude)),
                patch.dict(
                    os.environ,
                    {"WDYT_FAKE_MODE": "ok", "ANTHROPIC_BASE_URL": "https://proxy"},
                    clear=True,
                ),
            ):
                detected = wdyt.detect_capabilities()
        self.assertFalse(detected.ready)
        self.assertEqual(
            detected.unsupported_provider_routing,
            ("ANTHROPIC_BASE_URL",),
        )

        with (
            patch.object(wdyt, "detect_capabilities", return_value=detected),
            patch.object(wdyt.subprocess, "Popen") as popen,
            self.assertRaisesRegex(
                wdyt.WdytError, "requires direct Anthropic first-party routing"
            ) as raised,
        ):
            wdyt.execute_request(
                wdyt.validate_request({"repository": "off"}),
                "Give an independent view.",
            )
        popen.assert_not_called()
        self.assertEqual(
            raised.exception.category,
            "unsupported_provider_configuration",
        )

    def test_parse_events_rejects_malformed_or_incomplete_streams(self):
        cases = (
            ("{", "malformed JSONL"),
            ("[]", "non-object event"),
            (json.dumps({"type": "system", "subtype": "init"}), "omitted required"),
            (json.dumps({"type": "result"}), "omitted required"),
        )
        for stdout, message in cases:
            with self.subTest(stdout=stdout), self.assertRaisesRegex(
                wdyt.WdytError, message
            ):
                wdyt.parse_events(stdout)

    def test_failure_classifier_covers_each_public_category(self):
        cases = (
            ("not logged in", "authentication_failure"),
            ("Fable 5 requires usage credits", "usage_credits_required"),
            ("usage limit reached", "rate_limit"),
            ("requested model is unavailable", "model_unavailable"),
            ("JSON schema validation failed", "structured_output_failure"),
            ("provider connection failed", "provider_failure"),
            ("unrecognized failure", "claude_invocation_failure"),
        )
        for private_text, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(
                    wdyt.classify_invocation_failure(private_text),
                    expected,
                )

    def test_execute_request_terminates_a_timed_out_process_group(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_claude = root / "claude"
            fake_claude.write_text(
                f"""#!{sys.executable}
import time
time.sleep(30)
"""
            )
            fake_claude.chmod(0o755)
            available = wdyt.Capabilities(
                binary=str(fake_claude),
                version="Claude Code fake 1.0",
                missing_flags=(),
                supported_optional_flags=(),
                official_signal=True,
                authenticated=True,
                auth_method="oauth",
                api_provider="firstParty",
            )
            with (
                patch.object(wdyt, "detect_capabilities", return_value=available),
                self.assertRaisesRegex(wdyt.WdytError, "timed out"),
            ):
                wdyt.execute_request(
                    wdyt.validate_request({"repository": "off"}),
                    "Give an independent view.",
                    timeout=0.05,
                )

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
if sys.argv[1:] == ["auth", "status", "--json"]:
    print(json.dumps({{
        "loggedIn": True,
        "authMethod": "oauth",
        "apiProvider": "firstParty",
    }}))
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
            environment.pop("CODEX_SANDBOX", None)
            environment.pop("CODEX_SANDBOX_NETWORK_DISABLED", None)
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

    def test_opus_5_and_fable_5_names_are_passed_through_unchanged(self):
        for model in ("claude-opus-5", "claude-fable-5"):
            with self.subTest(model=model), tempfile.TemporaryDirectory() as temporary:
                request = wdyt.validate_request(
                    {"model": model, "repository": "off"}
                )
                root = Path(temporary)
                settings, mcp = wdyt.write_private_inputs(root, None)
                args = wdyt.build_claude_args(
                    capabilities(), request, None, settings, mcp
                )
            model_index = args.index("--model")
            self.assertEqual(args[model_index + 1], model)
            self.assertNotIn("--fallback-model", args)

    def test_prompt_keeps_generated_fields_below_runtime_caps(self):
        prompt = wdyt.trusted_system_prompt("review", "deep")
        self.assertIn("Target at most 450 characters for verdict", prompt)
        self.assertIn("These conservative targets apply even in deep mode", prompt)

        schema = wdyt.schema_for_claude(wdyt.load_schema())
        verdict_description = schema["properties"]["verdict"]["description"]
        self.assertTrue(verdict_description.startswith("Hard constraints:"))
        self.assertIn("maximum 600 characters.", verdict_description)

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
            "structured output failure",
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
        self.assertEqual(
            raised.exception.category,
            "structured_output_failure",
        )
        self.assertEqual(
            raised.exception.diagnostics["errorCount"],
            1,
        )

    def test_logged_out_cli_is_not_ready_and_stops_before_inference(self):
        logged_out = capabilities()
        logged_out = wdyt.Capabilities(
            binary=logged_out.binary,
            version=logged_out.version,
            missing_flags=logged_out.missing_flags,
            supported_optional_flags=logged_out.supported_optional_flags,
            official_signal=logged_out.official_signal,
            authenticated=False,
            auth_method="none",
            api_provider="firstParty",
        )
        with (
            patch.object(wdyt, "detect_capabilities", return_value=logged_out),
            patch.object(wdyt.subprocess, "Popen") as popen,
            self.assertRaisesRegex(wdyt.WdytError, "not authenticated") as raised,
        ):
            wdyt.execute_request(
                wdyt.validate_request({"repository": "off"}),
                "Give an independent view.",
            )
        popen.assert_not_called()
        self.assertEqual(raised.exception.category, "authentication_required")

    def test_sandboxed_auth_miss_requests_scoped_escalation(self):
        sandboxed = capabilities()
        sandboxed = wdyt.Capabilities(
            binary=sandboxed.binary,
            version=sandboxed.version,
            missing_flags=sandboxed.missing_flags,
            supported_optional_flags=sandboxed.supported_optional_flags,
            official_signal=sandboxed.official_signal,
            authenticated=False,
            auth_method="none",
            api_provider="firstParty",
            sandbox_access_required=True,
        )
        with (
            patch.object(wdyt, "detect_capabilities", return_value=sandboxed),
            patch.object(wdyt.subprocess, "Popen") as popen,
            self.assertRaisesRegex(
                wdyt.WdytError, "scoped sandbox escalation"
            ) as raised,
        ):
            wdyt.execute_request(
                wdyt.validate_request({"repository": "off"}),
                "Give an independent view.",
            )
        popen.assert_not_called()
        self.assertEqual(
            raised.exception.category,
            "sandbox_access_required",
        )

    def test_failure_diagnostics_are_printed_on_failure(self):
        failure = wdyt.WdytError(
            "provider failed",
            category="provider_failure",
            diagnostics={
                "status": "failed",
                "failureCategory": "provider_failure",
                "exitCode": 1,
            },
        )
        stderr = io.StringIO()
        with (
            patch.object(wdyt, "read_stdin_prompt", return_value="Review it."),
            patch.object(wdyt, "execute_request", side_effect=failure),
            patch("sys.stderr", stderr),
        ):
            status = wdyt.main(
                ["run", "--repository", "off", "--diagnostics"]
            )
        self.assertEqual(status, 1)
        lines = stderr.getvalue().splitlines()
        self.assertEqual(
            json.loads(lines[0]),
            {
                "exitCode": 1,
                "failureCategory": "provider_failure",
                "status": "failed",
            },
        )
        self.assertEqual(lines[1], "WDYT failed: provider failed")

    def test_observed_contradictory_result_remains_diagnostic(self):
        stdout = json.dumps(
            {
                "type": "result",
                "subtype": "success",
                "is_error": True,
            }
        )
        with self.assertRaises(wdyt.WdytError) as raised:
            wdyt.validate_turn(
                wdyt.validate_request({"repository": "off"}),
                capabilities(),
                None,
                1,
                stdout,
                "",
            )
        self.assertEqual(
            raised.exception.category,
            "claude_invocation_failure",
        )
        self.assertEqual(
            raised.exception.diagnostics,
            {
                "status": "failed",
                "failureCategory": "claude_invocation_failure",
                "exitCode": 1,
                "stderrPresent": False,
                "resultEventPresent": True,
                "resultSubtype": "success",
                "isError": True,
                "errorCount": 0,
                "apiErrorStatus": None,
                "terminalReason": None,
            },
        )

    def test_fable_credit_failure_is_actionable_without_leaking_provider_text(self):
        private_message = (
            "Fable 5 requires usage credits. Run /usage-credits to continue."
        )
        diagnostics = wdyt.invocation_failure_diagnostics(
            1,
            json.dumps(
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": True,
                    "terminal_reason": "api_error",
                    "api_error_status": 429,
                    "result": private_message,
                }
            ),
            "",
        )
        self.assertEqual(
            diagnostics["failureCategory"],
            "usage_credits_required",
        )
        self.assertEqual(diagnostics["apiErrorStatus"], 429)
        self.assertEqual(diagnostics["terminalReason"], "api_error")
        self.assertNotIn(private_message, json.dumps(diagnostics))

    def test_failure_classifier_uses_private_text_without_emitting_it(self):
        private_message = "Not logged in. Please run /login for account@example.com"
        diagnostics = wdyt.invocation_failure_diagnostics(
            1,
            json.dumps(
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": True,
                    "result": private_message,
                }
            ),
            "",
        )
        self.assertEqual(
            diagnostics["failureCategory"],
            "authentication_failure",
        )
        self.assertNotIn(private_message, json.dumps(diagnostics))
        self.assertNotIn("account@example.com", json.dumps(diagnostics))

    def test_failure_diagnostics_tolerate_non_string_result(self):
        diagnostics = wdyt.invocation_failure_diagnostics(
            1,
            json.dumps(
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": True,
                    "result": {"unexpected": "shape"},
                }
            ),
            "",
        )
        self.assertEqual(
            diagnostics["failureCategory"],
            "claude_invocation_failure",
        )

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
