#!/usr/bin/env python3
"""Lean Claude Code runtime for the WDYT skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SKILL_ROOT / "assets" / "wdyt-answer-2.schema.json"
PROMPT_PATH = SKILL_ROOT / "assets" / "wdyt-adviser-3.txt"
MAX_PROMPT_BYTES = 768
MAX_PROMPT_INPUT_BYTES = MAX_PROMPT_BYTES * 8
RUN_TIMEOUT_SECONDS = 300

MODES = {"advise", "challenge", "review", "decide", "diagnose"}
DEPTH_TO_EFFORT = {"quick": "low", "standard": "medium", "deep": "high"}
LIFECYCLES = {"fresh", "ephemeral"}
REPOSITORY_MODES = {"read", "off"}
REQUIRED_FLAGS = {
    "--disable-slash-commands",
    "--json-schema",
    "--mcp-config",
    "--no-chrome",
    "--no-session-persistence",
    "--output-format",
    "--permission-mode",
    "--safe-mode",
    "--setting-sources",
    "--settings",
    "--strict-mcp-config",
    "--system-prompt",
    "--tools",
    "--verbose",
}
OPTIONAL_FLAGS = {
    "--effort",
    "--include-partial-messages",
    "--model",
    "--prompt-suggestions",
}
UNSUPPORTED_PROVIDER_ENV = (
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_USE_VERTEX",
)
CLAUDE_SCHEMA_UNSUPPORTED_CONSTRAINTS = {
    "maxItems",
    "maxLength",
    "minItems",
    "minLength",
}
MODE_MODULES = {
    "advise": (
        "Recommend the best course from the current evidence. Explain why it "
        "dominates the live alternatives, name the main way it could be wrong, "
        "and give the next reversible move."
    ),
    "challenge": (
        "Develop the strongest realistic case that the current proposal or "
        "consensus is wrong. Identify the load-bearing assumption, the failure "
        "it would cause, and the smallest test that would meaningfully update "
        "confidence. Do not invent objections or reject a sound proposal merely "
        "to appear independent."
    ),
    "review": (
        "Evaluate the specified proposal or artifact against its stated "
        "objective, constraints, and acceptance criteria. Return a clear "
        "approve, revise, or block judgment. Prioritize defects that change "
        "correctness, safety, operability, or decision quality."
    ),
    "decide": (
        "Compare the explicit alternatives using the few tradeoffs that actually "
        "decide the outcome. State the decision rule, identify any dominated "
        "option, choose when the evidence supports choosing, and say what "
        "missing fact would change the choice."
    ),
    "diagnose": (
        "Rank the plausible explanations for the observed problem. Tie each "
        "leading hypothesis to evidence for and against it, then recommend the "
        "smallest discriminating check. Diagnose only; do not implement a fix."
    ),
}
DEPTH_MODULES = {
    "quick": (
        "Inspect only the highest-value evidence; return one or two rationale "
        "points and one main risk."
    ),
    "standard": (
        "Inspect enough evidence to test the recommendation; return up to three "
        "rationale points and the material risks and unknowns."
    ),
    "deep": (
        "Test competing explanations and hidden coupling more thoroughly; "
        "return up to five rationale points without exhaustive traversal."
    ),
}


class WdytError(RuntimeError):
    """A user-visible WDYT failure with optional sanitized diagnostics."""

    def __init__(
        self,
        message: str,
        *,
        category: str = "runtime_failure",
        diagnostics: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.diagnostics = diagnostics or {}


@dataclass(frozen=True)
class Capabilities:
    binary: str
    version: str
    missing_flags: tuple[str, ...]
    supported_optional_flags: tuple[str, ...]
    official_signal: bool
    authenticated: bool = True
    auth_method: str | None = None
    api_provider: str | None = None
    sandbox_access_required: bool = False
    unsupported_provider_routing: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return (
            self.official_signal
            and not self.missing_flags
            and self.authenticated
            and not self.sandbox_access_required
            and not self.unsupported_provider_routing
        )


@dataclass(frozen=True)
class Request:
    model: str | None
    mode: str
    depth: str
    repository: str
    lifecycle: str


@dataclass
class Turn:
    request: Request
    version: str
    used_model: str
    answer: dict[str, Any]
    tools: list[str]
    tool_calls: list[dict[str, Any]]
    usage: dict[str, Any]
    model_usage: dict[str, Any]
    cost_usd: float | None


def run_command(
    args: list[str], *, timeout: int = 30, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            text=True,
            capture_output=True,
            timeout=timeout,
            cwd=cwd,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise WdytError(f"could not run {args[0]!r}: {error}") from error


def detect_capabilities() -> Capabilities:
    binary = shutil.which("claude")
    if binary is None:
        raise WdytError(
            "official Claude Code was not found on PATH; install and authenticate "
            "it, then retry"
        )
    version_result = run_command([binary, "--version"])
    version = (version_result.stdout or version_result.stderr).strip()
    if version_result.returncode != 0 or not version:
        raise WdytError("Claude Code did not return a usable version")
    help_result = run_command([binary, "-p", "--help"])
    help_text = f"{help_result.stdout}\n{help_result.stderr}"
    if help_result.returncode != 0:
        raise WdytError("Claude Code print-mode help failed")
    missing = tuple(sorted(flag for flag in REQUIRED_FLAGS if flag not in help_text))
    supported_optional = tuple(
        sorted(flag for flag in OPTIONAL_FLAGS if flag in help_text)
    )
    official_signal = "Claude Code" in f"{version}\n{help_text}"
    auth_result = run_command([binary, "auth", "status", "--json"])
    try:
        auth_status = json.loads(auth_result.stdout)
    except json.JSONDecodeError as error:
        raise WdytError(
            "Claude Code returned malformed authentication status",
            category="authentication_status_unavailable",
        ) from error
    if not isinstance(auth_status, dict) or not isinstance(
        auth_status.get("loggedIn"), bool
    ):
        raise WdytError(
            "Claude Code returned incomplete authentication status",
            category="authentication_status_unavailable",
        )
    auth_method = auth_status.get("authMethod")
    api_provider = auth_status.get("apiProvider")
    network_blocked = os.environ.get("CODEX_SANDBOX_NETWORK_DISABLED") == "1"
    sandboxed = bool(os.environ.get("CODEX_SANDBOX"))
    sandbox_access_required = sandboxed and (
        network_blocked or not auth_status["loggedIn"]
    )
    unsupported_provider_routing = tuple(
        name for name in UNSUPPORTED_PROVIDER_ENV if os.environ.get(name)
    )
    if isinstance(api_provider, str) and api_provider != "firstParty":
        unsupported_provider_routing += ("Claude Code apiProvider",)
    return Capabilities(
        binary=binary,
        version=version,
        missing_flags=missing,
        supported_optional_flags=supported_optional,
        official_signal=official_signal,
        authenticated=auth_status["loggedIn"],
        auth_method=auth_method if isinstance(auth_method, str) else None,
        api_provider=api_provider if isinstance(api_provider, str) else None,
        sandbox_access_required=sandbox_access_required,
        unsupported_provider_routing=unsupported_provider_routing,
    )


def read_stdin_prompt(stream: Any = sys.stdin) -> str:
    reader = stream.buffer if hasattr(stream, "buffer") else stream
    raw = reader.readline(MAX_PROMPT_BYTES + 2)
    try:
        non_interactive = reader.isatty() is False
    except (AttributeError, OSError, ValueError):
        non_interactive = False
    if non_interactive and len(raw) <= MAX_PROMPT_INPUT_BYTES:
        raw += reader.read(MAX_PROMPT_INPUT_BYTES + 1 - len(raw))
    if isinstance(raw, str):
        text = raw
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise WdytError("task prompt must be UTF-8") from error
    if len(text.encode("utf-8")) > MAX_PROMPT_INPUT_BYTES:
        raise WdytError("task prompt input is too large to normalize")
    text = " ".join(text.split())
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_PROMPT_BYTES:
        raise WdytError(
            f"task prompt exceeds {MAX_PROMPT_BYTES} bytes after normalization; "
            "summarize it to one short question"
        )
    if not text:
        raise WdytError("run requires one short task prompt on stdin")
    return text


def validate_request(value: dict[str, Any]) -> Request:
    allowed = {"depth", "lifecycle", "mode", "model", "repository"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise WdytError(f"unknown request fields: {', '.join(unknown)}")

    model_value = value.get("model")
    if model_value in (None, "", "auto"):
        model = None
    elif not isinstance(model_value, str):
        raise WdytError("model must be a string, null, or omitted")
    else:
        model = model_value.strip()
        if not model or len(model) > 256 or "\x00" in model:
            raise WdytError("explicit model must be 1–256 non-NUL characters")

    mode = value.get("mode", "advise")
    if mode == "consult":
        mode = "advise"
    if mode not in MODES:
        raise WdytError(f"unsupported mode: {mode!r}")

    depth = value.get("depth", "standard")
    if depth not in DEPTH_TO_EFFORT:
        raise WdytError(f"unsupported depth: {depth!r}")

    repository = value.get("repository", "read")
    if repository == "no-repo":
        repository = "off"
    if repository not in REPOSITORY_MODES:
        raise WdytError(f"unsupported repository mode: {repository!r}")

    lifecycle = value.get("lifecycle", "fresh")
    if lifecycle not in LIFECYCLES:
        raise WdytError(
            "only fresh and ephemeral turns are supported; continuation and "
            "named sessions are not implemented"
        )

    return Request(
        model=model,
        mode=mode,
        depth=depth,
        repository=repository,
        lifecycle=lifecycle,
    )


def load_schema() -> dict[str, Any]:
    try:
        schema = json.loads(SCHEMA_PATH.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise WdytError(f"could not load bundled answer schema: {error}") from error
    if schema.get("$id") != "wdyt-answer/2":
        raise WdytError("bundled answer schema has the wrong protocol ID")
    return schema


def schema_for_claude(value: Any) -> Any:
    if isinstance(value, dict):
        transformed = {
            key: schema_for_claude(item)
            for key, item in value.items()
            if key not in CLAUDE_SCHEMA_UNSUPPORTED_CONSTRAINTS
        }
        constraints: list[str] = []
        if isinstance(value.get("minLength"), int):
            constraints.append(f"minimum {value['minLength']} characters")
        if isinstance(value.get("maxLength"), int):
            constraints.append(f"maximum {value['maxLength']} characters")
        if isinstance(value.get("minItems"), int):
            constraints.append(f"minimum {value['minItems']} items")
        if isinstance(value.get("maxItems"), int):
            constraints.append(f"maximum {value['maxItems']} items")
        if constraints:
            note = "Hard constraints: " + "; ".join(constraints) + "."
            existing = transformed.get("description")
            transformed["description"] = (
                f"{existing.rstrip()} {note}" if isinstance(existing, str) else note
            )
        return transformed
    if isinstance(value, list):
        return [schema_for_claude(item) for item in value]
    return value


def trusted_system_prompt(mode: str, depth: str) -> str:
    try:
        core = PROMPT_PATH.read_text().rstrip()
    except OSError as error:
        raise WdytError(f"could not load bundled adviser prompt: {error}") from error
    return (
        f"{core}\n\nMODE\n{MODE_MODULES[mode]}\n\n"
        f"DEPTH\n{DEPTH_MODULES[depth]}"
    )


def write_private_inputs(
    directory: Path, repository: Path | None
) -> tuple[Path, Path]:
    mcp_path = directory / "mcp.json"
    mcp_path.write_text(json.dumps({"mcpServers": {}}))
    mcp_path.chmod(0o600)

    allow: list[str] = []
    if repository is not None:
        canonical = str(repository)
        allow = [
            f"Read({canonical}/**)",
            f"Glob({canonical}/**)",
            f"Grep({canonical}/**)",
        ]
    settings = {
        "permissions": {
            "defaultMode": "dontAsk",
            "allow": allow,
            "deny": [
                "Bash",
                "Edit",
                "Write",
                "NotebookEdit",
                "WebFetch",
                "WebSearch",
                "Agent",
                "Task",
                "SendMessage",
            ],
        },
        "disableAllHooks": True,
        "disableBypassPermissionsMode": "disable",
        "disableAutoMode": "disable",
    }
    settings_path = directory / "settings.json"
    settings_path.write_text(json.dumps(settings))
    settings_path.chmod(0o600)
    return settings_path, mcp_path


def build_claude_args(
    capabilities: Capabilities,
    request: Request,
    repository: Path | None,
    settings_path: Path,
    mcp_path: Path,
) -> list[str]:
    schema = schema_for_claude(load_schema())
    args = [
        capabilities.binary,
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--system-prompt",
        trusted_system_prompt(request.mode, request.depth),
        "--json-schema",
        json.dumps(schema, separators=(",", ":")),
        "--safe-mode",
        "--disable-slash-commands",
        "--strict-mcp-config",
        "--mcp-config",
        str(mcp_path),
        "--no-chrome",
        "--no-session-persistence",
        "--permission-mode",
        "dontAsk",
        "--settings",
        str(settings_path),
        "--setting-sources",
        "",
        "--tools",
        "Read,Glob,Grep" if repository is not None else "",
    ]
    optional = set(capabilities.supported_optional_flags)
    if "--include-partial-messages" in optional:
        args.append("--include-partial-messages")
    if "--prompt-suggestions" in optional:
        args.extend(["--prompt-suggestions", "false"])
    if request.model is not None:
        if "--model" not in optional:
            raise WdytError(
                "installed Claude Code cannot accept an explicit model name"
            )
        args.extend(["--model", request.model])
    if "--effort" in optional:
        args.extend(["--effort", DEPTH_TO_EFFORT[request.depth]])
    args.append(
        "Use the short task supplied on stdin. When repository tools are "
        "available, inspect only the relevant files yourself. Return exactly "
        "the required wdyt-answer/2 object."
    )
    return args


def parse_events(stdout: str) -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[str],
    list[dict[str, Any]],
]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise WdytError(
                f"Claude emitted malformed JSONL on line {line_number}"
            ) from error
        if not isinstance(event, dict):
            raise WdytError(f"Claude emitted a non-object event on line {line_number}")
        events.append(event)
    init = next(
        (
            event
            for event in events
            if event.get("type") == "system" and event.get("subtype") == "init"
        ),
        None,
    )
    result = next(
        (event for event in reversed(events) if event.get("type") == "result"),
        None,
    )
    if init is None or result is None:
        raise WdytError("Claude output omitted required init or result events")

    assistant_models: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    for event in events:
        if event.get("type") != "assistant":
            continue
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        model = message.get("model")
        if isinstance(model, str):
            assistant_models.append(model)
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tool_calls.append(
                    {
                        "name": block.get("name"),
                        "input": block.get("input", {}),
                    }
                )
    return init, result, assistant_models, tool_calls


def _require_string(value: Any, name: str, *, minimum: int = 0, maximum: int) -> str:
    if not isinstance(value, str):
        raise WdytError(f"answer field {name} must be a string")
    if len(value) < minimum or len(value) > maximum:
        raise WdytError(
            f"answer field {name} must contain {minimum}–{maximum} characters"
        )
    return value


def _require_string_list(
    value: Any, name: str, *, maximum_items: int, maximum_length: int
) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum_items:
        raise WdytError(f"answer field {name} must be a list of at most {maximum_items}")
    return [
        _require_string(item, f"{name}[{index}]", maximum=maximum_length)
        for index, item in enumerate(value)
    ]


def validate_answer(answer: Any) -> dict[str, Any]:
    if not isinstance(answer, dict):
        raise WdytError("Claude result did not contain a structured answer object")
    required = {
        "protocolVersion",
        "verdict",
        "confidence",
        "rationale",
        "risks",
        "unknowns",
        "nextStep",
        "decisionPrompt",
    }
    if set(answer) != required:
        missing = sorted(required - set(answer))
        extra = sorted(set(answer) - required)
        raise WdytError(f"answer fields disagree with schema; missing={missing}, extra={extra}")
    if answer["protocolVersion"] != "wdyt-answer/2":
        raise WdytError("Claude returned an unsupported answer protocol")
    _require_string(answer["verdict"], "verdict", minimum=1, maximum=600)
    if answer["confidence"] not in {"low", "medium", "high"}:
        raise WdytError("answer confidence must be low, medium, or high")
    rationale = answer["rationale"]
    if not isinstance(rationale, list) or not 1 <= len(rationale) <= 5:
        raise WdytError("answer rationale must contain 1–5 points")
    for point_index, point in enumerate(rationale):
        if not isinstance(point, dict) or set(point) != {"point", "evidence"}:
            raise WdytError(f"rationale[{point_index}] has invalid fields")
        _require_string(
            point["point"], f"rationale[{point_index}].point", minimum=1, maximum=500
        )
        evidence = point["evidence"]
        if not isinstance(evidence, list) or len(evidence) > 5:
            raise WdytError(
                f"rationale[{point_index}].evidence must contain at most 5 items"
            )
        for evidence_index, item in enumerate(evidence):
            if not isinstance(item, dict) or set(item) != {"kind", "ref"}:
                raise WdytError(
                    f"rationale[{point_index}].evidence[{evidence_index}] "
                    "has invalid fields"
                )
            kind = item["kind"]
            reference = item["ref"]
            if kind not in {"context", "repository", "inference"}:
                raise WdytError("answer evidence kind is unsupported")
            if kind == "inference":
                if reference is not None:
                    raise WdytError("inference evidence must use a null ref")
            else:
                _require_string(
                    reference,
                    f"rationale[{point_index}].evidence[{evidence_index}].ref",
                    minimum=1,
                    maximum=300,
                )
    _require_string_list(answer["risks"], "risks", maximum_items=4, maximum_length=400)
    _require_string_list(
        answer["unknowns"], "unknowns", maximum_items=4, maximum_length=400
    )
    _require_string(answer["nextStep"], "nextStep", minimum=1, maximum=500)
    decision_prompt = answer["decisionPrompt"]
    if decision_prompt is not None:
        _require_string(decision_prompt, "decisionPrompt", maximum=400)
    return answer


def _path_is_within(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _static_pattern_prefix(value: str) -> str:
    wildcard = re.search(r"[*?\\[]", value)
    prefix = value[: wildcard.start()] if wildcard else value
    return prefix or "."


def validate_tool_paths(
    tool_calls: Iterable[dict[str, Any]], repository: Path | None
) -> None:
    for call in tool_calls:
        name = call.get("name")
        payload = call.get("input")
        if name == "StructuredOutput":
            continue
        if repository is None:
            raise WdytError(f"repository tool {name!r} was called in no-repo mode")
        if name not in {"Read", "Glob", "Grep"}:
            raise WdytError(f"unexpected tool call: {name!r}")
        if not isinstance(payload, dict):
            raise WdytError(f"{name} emitted a non-object input")

        path_values: list[str] = []
        for key in ("file_path", "path"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                path_values.append(value)
        for key in ("pattern", "glob"):
            value = payload.get(key)
            if not isinstance(value, str):
                continue
            if key == "pattern" and name == "Grep":
                # Grep.pattern is a regular expression, not a filesystem path.
                continue
            if Path(value).is_absolute() or ".." in Path(value).parts:
                raise WdytError(f"{name} used an escaping pattern: {value!r}")
            if key == "pattern" and name == "Glob":
                path_values.append(_static_pattern_prefix(value))

        for value in path_values or ["."]:
            candidate = Path(value)
            if not candidate.is_absolute():
                candidate = repository / candidate
            resolved = candidate.resolve(strict=False)
            if not _path_is_within(resolved, repository):
                raise WdytError(f"{name} attempted an out-of-root path: {value!r}")


def validate_turn(
    request: Request,
    capabilities: Capabilities,
    repository: Path | None,
    returncode: int,
    stdout: str,
    stderr: str,
) -> Turn:
    if returncode != 0:
        diagnostics = invocation_failure_diagnostics(returncode, stdout, stderr)
        detail = invocation_failure_detail(diagnostics)
        raise WdytError(
            f"Claude invocation failed with exit {returncode}: {detail}",
            category=str(diagnostics["failureCategory"]),
            diagnostics=diagnostics,
        )
    init, result, assistant_models, tool_calls = parse_events(stdout)
    used_model = init.get("model")
    if not isinstance(used_model, str) or not used_model:
        raise WdytError("Claude init did not identify the used model")
    if assistant_models and any(model != used_model for model in assistant_models):
        raise WdytError(
            f"assistant-model provenance disagreed with init model {used_model!r}"
        )

    expected_tools = (
        {"Read", "Glob", "Grep", "StructuredOutput"}
        if repository is not None
        else {"StructuredOutput"}
    )
    tools = init.get("tools")
    if not isinstance(tools, list) or set(tools) != expected_tools:
        raise WdytError(
            f"registered tools {tools!r} disagree with required "
            f"{sorted(expected_tools)!r}"
        )
    unexpected_calls = [
        call.get("name") for call in tool_calls if call.get("name") not in expected_tools
    ]
    if unexpected_calls:
        raise WdytError(f"unexpected model-callable tools were used: {unexpected_calls}")
    for key in ("mcp_servers", "plugins", "skills", "slash_commands"):
        if init.get(key) not in (None, [], {}):
            raise WdytError(f"unexpected Claude customization inventory: {key}")
    validate_tool_paths(tool_calls, repository)

    if result.get("is_error") is not False or result.get("subtype") != "success":
        raise WdytError(
            f"Claude result failed: subtype={result.get('subtype')!r}, "
            f"is_error={result.get('is_error')!r}"
        )
    structured = result.get("structured_output")
    if not isinstance(structured, dict) and isinstance(result.get("result"), dict):
        structured = result["result"]
    answer = validate_answer(structured)
    usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
    model_usage = (
        result.get("modelUsage") if isinstance(result.get("modelUsage"), dict) else {}
    )
    cost = result.get("total_cost_usd")
    return Turn(
        request=request,
        version=capabilities.version,
        used_model=used_model,
        answer=answer,
        tools=tools,
        tool_calls=tool_calls,
        usage=usage,
        model_usage=model_usage,
        cost_usd=float(cost) if isinstance(cost, (int, float)) else None,
    )


def classify_invocation_failure(text: str) -> str:
    lowered = text.lower()
    if any(
        marker in lowered
        for marker in (
            "not logged in",
            "please run /login",
            "authentication required",
            "unauthorized",
            "invalid api key",
        )
    ):
        return "authentication_failure"
    if "usage credits" in lowered:
        return "usage_credits_required"
    if any(marker in lowered for marker in ("rate limit", "usage limit", "quota")):
        return "rate_limit"
    if "model" in lowered and any(
        marker in lowered
        for marker in ("unavailable", "not found", "not supported", "no access")
    ):
        return "model_unavailable"
    if any(
        marker in lowered
        for marker in (
            "structured output",
            "json schema",
            "schema validation",
            "max structured output",
        )
    ):
        return "structured_output_failure"
    if any(
        marker in lowered
        for marker in ("api error", "provider", "transport", "connection")
    ):
        return "provider_failure"
    return "claude_invocation_failure"


def invocation_failure_diagnostics(
    returncode: int, stdout: str, stderr: str
) -> dict[str, Any]:
    result: dict[str, Any] | None = None
    for line in reversed(stdout.splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("type") == "result":
            result = event
            break
    errors = result.get("errors") if result is not None else None
    error_count = len(errors) if isinstance(errors, list) else 0
    result_text = result.get("result") if result is not None else None
    private_text = "\n".join(
        [
            stderr,
            result_text if isinstance(result_text, str) else "",
            *(
                item
                for item in (errors if isinstance(errors, list) else [])
                if isinstance(item, str)
            ),
        ]
    )
    subtype = result.get("subtype") if result is not None else None
    if isinstance(subtype, str) and "structured_output" in subtype:
        failure_category = "structured_output_failure"
    else:
        failure_category = classify_invocation_failure(private_text)
    api_error_status = result.get("api_error_status") if result is not None else None
    if failure_category == "claude_invocation_failure" and api_error_status == 429:
        failure_category = "rate_limit"
    terminal_reason = result.get("terminal_reason") if result is not None else None
    return {
        "status": "failed",
        "failureCategory": failure_category,
        "exitCode": returncode,
        "stderrPresent": bool(stderr.strip()),
        "resultEventPresent": result is not None,
        "resultSubtype": result.get("subtype") if result is not None else None,
        "isError": result.get("is_error") if result is not None else None,
        "errorCount": error_count,
        "apiErrorStatus": (
            api_error_status if isinstance(api_error_status, int) else None
        ),
        "terminalReason": (
            terminal_reason
            if terminal_reason in {"api_error", "error", "max_turns", "stop_sequence"}
            else None
        ),
    }


def invocation_failure_detail(diagnostics: dict[str, Any]) -> str:
    category = diagnostics["failureCategory"]
    if category != "claude_invocation_failure":
        return str(category).replace("_", " ")
    if diagnostics["resultEventPresent"]:
        return (
            f"result subtype={diagnostics['resultSubtype']!r}, "
            f"is_error={diagnostics['isError']!r}, "
            f"errors={diagnostics['errorCount']}"
        )
    return "no sanitized provider detail"


def _evidence_suffix(evidence: Any) -> str:
    if not isinstance(evidence, list):
        return ""
    references: list[str] = []
    for item in evidence:
        if isinstance(item, dict) and isinstance(item.get("ref"), str):
            references.append(item["ref"])
    return f" [{'; '.join(references)}]" if references else ""


def render_turn(turn: Turn) -> str:
    answer = turn.answer
    repository_label = "read-only" if turn.request.repository == "read" else "off"
    lines = [
        (
            f"WDYT · Claude Code · {turn.used_model} · {turn.request.mode} · "
            f"{turn.request.lifecycle}"
        ),
        f"Context: minimal · repo {repository_label}",
        (
            "Disclosure: Anthropic via Claude Code · short task + "
            f"{'repo read-only' if repository_label == 'read-only' else 'no repo'}"
        ),
    ]
    if turn.request.model is not None and turn.request.model != turn.used_model:
        lines.append(f"Model: {turn.request.model} → {turn.used_model}")
    lines.extend(["", answer["verdict"], "", "Why"])
    for index, point in enumerate(answer["rationale"], start=1):
        lines.append(
            f"{index}. {point['point']}{_evidence_suffix(point['evidence'])}"
        )
    watch = [
        *(f"Risk: {item}" for item in answer["risks"]),
        *(f"Unknown: {item}" for item in answer["unknowns"]),
    ]
    if watch:
        lines.extend(["", "Watch", *(f"• {item}" for item in watch)])
    lines.extend(["", "Next", answer["nextStep"]])
    if answer["decisionPrompt"] is not None:
        lines.extend(["", f"Your call: {answer['decisionPrompt']}"])
    lines.extend(["", f"Confidence: {answer['confidence']}"])
    return "\n".join(lines)


def execute_request(
    request: Request,
    prompt: str,
    *,
    cwd: Path | None = None,
    timeout: int = RUN_TIMEOUT_SECONDS,
) -> Turn:
    capabilities = detect_capabilities()
    if not capabilities.official_signal:
        raise WdytError(
            "the resolved claude executable does not identify itself as Claude Code"
        )
    if capabilities.missing_flags:
        raise WdytError(
            "installed Claude Code lacks required capabilities: "
            + ", ".join(capabilities.missing_flags)
        )
    if capabilities.sandbox_access_required:
        raise WdytError(
            "Claude authentication and network access are unavailable inside "
            "the current sandbox; rerun the exact WDYT command with scoped "
            "sandbox escalation",
            category="sandbox_access_required",
            diagnostics={
                "status": "failed",
                "failureCategory": "sandbox_access_required",
                "sandboxAccessRequired": True,
            },
        )
    if capabilities.unsupported_provider_routing:
        routing = ", ".join(capabilities.unsupported_provider_routing)
        raise WdytError(
            "Claude Code has alternate provider routing configured through "
            f"{routing}; WDYT requires direct Anthropic first-party routing",
            category="unsupported_provider_configuration",
            diagnostics={
                "status": "failed",
                "failureCategory": "unsupported_provider_configuration",
                "unsupportedProviderRouting": list(
                    capabilities.unsupported_provider_routing
                ),
            },
        )
    if not capabilities.authenticated:
        raise WdytError(
            "Claude Code is not authenticated; run `claude auth login`, then retry",
            category="authentication_required",
            diagnostics={
                "status": "failed",
                "failureCategory": "authentication_required",
                "authenticated": False,
                "authMethod": capabilities.auth_method,
                "apiProvider": capabilities.api_provider,
            },
        )

    repository = None
    if request.repository == "read":
        repository = (cwd or Path.cwd()).resolve()
        if not repository.is_dir():
            raise WdytError("repository mode requires an existing working directory")

    with tempfile.TemporaryDirectory(prefix="wdyt-") as temporary:
        private_directory = Path(temporary)
        private_directory.chmod(0o700)
        settings_path, mcp_path = write_private_inputs(private_directory, repository)
        args = build_claude_args(
            capabilities, request, repository, settings_path, mcp_path
        )
        process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=repository or private_directory,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            terminate_process(process)
            raise WdytError(f"Claude invocation timed out after {timeout} seconds") from error
        except KeyboardInterrupt:
            terminate_process(process)
            raise WdytError("Claude invocation was cancelled") from None
    return validate_turn(
        request,
        capabilities,
        repository,
        process.returncode,
        stdout,
        stderr,
    )


def terminate_process(process: subprocess.Popen[str]) -> None:
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()


def diagnostic_report() -> dict[str, Any]:
    schema_ok = False
    prompt_ok = False
    try:
        schema_ok = load_schema().get("$id") == "wdyt-answer/2"
    except WdytError:
        pass
    try:
        prompt = trusted_system_prompt("advise", "standard")
        prompt_ok = "short task" in prompt and "wdyt-answer/2" in prompt
    except WdytError:
        pass
    try:
        capabilities = detect_capabilities()
        report = {
            "ready": capabilities.ready and schema_ok and prompt_ok,
            "binary": capabilities.binary,
            "version": capabilities.version,
            "officialClaudeCodeSignal": capabilities.official_signal,
            "missingCapabilities": list(capabilities.missing_flags),
            "optionalCapabilities": list(capabilities.supported_optional_flags),
            "schema": "ok" if schema_ok else "invalid",
            "prompt": "ok" if prompt_ok else "invalid",
            "supportedLifecycles": ["fresh", "ephemeral"],
            "modelPolicy": "Claude default or any explicit model string",
            "authentication": (
                "unavailable_in_sandbox"
                if capabilities.sandbox_access_required
                else (
                    "authenticated"
                    if capabilities.authenticated
                    else "not_authenticated"
                )
            ),
            "authMethod": capabilities.auth_method,
            "apiProvider": capabilities.api_provider,
            "sandboxAccessRequired": capabilities.sandbox_access_required,
            "unsupportedProviderRouting": list(
                capabilities.unsupported_provider_routing
            ),
        }
        if capabilities.sandbox_access_required:
            report["error"] = (
                "Claude authentication and network access are unavailable "
                "inside the current sandbox; rerun the exact WDYT command with "
                "scoped sandbox escalation"
            )
        elif not capabilities.authenticated:
            report["error"] = (
                "Claude Code is not authenticated; run `claude auth login`, "
                "then retry"
            )
        elif capabilities.unsupported_provider_routing:
            report["error"] = (
                "Claude Code has alternate provider routing configured; "
                "WDYT requires direct Anthropic first-party routing"
            )
        return report
    except WdytError as error:
        return {
            "ready": False,
            "error": str(error),
            "schema": "ok" if schema_ok else "invalid",
            "prompt": "ok" if prompt_ok else "invalid",
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="check local Claude Code capabilities")
    run_parser = subparsers.add_parser(
        "run", help="read and normalize a short WDYT task prompt from stdin"
    )
    run_parser.add_argument("--model")
    run_parser.add_argument(
        "--mode",
        choices=sorted(MODES | {"consult"}),
        default="advise",
    )
    run_parser.add_argument(
        "--depth",
        choices=sorted(DEPTH_TO_EFFORT),
        default="standard",
    )
    run_parser.add_argument(
        "--repository",
        choices=sorted(REPOSITORY_MODES | {"no-repo"}),
        default="read",
    )
    run_parser.add_argument(
        "--lifecycle",
        choices=sorted(LIFECYCLES),
        default="fresh",
    )
    run_parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="write sanitized run metadata to stderr",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        report = diagnostic_report()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report.get("ready") else 1
    try:
        request = validate_request(
            {
                "model": args.model,
                "mode": args.mode,
                "depth": args.depth,
                "repository": args.repository,
                "lifecycle": args.lifecycle,
            }
        )
        prompt = read_stdin_prompt()
        turn = execute_request(request, prompt)
        print(render_turn(turn))
        if args.diagnostics:
            print(
                json.dumps(
                    {
                        "claudeCodeVersion": turn.version,
                        "usedModel": turn.used_model,
                        "registeredTools": turn.tools,
                        "toolCallCount": len(turn.tool_calls),
                        "usage": turn.usage,
                        "modelUsage": turn.model_usage,
                        "reportedCostUsd": turn.cost_usd,
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
        return 0
    except WdytError as error:
        if args.command == "run" and args.diagnostics:
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "failureCategory": error.category,
                        **error.diagnostics,
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
        print(f"WDYT failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
