#!/usr/bin/env python3
"""Normalize recoverable browser and terminal surface state for a fresh thread."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from smart_handoff_common import harden_bundle, write_json_private, write_text_private

MAX_TERMINAL_CHARS = 12_000
MAX_TERMINAL_EXCERPT = 4_000
MAX_TITLE_CHARS = 180
MAX_COMMAND_CHARS = 240
MAX_URLS = 12
MAX_COMMANDS = 12

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|token|bearer)\s*[:=]\s*[^\s'\"`]+"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]
URL_RE = re.compile(r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(?::\d+)?[^\s<>'\")`]*")
DEV_COMMAND_RE = re.compile(
    r"(?:(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?(?:dev|start|serve|preview)(?:\s+[^\n\r]*)?|"
    r"(?:next|vite|astro|remix|nuxt|svelte-kit)\s+(?:dev|start|preview)(?:\s+[^\n\r]*)?)",
    re.IGNORECASE,
)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False, "reason": "not captured", "selected": None, "tabs": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:  # noqa: BLE001 - capture files are best-effort inputs.
        return {"available": False, "reason": f"invalid JSON: {exc}", "selected": None, "tabs": []}
    return data if isinstance(data, dict) else {"available": False, "reason": "capture was not an object", "selected": None, "tabs": []}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[-MAX_TERMINAL_CHARS:]


def redact(text: str) -> tuple[str, int]:
    count = 0
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted, replaced = pattern.subn("[REDACTED]", redacted)
        count += replaced
    return redacted, count


def truncate(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 20].rstrip() + " [truncated]"


def normalize_url(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text.startswith(("http://", "https://")):
        return None
    parsed = urlparse(text)
    if not parsed.scheme or not parsed.netloc:
        return None
    return text


def local_port(url: str) -> int | None:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host not in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        return None
    try:
        return parsed.port
    except ValueError:
        return None


def unique(items: list[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for item in items:
        key = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def browser_entries(browser: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    selected_raw = browser.get("selected")
    selected = None
    if isinstance(selected_raw, dict):
        url = normalize_url(selected_raw.get("url"))
        if url:
            selected = {"url": url, "title": truncate(selected_raw.get("title"), MAX_TITLE_CHARS)}

    tabs: list[dict[str, str]] = []
    for raw in browser.get("tabs", []) if isinstance(browser.get("tabs"), list) else []:
        if not isinstance(raw, dict):
            continue
        url = normalize_url(raw.get("url"))
        if url:
            tabs.append({"url": url, "title": truncate(raw.get("title"), MAX_TITLE_CHARS)})
    return selected, unique(tabs)[:MAX_URLS]


def package_manager(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        return "bun"
    if (root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def package_script_commands(root: Path) -> list[str]:
    package_json = root / "package.json"
    if not package_json.exists():
        return []
    try:
        data = json.loads(package_json.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []
    scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
    if not isinstance(scripts, dict):
        return []
    pm = package_manager(root)
    commands: list[str] = []
    for name in ("dev", "start", "serve", "preview"):
        if name in scripts:
            if pm == "npm":
                commands.append(f"npm run {name}")
            elif pm == "yarn":
                commands.append(f"yarn {name}")
            else:
                commands.append(f"{pm} {name}")
    return commands


def terminal_commands(terminal: str) -> list[str]:
    commands: list[str] = []
    for match in DEV_COMMAND_RE.finditer(terminal):
        command = truncate(match.group(0), MAX_COMMAND_CHARS)
        commands.append(command)
    return commands


def terminal_urls(terminal: str) -> list[str]:
    return unique([match.group(0) for match in URL_RE.finditer(terminal)])[:MAX_URLS]


def render_markdown(surface: dict[str, Any]) -> str:
    lines = [
        "# Surface State",
        "",
        f"- Capture status: `{surface['capture_status']}`",
        f"- Source thread semantics: `{surface['source_thread_semantics']}`",
        "",
        "## Browser",
    ]
    selected = surface["browser"].get("selected")
    lines.append(f"- Selected URL: {selected['url']}" if selected else "- Selected URL: (none captured)")
    tabs = surface["browser"].get("tabs") or []
    lines.append("- Open tabs:")
    lines.extend(f"  - {tab['url']} ({tab.get('title') or 'untitled'})" for tab in tabs[:MAX_URLS])
    if not tabs:
        lines.append("  - (none captured)")
    lines += ["", "## Localhost And Dev Server"]
    urls = surface.get("localhost_urls") or []
    lines.append("- Local URLs:")
    lines.extend(f"  - {url}" for url in urls)
    if not urls:
        lines.append("  - (none captured)")
    ports = surface.get("ports") or []
    lines.append("- Ports:")
    lines.extend(f"  - {port}" for port in ports)
    if not ports:
        lines.append("  - (none captured)")
    commands = surface.get("dev_server_command_candidates") or []
    lines.append("- Dev server command candidates:")
    lines.extend(f"  - `{command}`" for command in commands)
    if not commands:
        lines.append("  - (none captured)")
    lines += [
        "",
        "## Fresh Thread Takeover Guidance",
        "- Reopen captured browser URLs when browser tooling is available.",
        "- For localhost URLs, first check whether the captured URL is reachable.",
        "- If the server is down, start the most plausible project dev command from the original cwd.",
        "- If the captured port is occupied by an unrelated process, do not kill it; choose a safe alternative and explain.",
        "- If the captured port is occupied by this same project/dev server, reuse or restart it so the URL stays stable.",
        "- Do not claim scroll position, form state, terminal scrollback, or hidden browser state was preserved.",
        "",
        "## Terminal Tail Excerpt",
    ]
    excerpt = surface["terminal"].get("tail_excerpt") or "(none captured)"
    lines += ["```text", excerpt, "```", ""]
    return "\n".join(lines)


def update_manifest(bundle: Path, redactions: int) -> None:
    manifest_path = bundle / "manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["redaction_count"] = int(manifest.get("redaction_count", 0)) + redactions
    artifacts = manifest.setdefault("artifacts", {})
    artifacts.setdefault("browser_state", "browser-state.json")
    artifacts.setdefault("terminal_state", "terminal-state.txt")
    artifacts.setdefault("surface_state_json", "surface-state.json")
    artifacts.setdefault("surface_state_markdown", "surface-state.md")
    write_json_private(manifest_path, manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Smart Handoff surface-state artifacts.")
    parser.add_argument("--bundle", required=True)
    args = parser.parse_args()

    bundle = Path(args.bundle).resolve()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8")) if (bundle / "manifest.json").exists() else {}
    root = Path(manifest.get("cwd") or ".").resolve()

    browser_raw = read_json(bundle / "browser-state.json")
    terminal_raw, redactions = redact(read_text(bundle / "terminal-state.txt"))
    selected, tabs = browser_entries(browser_raw)
    browser_urls = [selected["url"]] if selected else []
    browser_urls.extend(tab["url"] for tab in tabs)
    local_urls = unique([url for url in browser_urls + terminal_urls(terminal_raw) if local_port(url) is not None])[:MAX_URLS]
    ports = unique([port for port in (local_port(url) for url in local_urls) if port is not None])
    commands = unique(terminal_commands(terminal_raw) + package_script_commands(root))[:MAX_COMMANDS]

    has_surface = bool(selected or tabs or local_urls or commands or terminal_raw.strip())
    surface = {
        "capture_status": "captured" if has_surface else "not_captured",
        "source_thread_semantics": "source_thread_abandoned_continue_in_fresh_thread",
        "browser": {
            "available": bool(browser_raw.get("available")),
            "reason": browser_raw.get("reason") or browser_raw.get("error"),
            "selected": selected,
            "tabs": tabs,
        },
        "terminal": {
            "captured": bool(terminal_raw.strip()),
            "tail_chars": len(terminal_raw),
            "tail_excerpt": terminal_raw[-MAX_TERMINAL_EXCERPT:].strip(),
        },
        "localhost_urls": local_urls,
        "ports": ports,
        "dev_server_command_candidates": commands,
        "takeover_allowed": True,
        "takeover_limits": [
            "Recreate reachable browser URLs and dev servers; do not preserve hidden UI state.",
            "Only stop/restart a process when it appears to be the captured project dev server.",
            "Do not kill unrelated processes just because they use the same port.",
        ],
        "redaction_count": redactions,
    }

    write_json_private(bundle / "surface-state.json", surface)
    write_text_private(bundle / "surface-state.md", render_markdown(surface))
    update_manifest(bundle, redactions)
    harden_bundle(bundle)
    print(f"Surface state built: {bundle / 'surface-state.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
