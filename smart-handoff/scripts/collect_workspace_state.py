#!/usr/bin/env python3
"""Collect grounded workspace evidence for Smart Handoff."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from smart_handoff_common import harden_bundle, write_json_private, write_text_private

MAX_COMMAND_CHARS = 180_000
MAX_FILE_CHARS = 24_000
MAX_PROJECTLESS_FILES = 80
MAX_PROJECTLESS_TOTAL_CHARS = 120_000

SKIP_DIRS = {
    ".git",
    ".codex",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "target",
    ".next",
    ".cache",
    "coverage",
    "__pycache__",
    ".venv",
    "venv",
}

SENSITIVE_PATTERNS = [
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "id_rsa",
    "id_ed25519",
    "*credentials*",
    "*secret*",
]

GUIDANCE_PATTERNS = [
    "AGENTS.md",
    "CLAUDE.md",
    "README",
    "README.*",
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "requirements*.txt",
    "pnpm-lock.yaml",
    "bun.lock",
    "yarn.lock",
    "package-lock.json",
]

SECRET_REGEXES = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password|authorization|bearer)\b\s*[:=]\s*[\"']?([A-Za-z0-9_./+=:@-]{8,})"),
]


def load_manifest(bundle: Path) -> dict[str, Any]:
    return json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))


def save_manifest(bundle: Path, manifest: dict[str, Any]) -> None:
    write_json_private(bundle / "manifest.json", manifest)


def redact(text: str) -> tuple[str, int]:
    count = 0
    redacted = text
    for regex in SECRET_REGEXES:
        def repl(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            if len(match.groups()) >= 2:
                return f"{match.group(1)}=<REDACTED>"
            return "<REDACTED_SECRET>"

        redacted = regex.sub(repl, redacted)
    return redacted, count


def run(cmd: list[str], cwd: Path, timeout: int = 20) -> dict[str, Any]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        stdout, c1 = redact(result.stdout)
        stderr, c2 = redact(result.stderr)
        truncated = False
        combined_len = len(stdout) + len(stderr)
        if combined_len > MAX_COMMAND_CHARS:
            keep = MAX_COMMAND_CHARS // 2
            stdout = stdout[:keep] + "\n[TRUNCATED]\n" + stdout[-keep:]
            stderr = stderr[:keep] + "\n[TRUNCATED]\n" + stderr[-keep:]
            truncated = True
        return {
            "cmd": cmd,
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "redactions": c1 + c2,
            "truncated": truncated,
        }
    except Exception as exc:  # noqa: BLE001 - evidence capture should continue.
        return {"cmd": cmd, "error": str(exc), "returncode": None, "stdout": "", "stderr": "", "redactions": 0}


def is_git_repo(root: Path) -> bool:
    result = run(["git", "rev-parse", "--is-inside-work-tree"], root, timeout=10)
    return result.get("returncode") == 0 and "true" in result.get("stdout", "")


def skipped_path(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIRS:
        return True
    name = path.name
    return any(fnmatch.fnmatch(name, pattern) for pattern in SENSITIVE_PATTERNS)


def is_text_file(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            chunk = handle.read(4096)
        if b"\x00" in chunk:
            return False
        chunk.decode("utf-8")
        return True
    except Exception:
        return False


def read_safe(path: Path) -> dict[str, Any]:
    if skipped_path(path):
        return {"path": str(path), "omitted": "sensitive_or_skipped"}
    if not path.is_file() or not is_text_file(path):
        return {"path": str(path), "omitted": "non_text_or_missing"}
    text = path.read_text(encoding="utf-8", errors="replace")
    text, count = redact(text)
    truncated = len(text) > MAX_FILE_CHARS
    if truncated:
        text = text[:MAX_FILE_CHARS] + "\n[TRUNCATED]\n"
    return {"path": str(path), "content": text, "redactions": count, "truncated": truncated}


def find_guidance_files(root: Path) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not skipped_path(current / d)]
        depth = len(current.relative_to(root).parts)
        if depth > 3:
            dirnames[:] = []
        for filename in filenames:
            if any(fnmatch.fnmatch(filename, pattern) for pattern in GUIDANCE_PATTERNS):
                found.append(read_safe(current / filename))
    return found[:40]


def parse_status_paths(status: str) -> list[str]:
    paths: list[str] = []
    for line in status.splitlines():
        if not line.strip():
            continue
        raw = line[3:] if len(line) > 3 else line
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        paths.append(raw.strip())
    return paths


def is_skipped_rel(rel: str) -> bool:
    cleaned = rel.strip().strip('"')
    if not cleaned:
        return False
    return skipped_path(Path(cleaned))


def status_path(line: str) -> str | None:
    if line.startswith("##"):
        return None
    raw = line[3:] if len(line) > 3 else line
    if " -> " in raw:
        raw = raw.split(" -> ", 1)[1]
    return raw.strip().strip('"')


def filter_status_output(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        path = status_path(line)
        if path is None:
            lines.append(line)
        elif not is_skipped_rel(path):
            lines.append(line)
    return "\n".join(lines) + ("\n" if lines else "")


def filter_untracked_output(text: str) -> str:
    lines = [line for line in text.splitlines() if not is_skipped_rel(line)]
    return "\n".join(lines) + ("\n" if lines else "")


def collect_git(root: Path) -> dict[str, Any]:
    if not is_git_repo(root):
        return {"is_git_repo": False}
    commands = {
        "top_level": ["git", "rev-parse", "--show-toplevel"],
        "branch": ["git", "branch", "--show-current"],
        "head": ["git", "rev-parse", "--short", "HEAD"],
        "status_short": ["git", "status", "--short"],
        "status": ["git", "status", "--porcelain=v1", "-b"],
        "diffstat": ["git", "diff", "--stat"],
        "staged_diffstat": ["git", "diff", "--cached", "--stat"],
        "diff": ["git", "diff", "--no-ext-diff"],
        "staged_diff": ["git", "diff", "--cached", "--no-ext-diff"],
        "untracked": ["git", "ls-files", "--others", "--exclude-standard"],
    }
    data: dict[str, Any] = {"is_git_repo": True, "commands": {}}
    redactions = 0
    for name, cmd in commands.items():
        result = run(cmd, root, timeout=30)
        redactions += int(result.get("redactions", 0))
        if name in {"status", "status_short"}:
            result["stdout"] = filter_status_output(result.get("stdout", ""))
        if name == "untracked":
            result["stdout"] = filter_untracked_output(result.get("stdout", ""))
        data["commands"][name] = result
    status_short = data["commands"]["status_short"].get("stdout", "")
    data["changed_paths"] = parse_status_paths(status_short)
    return data | {"redactions": redactions}


def collect_untracked_summaries(root: Path, git_data: dict[str, Any]) -> list[dict[str, Any]]:
    if not git_data.get("is_git_repo"):
        return []
    raw = git_data.get("commands", {}).get("untracked", {}).get("stdout", "")
    summaries = []
    for rel in raw.splitlines()[:60]:
        path = root / rel
        summaries.append(read_safe(path))
    return summaries


def collect_projectless_files(root: Path, guidance: list[dict[str, Any]]) -> list[dict[str, Any]]:
    guidance_paths = {str(item.get("path")) for item in guidance}
    captured: list[dict[str, Any]] = []
    total_chars = 0
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not skipped_path(current / d)]
        depth = len(current.relative_to(root).parts)
        if depth > 3:
            dirnames[:] = []
            continue
        for filename in sorted(filenames):
            path = current / filename
            if str(path) in guidance_paths:
                continue
            if skipped_path(path) or not path.is_file() or not is_text_file(path):
                continue
            item = read_safe(path)
            content = str(item.get("content", ""))
            total_chars += len(content)
            captured.append(item)
            if len(captured) >= MAX_PROJECTLESS_FILES or total_chars >= MAX_PROJECTLESS_TOTAL_CHARS:
                return captured
    return captured


def render_summary(root: Path, state: dict[str, Any]) -> str:
    git_data = state.get("git", {})
    lines = ["# Workspace Evidence", "", f"- CWD: `{root}`"]
    if git_data.get("is_git_repo"):
        commands = git_data.get("commands", {})
        branch = commands.get("branch", {}).get("stdout", "").strip() or "(detached/unknown)"
        head = commands.get("head", {}).get("stdout", "").strip() or "unknown"
        lines += [f"- Git branch: `{branch}`", f"- Git HEAD: `{head}`", ""]
        lines += ["## Git Status", "", "```text", commands.get("status_short", {}).get("stdout", "").strip() or "(clean)", "```", ""]
        lines += ["## Diffstat", "", "```text", commands.get("diffstat", {}).get("stdout", "").strip() or "(none)", "```", ""]
        lines += ["## Staged Diffstat", "", "```text", commands.get("staged_diffstat", {}).get("stdout", "").strip() or "(none)", "```", ""]
    else:
        lines += ["- Git repo: no", ""]
    lines += ["## Guidance And Project Metadata", ""]
    guidance = state.get("guidance_files", [])
    if not guidance:
        lines.append("(none found)")
    for item in guidance:
        rel = item.get("path", "")
        if item.get("omitted"):
            lines.append(f"- `{rel}` omitted: {item['omitted']}")
        else:
            lines.append(f"- `{rel}` captured")
    explicit_files = state.get("explicit_workspace_files", [])
    if explicit_files:
        lines += ["", "## Projectless Workspace Files", ""]
        for item in explicit_files:
            rel = item.get("path", "")
            if item.get("omitted"):
                lines.append(f"- `{rel}` omitted: {item['omitted']}")
            else:
                lines.append(f"- `{rel}` captured")
    lines += ["", "## Omissions", ""]
    omissions = state.get("omissions", [])
    lines.extend(f"- {item}" for item in omissions) if omissions else lines.append("(none)")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Smart Handoff workspace evidence.")
    parser.add_argument("--bundle", required=True)
    args = parser.parse_args()

    bundle = Path(args.bundle).resolve()
    manifest = load_manifest(bundle)
    root = Path(manifest["cwd"]).resolve()
    omissions: list[str] = []

    git_data = collect_git(root)
    untracked = collect_untracked_summaries(root, git_data)
    guidance = find_guidance_files(root)
    explicit_workspace_files = [] if git_data.get("is_git_repo") else collect_projectless_files(root, guidance)
    if not git_data.get("is_git_repo"):
        git_data["changed_paths"] = [
            str(Path(item["path"]).resolve().relative_to(root))
            for item in guidance + explicit_workspace_files
            if item.get("path") and not item.get("omitted")
        ]

    redaction_count = int(git_data.get("redactions", 0))
    for item in untracked + guidance + explicit_workspace_files:
        redaction_count += int(item.get("redactions", 0))
        if item.get("omitted"):
            omissions.append(f"{item.get('path')}: {item.get('omitted')}")

    state = {
        "cwd": str(root),
        "git": git_data,
        "untracked_summaries": untracked,
        "guidance_files": guidance,
        "explicit_workspace_files": explicit_workspace_files,
        "omissions": omissions,
        "redaction_count": redaction_count,
    }

    write_json_private(bundle / "workspace-state.json", state)
    write_text_private(bundle / "workspace-summary.md", render_summary(root, state))

    manifest["redaction_count"] = int(manifest.get("redaction_count", 0)) + redaction_count
    manifest.setdefault("omissions", []).extend(omissions)
    if not git_data.get("is_git_repo"):
        manifest.setdefault("warnings", []).append("Workspace is not a git repository.")
    save_manifest(bundle, manifest)
    harden_bundle(bundle)
    print(f"Workspace evidence captured: {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
