#!/usr/bin/env python3
"""Build the evidence packet sent to synthesis models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_handoff_common import harden_bundle, write_text_private

MAX_SECTION_CHARS = 120_000
KEYWORDS = (
    "objective",
    "decision",
    "decided",
    "constraint",
    "preference",
    "blocker",
    "blocked",
    "open item",
    "next",
    "todo",
    "do not",
    "don't",
    "command",
    "test",
    "verify",
    "error",
    "fail",
    "file",
    "path",
    "needle",
)


def compress_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text

    head_chars = limit // 3
    tail_chars = limit // 3
    middle_budget = limit - head_chars - tail_chars - 400
    lines = text.splitlines()
    priority: list[str] = []
    seen: set[str] = set()
    for line in lines:
        lowered = line.lower()
        if any(keyword in lowered for keyword in KEYWORDS):
            stripped = line[:1000]
            if stripped not in seen:
                priority.append(stripped)
                seen.add(stripped)
        if sum(len(item) + 1 for item in priority) >= middle_budget:
            break

    priority_text = "\n".join(priority)
    if len(priority_text) > middle_budget:
        priority_text = priority_text[:middle_budget] + "\n[PRIORITY LINES TRUNCATED]"

    return (
        text[:head_chars]
        + "\n\n[TRUNCATED: priority lines extracted from omitted middle]\n"
        + priority_text
        + "\n\n[TRUNCATED: tail]\n"
        + text[-tail_chars:]
    )


def read(path: Path, fallback: str = "") -> str:
    if not path.exists():
        return fallback
    text = path.read_text(encoding="utf-8", errors="replace")
    return compress_text(text, MAX_SECTION_CHARS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Smart Handoff synthesis input.")
    parser.add_argument("--bundle", required=True)
    args = parser.parse_args()
    bundle = Path(args.bundle).resolve()

    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    sections = [
        "# Smart Handoff Synthesis Evidence",
        "",
        "## Manifest",
        "```json",
        json.dumps(manifest, indent=2),
        "```",
        "",
        "## Workspace Summary",
        read(bundle / "workspace-summary.md", "(missing workspace summary)"),
        "",
        "## Conversation Brief",
        read(bundle / "conversation-brief.md", "(conversation brief not captured; use available manifest/workspace evidence and mark conversation unknowns)"),
        "",
        "## Decisions",
        read(bundle / "decisions.md", "(decisions not captured)"),
        "",
        "## Open Items",
        read(bundle / "open-items.md", "(open items not captured)"),
        "",
        "## User Preferences",
        read(bundle / "user-preferences.md", "(user preferences not captured)"),
        "",
        "## Surface State",
        read(bundle / "surface-state.md", "(surface state not captured)"),
        "",
        "## Workspace State JSON",
        "```json",
        read(bundle / "workspace-state.json", "{}"),
        "```",
    ]
    output = "\n".join(sections).strip() + "\n"
    write_text_private(bundle / "synthesis-input.md", output)
    harden_bundle(bundle)
    print(f"Synthesis input built: {bundle / 'synthesis-input.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
