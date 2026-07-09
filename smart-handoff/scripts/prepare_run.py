#!/usr/bin/env python3
"""Prepare a Smart Handoff run directory and manifest."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from smart_handoff_common import PRIVATE_DIR_MODE, model_policy, write_json_private

SKILL_VERSION = "1.4.1"


def now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def detect_tools() -> dict[str, str | None]:
    return {
        "claude": shutil.which("claude") or "/Users/phil/.local/bin/claude",
        "codex": shutil.which("codex") or "/opt/homebrew/bin/codex",
        "git": shutil.which("git"),
        "python3": shutil.which("python3"),
    }


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    slug = slug.strip(".-")[:64]
    return slug or "workspace"


def default_base_dir(root: Path) -> Path:
    temp_root = Path(os.environ.get("SMART_HANDOFF_TMPDIR", "/private/tmp")).resolve()
    if not temp_root.exists():
        temp_root = Path(tempfile.gettempdir()).resolve()
    return temp_root / "codex-smart-handoff" / safe_slug(root.name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Smart Handoff bundle.")
    parser.add_argument("--root", default=os.getcwd(), help="Workspace root. Defaults to cwd.")
    parser.add_argument("--base-dir", default=None, help="Override handoff base directory.")
    parser.add_argument("--source-thread-id", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_id = now_slug()
    base_dir = Path(args.base_dir).resolve() if args.base_dir else default_base_dir(root)
    base_dir.mkdir(mode=PRIVATE_DIR_MODE, parents=True, exist_ok=True)
    os.chmod(base_dir, PRIVATE_DIR_MODE)
    if base_dir.parent.name == "codex-smart-handoff":
        try:
            os.chmod(base_dir.parent, PRIVATE_DIR_MODE)
        except OSError:
            pass
    bundle = base_dir / run_id
    bundle.mkdir(mode=PRIVATE_DIR_MODE, parents=True, exist_ok=False)
    os.chmod(bundle, PRIVATE_DIR_MODE)

    artifacts = {
        "manifest": "manifest.json",
        "workspace_state": "workspace-state.json",
        "workspace_summary": "workspace-summary.md",
        "browser_state": "browser-state.json",
        "terminal_state": "terminal-state.txt",
        "surface_state_json": "surface-state.json",
        "surface_state_markdown": "surface-state.md",
        "preflight_status": "preflight-status.json",
        "synthesis_input": "synthesis-input.md",
        "handoff_json": "handoff.json",
        "handoff_markdown": "handoff.md",
        "verification_json": "verification.json",
        "verification_markdown": "verification.md",
        "new_thread_prompt": "new-thread-prompt.md",
        "validation": "validation.json",
        "cleanup_log": "cleanup.log",
        "conversation_brief": "conversation-brief.md",
        "decisions": "decisions.md",
        "open_items": "open-items.md",
        "user_preferences": "user-preferences.md",
    }

    manifest = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cwd": str(root),
        "bundle_path": str(bundle),
        "bundle_storage": "temporary_scratch",
        "cleanup_status": "not_run",
        "retention_policy": "delete_after_successful_thread_creation; keep_on_validation_or_thread_creation_failure",
        "host": platform.node(),
        "source_thread_id": args.source_thread_id,
        "skill_version": SKILL_VERSION,
        "detected_tools": detect_tools(),
        "model_policy": model_policy(),
        "preflight": {"status": "not_run", "checks": {}},
        "synthesis_engine": None,
        "synthesis_model": None,
        "synthesis_effort": None,
        "verification_engine": None,
        "verification_model": None,
        "verification_effort": None,
        "fallback_reason": None,
        "artifacts": artifacts,
        "warnings": [],
        "omissions": [],
        "redaction_count": 0,
        "verification_status": "not_run",
        "handoff_quality": "not_run",
        "degraded_reasons": [],
    }
    write_json_private(bundle / "manifest.json", manifest)

    if args.quiet:
        print(str(bundle))
    else:
        print(f"Smart Handoff bundle: {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
