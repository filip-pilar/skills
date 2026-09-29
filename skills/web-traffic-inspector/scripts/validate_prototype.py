#!/usr/bin/env python3
"""Check that a generated proof is complete; this does not verify its behavior."""

import argparse
import json
import re
from pathlib import Path


def read_config(text: str, name: str) -> dict:
    match = re.search(rf"\bconst\s+{name}\s*=\s*", text)
    if not match:
        raise ValueError(f"Missing generated {name} configuration.")
    value, _ = json.JSONDecoder().raw_decode(text[match.end():])
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object.")
    return value


def validate(directory: Path) -> list[str]:
    errors = []
    try:
        demo = (directory / "demo.html").read_text(encoding="utf-8")
        findings = (directory / "FINDINGS.md").read_text(encoding="utf-8")
        spec = read_config(demo, "SPEC")
        if spec.get("mode") not in {"direct", "relay", "browser"}:
            errors.append("Unknown execution mode.")
        if spec.get("mechanismKind") not in {"http-replay", "page-runtime-extraction"}:
            errors.append("Unknown mechanism kind.")
        companion = ""
        if spec.get("mode") in {"relay", "browser"}:
            companion = (directory / "browser-companion.mjs").read_text(encoding="utf-8")
            config = read_config(companion, "CONFIG")
            transport = "browser" if spec["mode"] == "browser" else "node"
            if config.get("transport") != transport or config.get("mechanismKind") != spec.get("mechanismKind"):
                errors.append("Page and companion execution configurations disagree.")
        if "__WTI_" in demo + findings + companion:
            errors.append("Unresolved scaffold marker found.")
        if "WTI_ACTION_REQUIRED" in demo:
            errors.append("Complete the task-specific action and its domain success check.")
        if "WTI-FINDINGS:" in findings or not findings.strip():
            errors.append("Replace the findings prompt with actual verification evidence and limits.")
        if spec.get("mechanismKind") == "page-runtime-extraction":
            if spec.get("mode") != "browser" or "WTI_PAGE_RUNTIME_RECIPE_REQUIRED" in companion:
                errors.append("Page extraction requires a browser companion with a completed fixed recipe.")
        for pattern in ("spec.json", "*probe.html", "*.har", "*.trace", "trace.zip"):
            errors.extend(f"Remove temporary capture/probe: {path.relative_to(directory)}" for path in directory.rglob(pattern))
    except (OSError, ValueError) as error:
        errors.append(str(error))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    errors = validate(parser.parse_args().directory)
    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1
    print("Completion check passed. Behavioral verification still depends on the recorded evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
