#!/usr/bin/env python3
"""Validate a Smart Handoff bundle before fresh-thread creation."""

from __future__ import annotations

import argparse
import json
import stat
import os
from pathlib import Path

from smart_handoff_common import PRIVATE_DIR_MODE, PRIVATE_FILE_MODE, harden_bundle, write_json_private

MAX_PROMPT_CHARS = 20_000

REQUIRED_FILES = [
    "manifest.json",
    "workspace-state.json",
    "workspace-summary.md",
    "surface-state.json",
    "surface-state.md",
    "synthesis-input.md",
    "handoff.json",
    "handoff.md",
    "verification.json",
    "verification.md",
    "new-thread-prompt.md",
]

REQUIRED_MANIFEST_KEYS = [
    "run_id",
    "created_at",
    "cwd",
    "bundle_path",
    "bundle_storage",
    "cleanup_status",
    "source_thread_id",
    "skill_version",
    "detected_tools",
    "artifacts",
    "warnings",
    "omissions",
    "redaction_count",
    "verification_status",
    "handoff_quality",
    "degraded_reasons",
    "model_policy",
    "preflight",
    "synthesis_engine",
    "synthesis_model",
    "synthesis_effort",
    "verification_engine",
    "verification_model",
    "verification_effort",
    "fallback_reason",
]

REQUIRED_HANDOFF_KEYS = [
    "objective",
    "current_status",
    "user_preferences",
    "important_context",
    "decisions_made",
    "files_and_changes",
    "commands_and_results",
    "validation_status",
    "open_questions",
    "blockers",
    "next_steps",
    "do_not_redo",
    "evidence_index",
    "confidence_notes",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def mode(path: Path) -> int:
    return stat.S_IMODE(path.lstat().st_mode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Smart Handoff bundle artifacts.")
    parser.add_argument("--bundle", required=True)
    args = parser.parse_args()
    bundle = Path(args.bundle).resolve()
    harden_bundle(bundle)
    errors: list[str] = []
    warnings: list[str] = []

    if bundle.exists() and mode(bundle) != PRIVATE_DIR_MODE:
        errors.append(f"Bundle directory mode must be 0700, found {oct(mode(bundle))}")

    for filename in REQUIRED_FILES:
        path = bundle / filename
        if not path.exists():
            errors.append(f"Missing required file: {filename}")
        elif path.stat().st_size == 0:
            errors.append(f"Required file is empty: {filename}")
        elif mode(path) != PRIVATE_FILE_MODE:
            errors.append(f"Required file must be 0600: {filename} has {oct(mode(path))}")

    if (bundle / "manifest.json").exists():
        manifest = load_json(bundle / "manifest.json")
        for key in REQUIRED_MANIFEST_KEYS:
            if key not in manifest:
                errors.append(f"manifest.json missing key: {key}")
        quality = manifest.get("handoff_quality")
        if quality in {"failed", "degraded"}:
            errors.append(f"handoff_quality is {quality}: {', '.join(manifest.get('degraded_reasons', []))}")
        elif quality == "partial":
            allow_partial = bool(manifest.get("model_policy", {}).get("allow_partial_create")) or os.environ.get("SMART_HANDOFF_ALLOW_PARTIAL_CREATE") in {"1", "true", "TRUE", "yes", "on"}
            if allow_partial:
                warnings.append("handoff_quality is partial; fresh-thread creation is explicitly allowed with caveats")
            else:
                errors.append("handoff_quality is partial and SMART_HANDOFF_ALLOW_PARTIAL_CREATE is not enabled")
        if manifest.get("preflight", {}).get("status") in {"fail", "needs_escalation"}:
            errors.append(f"preflight status is {manifest.get('preflight', {}).get('status')}")
        if manifest.get("bundle_storage") != "temporary_scratch":
            errors.append("manifest.json bundle_storage must be temporary_scratch")

    if (bundle / "handoff.json").exists():
        handoff = load_json(bundle / "handoff.json")
        for key in REQUIRED_HANDOFF_KEYS:
            if key not in handoff:
                errors.append(f"handoff.json missing key: {key}")
        if not handoff.get("next_steps"):
            errors.append("handoff.json next_steps is empty")

    if (bundle / "verification.json").exists():
        verification = load_json(bundle / "verification.json")
        if verification.get("status") == "fail":
            errors.append("verification status is fail")
        if verification.get("safe_to_create_thread") is False:
            errors.append("verification marks bundle unsafe for fresh-thread creation")
        if verification.get("handoff_quality") in {"failed", "degraded"}:
            errors.append(f"verification handoff_quality is {verification.get('handoff_quality')}")

    prompt_path = bundle / "new-thread-prompt.md"
    if prompt_path.exists():
        prompt_text = prompt_path.read_text(encoding="utf-8", errors="replace")
        prompt_lower = prompt_text.lower()
        if len(prompt_text) > MAX_PROMPT_CHARS:
            errors.append(f"new-thread-prompt.md exceeds {MAX_PROMPT_CHARS} characters")
        if "self-contained" not in prompt_lower:
            errors.append("new-thread-prompt.md must state that the prompt is self-contained")
        if "read first:" in prompt_lower:
            errors.append("new-thread-prompt.md must not depend on a Read first bundle-file instruction")
        if str(bundle) in prompt_text:
            errors.append("new-thread-prompt.md must not include or depend on the temporary scratch bundle path")
        if (bundle / "surface-state.json").exists():
            surface = load_json(bundle / "surface-state.json")
            if surface.get("capture_status") == "captured" and "surface state to recreate" not in prompt_lower:
                errors.append("new-thread-prompt.md must include captured surface state recreation guidance")

    report = {
        "status": "fail" if errors else "pass",
        "errors": errors,
        "warnings": warnings,
    }
    write_json_private(bundle / "validation.json", report)
    harden_bundle(bundle)
    print(f"Bundle validation: {report['status']}")
    if errors:
        for error in errors[:10]:
            print(f"- {error}")
    elif warnings:
        for warning in warnings[:10]:
            print(f"- warning: {warning}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
