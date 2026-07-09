#!/usr/bin/env python3
"""Create the bounded self-contained prompt used for the fresh Codex thread."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from smart_handoff_common import harden_bundle, write_text_private

MAX_PROMPT_CHARS = 20_000
HANDOFF_BUDGET = 12_500
WORKSPACE_BUDGET = 4_000
VERIFICATION_BUDGET = 2_000
SURFACE_BUDGET = 3_000


def as_lines(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value) or "(none)"
    if isinstance(value, dict):
        return json.dumps(value, indent=2)
    return str(value or "(none)")


def read_text(path: Path, fallback: str = "") -> str:
    if not path.exists():
        return fallback
    return path.read_text(encoding="utf-8", errors="replace").strip()


def compress_middle(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    if limit < 500:
        return text[:limit]
    head = max(200, limit // 2)
    tail = max(200, limit - head - 120)
    return text[:head].rstrip() + "\n\n[Omitted middle content to keep the fresh-thread prompt bounded.]\n\n" + text[-tail:].lstrip()


def compact_json(data: Any, limit: int) -> str:
    return compress_middle(json.dumps(data, indent=2, sort_keys=True), limit)


def scrub_temporary_paths(text: str, bundle: Path) -> str:
    replacements = {
        str(bundle): "[temporary Smart Handoff scratch bundle path omitted]",
        str(bundle.parent): "[temporary Smart Handoff scratch parent omitted]",
    }
    scrubbed = text
    for needle, replacement in replacements.items():
        scrubbed = scrubbed.replace(needle, replacement)
    return scrubbed


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a fresh-thread Smart Handoff prompt.")
    parser.add_argument("--bundle", required=True)
    args = parser.parse_args()

    bundle = Path(args.bundle).resolve()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    handoff = json.loads((bundle / "handoff.json").read_text(encoding="utf-8"))
    verification = json.loads((bundle / "verification.json").read_text(encoding="utf-8")) if (bundle / "verification.json").exists() else {}
    workspace_state = json.loads((bundle / "workspace-state.json").read_text(encoding="utf-8")) if (bundle / "workspace-state.json").exists() else {}
    surface_state = json.loads((bundle / "surface-state.json").read_text(encoding="utf-8")) if (bundle / "surface-state.json").exists() else {}
    changed_paths = workspace_state.get("git", {}).get("changed_paths", [])
    handoff_markdown = compress_middle(read_text(bundle / "handoff.md", "# Smart Handoff\n\n(missing handoff markdown)"), HANDOFF_BUDGET)
    workspace_summary = compress_middle(read_text(bundle / "workspace-summary.md", "(workspace summary missing)"), WORKSPACE_BUDGET)
    surface_summary = compress_middle(read_text(bundle / "surface-state.md", "(surface state not captured)"), SURFACE_BUDGET)
    surface_present = surface_state.get("capture_status") == "captured"
    verification_summary = compact_json(
        {
            "status": verification.get("status", "unknown"),
            "handoff_quality": verification.get("handoff_quality", manifest.get("handoff_quality", "unknown")),
            "safe_to_create_thread": verification.get("safe_to_create_thread"),
            "issues": verification.get("issues", []),
            "required_repairs": verification.get("required_repairs", []),
            "degraded_reasons": verification.get("degraded_reasons", manifest.get("degraded_reasons", [])),
            "confidence_notes": verification.get("confidence_notes", []),
            "synthesis_engine": manifest.get("synthesis_engine"),
            "synthesis_model": manifest.get("synthesis_model"),
            "synthesis_effort": manifest.get("synthesis_effort"),
            "verification_engine": manifest.get("verification_engine"),
            "verification_model": manifest.get("verification_model"),
            "verification_effort": manifest.get("verification_effort"),
            "fallback_reason": manifest.get("fallback_reason"),
        },
        VERIFICATION_BUDGET,
    )

    prompt = f"""Continue this Codex session from the self-contained Smart Handoff below.

Original cwd:
{manifest.get("cwd")}

This prompt is self-contained. The scratch bundle files used to build it are temporary and may be deleted after this thread is created. Do not ask the user to restate context.

Operating instructions:
- Continue the user's active task without redoing completed work.
- Verify the current filesystem and git state in the original cwd before editing.
- Preserve the user preferences and constraints listed in the handoff.
- Treat the handoff as evidence-backed but not magical hidden state; unfinished tool calls, browser internals, form state, and terminal scrollback do not carry over.
- Recreate captured browser/dev-server surface state when the Surface State section contains concrete URLs, ports, or commands.
- For localhost URLs, keep the captured port when feasible: check reachability first, start the likely dev server if it is down, and only stop/restart a process if it appears to be this same project dev server.
- Do not kill unrelated processes just because they occupy a captured port.
- If this prompt conflicts with the current filesystem state, trust the filesystem and explain the discrepancy briefly.

Objective snapshot:
{as_lines(handoff.get("objective"))}

Next steps:
{as_lines(handoff.get("next_steps"))}

Do not redo:
{as_lines(handoff.get("do_not_redo"))}

Changed paths captured at handoff time:
{as_lines(changed_paths)}

Surface state to recreate:
{surface_summary if surface_present else "(no recoverable browser/dev-server surface state was captured)"}

Verification summary:
```json
{verification_summary}
```

Embedded handoff:
{handoff_markdown}

Workspace snapshot:
{workspace_summary}
"""
    if len(prompt) > MAX_PROMPT_CHARS:
        overflow = len(prompt) - MAX_PROMPT_CHARS + 400
        handoff_markdown = compress_middle(handoff_markdown, max(4_000, len(handoff_markdown) - overflow))
        prompt = f"""Continue this Codex session from the self-contained Smart Handoff below.

Original cwd:
{manifest.get("cwd")}

This prompt is self-contained. The scratch bundle files used to build it are temporary and may be deleted after this thread is created. Do not ask the user to restate context.

Operating instructions:
- Continue the user's active task without redoing completed work.
- Verify the current filesystem and git state in the original cwd before editing.
- Preserve the user preferences and constraints listed in the handoff.
- Recreate captured browser/dev-server surface state when the Surface State section contains concrete URLs, ports, or commands; do not kill unrelated processes.
- If this prompt conflicts with the current filesystem state, trust the filesystem and explain the discrepancy briefly.

Objective snapshot:
{as_lines(handoff.get("objective"))}

Next steps:
{as_lines(handoff.get("next_steps"))}

Do not redo:
{as_lines(handoff.get("do_not_redo"))}

Changed paths captured at handoff time:
{as_lines(changed_paths)}

Surface state to recreate:
{compress_middle(surface_summary if surface_present else "(no recoverable browser/dev-server surface state was captured)", 1_500)}

Verification summary:
```json
{verification_summary}
```

Embedded handoff:
{handoff_markdown}

Workspace snapshot:
{compress_middle(workspace_summary, 2_000)}
"""
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[: MAX_PROMPT_CHARS - 120].rstrip() + "\n\n[Prompt tail truncated to respect the Smart Handoff prompt limit.]\n"
    prompt = scrub_temporary_paths(prompt, bundle)
    write_text_private(bundle / "new-thread-prompt.md", prompt)
    harden_bundle(bundle)
    print(f"New-thread prompt built: {bundle / 'new-thread-prompt.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
