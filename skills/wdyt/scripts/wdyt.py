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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SKILL_ROOT / "assets" / "wdyt-answer-2.schema.json"
PROMPT_PATH = SKILL_ROOT / "assets" / "wdyt-adviser-3.txt"
MAX_REQUEST_BYTES = 1_000_000
RUN_TIMEOUT_SECONDS = 300

MODES = {"advise", "challenge", "review", "decide", "diagnose"}
DEPTH_TO_EFFORT = {"quick": "low", "standard": "medium", "deep": "high"}
LIFECYCLES = {"fresh", "ephemeral"}
REPOSITORY_MODES = {"read", "off"}
CONTEXT_MODES = {"state", "blind", "thread"}
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
CONTEXT_FIELDS = {
    "artifacts",
    "constraints",
    "contextMode",
    "conversationSummary",
    "currentProposal",
    "decisions",
    "exclusions",
    "objective",
    "omissions",
    "openQuestions",
    "question",
    "recentTurns",
    "sourceTaskId",
    "truncations",
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
    """A user-visible WDYT failure."""


@dataclass(frozen=True)
class Capabilities:
    binary: str
    version: str
    missing_flags: tuple[str, ...]
    supported_optional_flags: tuple[str, ...]
    official_signal: bool

    @property
    def ready(self) -> bool:
        return self.official_signal and not self.missing_flags


@dataclass(frozen=True)
class Request:
    model: str | None
    mode: str
    depth: str
    repository: str
    lifecycle: str
    context: dict[str, Any]


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
    return Capabilities(
        binary=binary,
        version=version,
        missing_flags=missing,
        supported_optional_flags=supported_optional,
        official_signal=official_signal,
    )


def read_stdin_request(stream: Any = sys.stdin) -> dict[str, Any]:
    raw = stream.buffer.read(MAX_REQUEST_BYTES + 1) if hasattr(stream, "buffer") else stream.read(MAX_REQUEST_BYTES + 1)
    if isinstance(raw, str):
        encoded = raw.encode("utf-8")
        text = raw
    else:
        encoded = raw
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise WdytError("request input must be UTF-8 JSON") from error
    if len(encoded) > MAX_REQUEST_BYTES:
        raise WdytError(f"request exceeds {MAX_REQUEST_BYTES} bytes")
    if not text.strip():
        raise WdytError("run requires one JSON request on stdin")
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise WdytError(f"request is not valid JSON: {error}") from error
    if not isinstance(value, dict):
        raise WdytError("request must be a JSON object")
    return value


def validate_request(value: dict[str, Any]) -> Request:
    allowed = {"context", "depth", "lifecycle", "mode", "model", "repository"}
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

    context = value.get("context", {})
    if not isinstance(context, dict):
        raise WdytError("context must be a JSON object")
    unknown_context = sorted(set(context) - CONTEXT_FIELDS)
    if unknown_context:
        raise WdytError(f"unknown context fields: {', '.join(unknown_context)}")
    context_mode = context.get("contextMode", "state")
    if context_mode not in CONTEXT_MODES:
        raise WdytError(f"unsupported context mode: {context_mode!r}")

    return Request(
        model=model,
        mode=mode,
        depth=depth,
        repository=repository,
        lifecycle=lifecycle,
        context=context,
    )


def _git_value(repository: Path, args: list[str]) -> str | None:
    try:
        result = run_command(["git", "-C", str(repository), *args], timeout=10)
    except WdytError:
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def build_context_envelope(request: Request, repository: Path | None) -> dict[str, Any]:
    context = request.context
    source: dict[str, Any] = {
        "host": "codex",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
    if isinstance(context.get("sourceTaskId"), str):
        source["sourceTaskId"] = context["sourceTaskId"]
    if repository is not None:
        source.update(
            {
                "repository": repository.name,
                "cwd": ".",
            }
        )
        branch = _git_value(repository, ["branch", "--show-current"])
        revision = _git_value(repository, ["rev-parse", "HEAD"])
        if branch:
            source["branch"] = branch
        if revision:
            source["revision"] = revision

    envelope: dict[str, Any] = {
        "protocolVersion": "wdyt-context/3",
        "request": {
            "mode": request.mode,
            "depth": request.depth,
            "answerProtocol": "wdyt-answer/2",
        },
        "source": source,
        "disclosure": {
            "recipient": {"organization": "Anthropic", "product": "Claude Code"},
            "conversation": context.get("contextMode", "state"),
            "repository": (
                "model-directed-selective-read"
                if repository is not None
                else "off"
            ),
            "artifacts": "auto" if context.get("artifacts") else "none",
            "omissions": context.get("omissions", []),
            "truncations": context.get("truncations", []),
        },
        "constraints": context.get("constraints", []),
        "decisions": context.get("decisions", []),
        "openQuestions": context.get("openQuestions", []),
        "recentTurns": context.get("recentTurns", []),
        "artifacts": context.get("artifacts", []),
        "exclusions": context.get("exclusions", []),
    }
    for key in ("objective", "currentProposal", "conversationSummary"):
        if key in context:
            envelope[key] = context[key]
    question = context.get("question")
    if isinstance(question, str) and question.strip():
        envelope["request"]["question"] = question
    if repository is not None:
        envelope["repositoryAccess"] = {
            "scope": "entire-repository",
            "view": "live-read-only",
            "logicalRoot": "/repo",
            "toolRoot": ".",
        }
    return envelope


def load_schema() -> dict[str, Any]:
    try:
        schema = json.loads(SCHEMA_PATH.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise WdytError(f"could not load bundled answer schema: {error}") from error
    if schema.get("$id") != "wdyt-answer/2":
        raise WdytError("bundled answer schema has the wrong protocol ID")
    return schema


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
    schema = load_schema()
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
        "Assess the wdyt-context/3 JSON supplied on stdin and return exactly "
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
        detail = stderr.strip().splitlines()[-1] if stderr.strip() else "no detail"
        raise WdytError(f"Claude invocation failed with exit {returncode}: {detail[:500]}")
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
    context_mode = turn.request.context.get("contextMode", "state")
    lines = [
        (
            f"WDYT · Claude Code · {turn.used_model} · {turn.request.mode} · "
            f"{turn.request.lifecycle}"
        ),
        f"Context: {context_mode} · repo {repository_label}",
        (
            "Disclosure: Anthropic via Claude Code · task context + "
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

    repository = None
    if request.repository == "read":
        repository = (cwd or Path.cwd()).resolve()
        if not repository.is_dir():
            raise WdytError("repository mode requires an existing working directory")

    envelope = build_context_envelope(request, repository)
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
            stdout, stderr = process.communicate(
                json.dumps(envelope, separators=(",", ":")), timeout=timeout
            )
        except subprocess.TimeoutExpired as error:
            os.killpg(process.pid, signal.SIGTERM)
            process.communicate()
            raise WdytError(f"Claude invocation timed out after {timeout} seconds") from error
        except KeyboardInterrupt:
            os.killpg(process.pid, signal.SIGTERM)
            process.communicate()
            raise WdytError("Claude invocation was cancelled") from None
    return validate_turn(
        request,
        capabilities,
        repository,
        process.returncode,
        stdout,
        stderr,
    )


def diagnostic_report() -> dict[str, Any]:
    schema_ok = False
    prompt_ok = False
    try:
        schema_ok = load_schema().get("$id") == "wdyt-answer/2"
    except WdytError:
        pass
    try:
        prompt_ok = "wdyt-context/3" in trusted_system_prompt("advise", "standard")
    except WdytError:
        pass
    try:
        capabilities = detect_capabilities()
        return {
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
        }
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
        "run", help="read one WDYT request as JSON from stdin"
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
        request = validate_request(read_stdin_request())
        turn = execute_request(request)
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
        print(f"WDYT failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
