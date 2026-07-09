"""Shared helpers for Smart Handoff scripts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
DEFAULT_CLAUDE_MODEL = "opus"
DEFAULT_CLAUDE_EFFORT = "high"
DEFAULT_CODEX_MODEL = "gpt-5.5"
DEFAULT_CODEX_EFFORT = "xhigh"

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


def as_markdown(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value) or "(none)"
    if isinstance(value, dict):
        return "```json\n" + json.dumps(value, indent=2) + "\n```"
    return str(value or "(none)")


def render_handoff_markdown(data: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Smart Handoff",
            "",
            "## Objective",
            as_markdown(data.get("objective")),
            "",
            "## Current State",
            as_markdown(data.get("current_status")),
            "",
            "## User Preferences And Constraints",
            as_markdown(data.get("user_preferences")),
            "",
            "## Decisions Made",
            as_markdown(data.get("decisions_made")),
            "",
            "## Workspace State",
            as_markdown(data.get("important_context")),
            "",
            "## Files Changed",
            as_markdown(data.get("files_and_changes")),
            "",
            "## Commands And Verification",
            as_markdown(data.get("commands_and_results")) + "\n\n" + as_markdown(data.get("validation_status")),
            "",
            "## Open Questions And Blockers",
            as_markdown(data.get("open_questions")) + "\n\n" + as_markdown(data.get("blockers")),
            "",
            "## Next Steps",
            as_markdown(data.get("next_steps")),
            "",
            "## Do Not Redo",
            as_markdown(data.get("do_not_redo")),
            "",
            "## Evidence Index",
            as_markdown(data.get("evidence_index")),
            "",
        ]
    )


def normalize_handoff(data: dict[str, Any]) -> tuple[dict[str, Any], str]:
    data = dict(data)
    data.pop("handoff_markdown", None)
    for key in REQUIRED_HANDOFF_KEYS:
        data.setdefault(key, [] if key in {"next_steps", "evidence_index"} else "")
    return data, render_handoff_markdown(data).rstrip() + "\n"


def write_text_private(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    try:
        os.chmod(path, PRIVATE_FILE_MODE)
    except OSError:
        pass


def write_json_private(path: Path, data: Any) -> None:
    write_text_private(path, json.dumps(data, indent=2) + "\n")


def harden_bundle(bundle: Path) -> None:
    if not bundle.exists():
        return
    for dirpath, dirnames, filenames in os.walk(bundle):
        current = Path(dirpath)
        if not current.is_symlink():
            try:
                os.chmod(current, PRIVATE_DIR_MODE)
            except OSError:
                pass
        for dirname in list(dirnames):
            path = current / dirname
            if path.is_symlink():
                dirnames.remove(dirname)
        for filename in filenames:
            path = current / filename
            if path.is_symlink():
                continue
            try:
                os.chmod(path, PRIVATE_FILE_MODE)
            except OSError:
                pass


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def model_policy() -> dict[str, Any]:
    return {
        "claude_model": os.environ.get("SMART_HANDOFF_CLAUDE_MODEL", DEFAULT_CLAUDE_MODEL),
        "claude_effort": os.environ.get("SMART_HANDOFF_CLAUDE_EFFORT", DEFAULT_CLAUDE_EFFORT),
        "codex_model": os.environ.get("SMART_HANDOFF_CODEX_MODEL", DEFAULT_CODEX_MODEL),
        "codex_effort": os.environ.get("SMART_HANDOFF_CODEX_EFFORT", DEFAULT_CODEX_EFFORT),
        "allow_partial_create": env_bool("SMART_HANDOFF_ALLOW_PARTIAL_CREATE", False),
    }
