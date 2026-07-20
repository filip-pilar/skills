#!/usr/bin/env python3
"""Validate a completed Web Traffic Inspector deliverable directory."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path


REQUIRED_FINDINGS_HEADINGS = (
    "## Observed action and outcome",
    "## Isolated mechanism",
    "## Verification evidence",
    "## Verification status and provenance",
    "## Execution mode",
    "## Run or restart",
    "## Authentication, CORS, stability, and side effects",
    "## Scraping and integration readiness",
    "## Production gaps and uncertainty",
    "## Skill friction",
)

PAGE_RUNTIME_FORBIDDEN_PATTERNS = (
    (r"\b(?:localStorage|sessionStorage|indexedDB|cookieStore)\b", "browser storage inspection"),
    (r"document\s*\.\s*cookie\b", "cookie inspection"),
    (r"navigator\s*\.\s*credentials\b", "credential inspection"),
    (r"\b(?:eval|Function)\s*\(", "arbitrary JavaScript execution"),
    (r"\b(?:fetch|XMLHttpRequest|WebSocket|EventSource)\b", "network execution inside the projection recipe"),
    (r"\b(?:window\s*\.\s*open|history\s*\.)\b", "broad navigation or history automation"),
    (r"(?:window\s*\.\s*)?location\s*(?:\.\s*href\s*)?=", "runtime navigation"),
    (r"(?:querySelector|querySelectorAll|matches|closest)\s*\(\s*inputs\b", "a user-supplied selector"),
    (r"\b(?:runAgentBrowser|spawn)\s*\(", "direct browser-process control from the projection recipe"),
    (r"\b(?:process|child_process|readFile|readFileSync)\b", "host process or filesystem access"),
    (r"\b(?:input|radio|checkbox|option)\s*\.\s*(?:offsetParent|getClientRects\s*\()", "native form-control geometry as a visibility test; inspect its fixed associated label or option container instead"),
    (r"\bdocument\s*\.\s*querySelector(?:All)?\s*\(\s*[\"'`]\s*(?:main|body)(?:[\"'`]|\s|[>.:#\[])", "broad structural page root; scope the recipe to a fixed semantic component"),
)

AUTH_MODES = {"none", "existing-session", "interactive-profile", "cdp", "runtime-headers"}

TEMPORARY_ARTIFACT_PATTERNS = (
    "spec.json",
    "probe.html",
    "*-probe.html",
    "*.har",
    "*.trace",
    "trace.zip",
)


def validate(directory: Path) -> list[str]:
    errors: list[str] = []
    demo = directory / "demo.html"
    findings = directory / "FINDINGS.md"
    for path in (demo, findings):
        if not path.is_file():
            errors.append(f"missing required file: {path.name}")
    if errors:
        return errors

    demo_text = demo.read_text(encoding="utf-8")
    findings_text = findings.read_text(encoding="utf-8")
    spec = None
    match = re.search(r"^\s*const SPEC = (\{.*\});\s*$", demo_text, re.MULTILINE)
    if not match:
        errors.append("demo.html is missing readable generated mechanism metadata")
    else:
        try:
            spec = json.loads(match.group(1))
        except json.JSONDecodeError:
            errors.append("demo.html contains invalid generated mechanism metadata")
    if "__WTI_" in demo_text or "__WTI_" in findings_text:
        errors.append("unresolved scaffold marker found")
    if "WTI-FINDINGS:" in findings_text:
        errors.append("FINDINGS.md still contains scaffold prompts")
    for heading in REQUIRED_FINDINGS_HEADINGS:
        if heading not in findings_text:
            errors.append(f"FINDINGS.md is missing heading: {heading}")
    for required in (
        'id="raw"',
        'id="raw-summary"',
        'id="copy"',
        'id="download"',
        'id="utility-status"',
        'id="verification-status"',
        'id="execution-mode"',
        'id="mechanism-kind"',
        'id="mechanism-summary"',
        'id="mechanism-stages"',
    ):
        if required not in demo_text:
            errors.append(f"demo.html is missing required interface marker: {required}")
    companion = directory / "browser-companion.mjs"
    companion_text = companion.read_text(encoding="utf-8") if companion.exists() else ""
    companion_config = None
    if companion_text:
        config_match = re.search(r"^const CONFIG = (\{.*\});$", companion_text, re.MULTILINE)
        if not config_match:
            errors.append("browser-companion.mjs is missing readable generated companion metadata")
        else:
            try:
                companion_config = json.loads(config_match.group(1))
            except json.JSONDecodeError:
                errors.append("browser-companion.mjs contains invalid generated companion metadata")
    if companion.exists() and "WTI-CUSTOMIZE: companion:start" not in companion_text:
        errors.append("browser-companion.mjs is missing its bounded customization region")
    if spec and spec.get("mode") in {"relay", "browser"}:
        public_runtime = spec.get("companion", {}).get("runtime")
        if not isinstance(public_runtime, dict) or set(public_runtime) != {"authMode"}:
            errors.append("demo.html companion runtime metadata must expose only authMode")
        elif public_runtime.get("authMode") not in AUTH_MODES:
            errors.append("demo.html contains an invalid companion authentication posture")
        if companion_config:
            runtime = companion_config.get("runtime")
            if not isinstance(runtime, dict) or runtime.get("authMode") not in AUTH_MODES:
                errors.append("browser-companion.mjs contains invalid runtime launch metadata")
            elif isinstance(public_runtime, dict) and public_runtime.get("authMode") != runtime.get("authMode"):
                errors.append("demo.html authentication posture does not match browser-companion.mjs")
            run_match = re.search(r"## Run or restart\s+```bash\s*\n([^\n]+)\n```", findings_text)
            if not run_match:
                errors.append("FINDINGS.md is missing a single-line bash restart command")
            else:
                try:
                    run_arguments = shlex.split(run_match.group(1))
                except ValueError:
                    errors.append("FINDINGS.md restart command is not valid shell syntax")
                    run_arguments = []
                auth_mode = runtime.get("authMode")
                expected_pairs = []
                expected_flags = []
                if companion_config.get("transport") == "browser":
                    expected_pairs.append(("--session", runtime.get("session")))
                    if auth_mode == "interactive-profile":
                        expected_pairs.append(("--profile", runtime.get("profile")))
                    elif auth_mode == "cdp":
                        expected_pairs.append(("--cdp", runtime.get("cdp")))
                    elif auth_mode == "existing-session":
                        expected_flags.append("--no-prepare")
                elif auth_mode == "runtime-headers":
                    expected_flags.append("--runtime-headers-stdin")
                for flag, value in expected_pairs:
                    try:
                        index = run_arguments.index(flag)
                    except ValueError:
                        errors.append(f"FINDINGS.md restart command is missing {flag}")
                    else:
                        if index + 1 >= len(run_arguments) or run_arguments[index + 1] != value:
                            errors.append(f"FINDINGS.md restart command has the wrong value for {flag}")
                for flag in expected_flags:
                    if flag not in run_arguments:
                        errors.append(f"FINDINGS.md restart command is missing {flag}")
    if spec and f"Mechanism kind: `{spec.get('mechanismKind')}`" not in findings_text:
        errors.append("FINDINGS.md mechanism-kind provenance does not match demo.html")
    elif not spec and "Mechanism kind: `" not in findings_text:
        errors.append("FINDINGS.md is missing mechanism-kind provenance")
    if spec and spec.get("mechanismKind") == "page-runtime-extraction":
        if spec.get("mode") != "browser" or "request" in spec:
            errors.append("page-runtime extraction metadata must be browser-only and must not contain an HTTP request")
        if not companion.exists():
            errors.append("page-runtime extraction requires browser-companion.mjs")
        else:
            start_marker = "// WTI-CUSTOMIZE: page-runtime:start"
            end_marker = "// WTI-CUSTOMIZE: page-runtime:end"
            start = companion_text.find(start_marker)
            end = companion_text.find(end_marker, start + len(start_marker))
            if start < 0 or end < 0:
                errors.append("browser-companion.mjs is missing its bounded page-runtime recipe region")
            else:
                recipe = companion_text[start + len(start_marker):end]
                if "WTI_PAGE_RUNTIME_RECIPE_REQUIRED" in recipe:
                    errors.append("browser-companion.mjs still contains the unfinished page-runtime recipe")
                evaluate_calls = re.findall(r"\bevaluate\s*\(", recipe)
                if len(evaluate_calls) != 1 or not re.search(r"\bevaluate\s*\(\s*(?:async\s*)?(?:function\b|\()", recipe):
                    errors.append("page-runtime recipe must contain exactly one fixed inline evaluate function")
                for pattern, label in PAGE_RUNTIME_FORBIDDEN_PATTERNS:
                    if re.search(pattern, recipe):
                        errors.append(f"page-runtime recipe contains forbidden {label}")
            if "assertActiveBrowserPage(session, true)" not in companion_text:
                errors.append("browser-companion.mjs is missing the exact page-path guard")
    temporary_artifacts = sorted(
        {
            path.name
            for pattern in TEMPORARY_ARTIFACT_PATTERNS
            for path in directory.glob(pattern)
            if path.is_file()
        }
    )
    if temporary_artifacts:
        errors.append(
            "temporary build or discovery artifacts remain in the deliverable: "
            + ", ".join(temporary_artifacts)
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Generated prototype directory")
    arguments = parser.parse_args(argv)
    errors = validate(arguments.directory.resolve())
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Prototype validation passed: {arguments.directory.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
