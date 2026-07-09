#!/usr/bin/env python3
"""Run Claude Code as the preferred Smart Handoff synthesis engine."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from smart_handoff_common import (
    REQUIRED_HANDOFF_KEYS,
    DEFAULT_CLAUDE_EFFORT,
    DEFAULT_CLAUDE_MODEL,
    harden_bundle,
    normalize_handoff,
    write_json_private,
    write_text_private,
)

CLAUDE_PREFLIGHT_FALLBACK_WARNING = "Claude preflight unavailable; using configured Codex fallback."


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def update_manifest(
    bundle: Path,
    status: str,
    warning: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    fallback_reason: str | None = None,
) -> None:
    path = bundle / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["synthesis_status"] = status
    manifest["synthesis_engine"] = "claude" if status == "claude" else None
    manifest["synthesis_model"] = model
    manifest["synthesis_effort"] = effort
    if fallback_reason:
        manifest["fallback_reason"] = fallback_reason
    if warning:
        manifest.setdefault("warnings", []).append(warning)
    write_json_private(path, manifest)


def read_manifest(bundle: Path) -> dict[str, Any]:
    path = bundle / "manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def should_skip_for_codex_fallback(manifest: dict[str, Any]) -> bool:
    checks = manifest.get("preflight", {}).get("checks", {})
    claude_unavailable = (
        checks.get("claude_binary", {}).get("ok") is False
        or checks.get("claude_live", {}).get("ok") is False
    )
    codex_available = all(
        checks.get(name, {}).get("ok") is True
        for name in ("codex_binary", "codex_model_policy", "codex_live")
    )
    return claude_unavailable and codex_available


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Claude synthesis for Smart Handoff.")
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--claude-bin", default=os.environ.get("SMART_HANDOFF_CLAUDE_BIN") or shutil.which("claude") or "/Users/phil/.local/bin/claude")
    parser.add_argument("--model", default=os.environ.get("SMART_HANDOFF_CLAUDE_MODEL", DEFAULT_CLAUDE_MODEL))
    parser.add_argument("--effort", default=os.environ.get("SMART_HANDOFF_CLAUDE_EFFORT", DEFAULT_CLAUDE_EFFORT))
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--skip-external", action="store_true", help="Write a deterministic minimal handoff for tests.")
    args = parser.parse_args()

    bundle = Path(args.bundle).resolve()
    synthesis_input = (bundle / "synthesis-input.md").read_text(encoding="utf-8", errors="replace")
    prompt = (
        (skill_root() / "references" / "synthesis-prompt.md").read_text(encoding="utf-8")
        + "\n\n# Evidence\n\n"
        + synthesis_input
    )

    if args.skip_external:
        data = {key: "(not generated; external synthesis skipped)" for key in REQUIRED_HANDOFF_KEYS}
        data["next_steps"] = ["Inspect the handoff bundle and continue from available evidence."]
        data["evidence_index"] = ["synthesis-input.md"]
        handoff, markdown = normalize_handoff(data)
        write_json_private(bundle / "handoff.json", handoff)
        write_text_private(bundle / "handoff.md", markdown)
        update_manifest(bundle, "skipped", model=args.model, effort=args.effort, fallback_reason="external_synthesis_skipped")
        harden_bundle(bundle)
        print("Claude synthesis skipped; deterministic handoff written.")
        return 0

    if should_skip_for_codex_fallback(read_manifest(bundle)):
        write_text_private(bundle / "synthesis-error.txt", CLAUDE_PREFLIGHT_FALLBACK_WARNING + "\n")
        update_manifest(
            bundle,
            "skipped",
            CLAUDE_PREFLIGHT_FALLBACK_WARNING,
            args.model,
            args.effort,
            "claude_preflight_unavailable",
        )
        harden_bundle(bundle)
        print(CLAUDE_PREFLIGHT_FALLBACK_WARNING)
        return 0

    if not args.claude_bin or not Path(args.claude_bin).exists():
        message = f"Claude binary not found: {args.claude_bin}"
        write_text_private(bundle / "synthesis-error.txt", message + "\n")
        update_manifest(bundle, "failed", message, args.model, args.effort, "claude_binary_missing")
        harden_bundle(bundle)
        print(message)
        return 2

    base_cmd = [
        args.claude_bin,
        "-p",
        "--model",
        args.model,
        "--effort",
        args.effort,
        "--permission-mode",
        "dontAsk",
        "--tools",
        "",
    ]
    try:
        result = subprocess.run(base_cmd, input=prompt, text=True, capture_output=True, timeout=args.timeout, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"claude exited {result.returncode}")
        parsed = extract_json(result.stdout)
        handoff, markdown = normalize_handoff(parsed)
        write_json_private(bundle / "handoff.json", handoff)
        write_text_private(bundle / "handoff.md", markdown.rstrip() + "\n")
        update_manifest(bundle, "claude", model=args.model, effort=args.effort)
        harden_bundle(bundle)
        print("Claude synthesis complete.")
        return 0
    except Exception as exc:  # noqa: BLE001 - fallback is handled by verifier.
        message = f"Claude synthesis failed: {exc}"
        write_text_private(bundle / "synthesis-error.txt", message + "\n")
        update_manifest(bundle, "failed", message, args.model, args.effort, "claude_synthesis_failed")
        harden_bundle(bundle)
        print(message)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
