#!/usr/bin/env python3
"""Verify and, when needed, synthesize a Smart Handoff with Codex fallback."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from smart_handoff_common import DEFAULT_CODEX_EFFORT, DEFAULT_CODEX_MODEL, env_bool, harden_bundle, write_json_private, write_text_private

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

SECRET_HINT = re.compile(r"(?i)(api[_-]?key|secret|password|token|bearer)\s*[:=]\s*[A-Za-z0-9_./+=:@-]{8,}|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}")


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    write_json_private(path, data)


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


def normalize_model_handoff(data: dict[str, Any]) -> tuple[dict[str, Any], str]:
    data.pop("handoff_markdown", None)
    for key in REQUIRED_HANDOFF_KEYS:
        data.setdefault(key, [] if key in {"next_steps", "evidence_index"} else "")
    markdown = render_handoff_markdown(data)
    return data, markdown.rstrip() + "\n"


def stringify(data: Any) -> str:
    return json.dumps(data, sort_keys=True) if not isinstance(data, str) else data


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


def status_paths(workspace_state: dict[str, Any]) -> list[str]:
    git = workspace_state.get("git", {})
    paths = git.get("changed_paths", [])
    return [str(p) for p in paths]


def deterministic_verify(bundle: Path) -> dict[str, Any]:
    handoff = read_json(bundle / "handoff.json", {})
    workspace_state = read_json(bundle / "workspace-state.json", {})
    handoff_text = stringify(handoff) + "\n" + (bundle / "handoff.md").read_text(encoding="utf-8", errors="replace") if (bundle / "handoff.md").exists() else stringify(handoff)
    issues: list[str] = []
    required_repairs: list[str] = []

    if not handoff:
        issues.append("handoff.json is missing or empty.")
        required_repairs.append("Create handoff.json and handoff.md from synthesis evidence.")
    for key in REQUIRED_HANDOFF_KEYS:
        if key not in handoff:
            issues.append(f"handoff.json missing key: {key}")
            required_repairs.append(f"Add required key: {key}")
    for path in status_paths(workspace_state):
        if path and path not in handoff_text:
            issues.append(f"Changed path not represented in handoff: {path}")
    if not handoff.get("next_steps"):
        issues.append("next_steps is empty.")
        required_repairs.append("Add concrete next steps.")
    if SECRET_HINT.search(handoff_text):
        issues.append("Potential secret-like value appears in handoff.")
        required_repairs.append("Redact secret-like values.")

    critical = any("missing or empty" in item or "Potential secret" in item for item in issues)
    status = "fail" if critical else "warn" if issues else "pass"
    return {
        "status": status,
        "issues": issues,
        "required_repairs": required_repairs,
        "safe_to_create_thread": status != "fail",
        "confidence_notes": ["Deterministic verifier completed."],
    }


def minimal_handoff(bundle: Path) -> None:
    workspace_summary = (bundle / "workspace-summary.md").read_text(encoding="utf-8", errors="replace") if (bundle / "workspace-summary.md").exists() else "(missing)"
    conversation = (bundle / "conversation-brief.md").read_text(encoding="utf-8", errors="replace") if (bundle / "conversation-brief.md").exists() else "(conversation evidence not captured)"
    data = {
        "objective": "Continue the active Codex task from the Smart Handoff evidence.",
        "current_status": conversation,
        "user_preferences": (bundle / "user-preferences.md").read_text(encoding="utf-8", errors="replace") if (bundle / "user-preferences.md").exists() else "Unknown from captured evidence.",
        "important_context": workspace_summary,
        "decisions_made": (bundle / "decisions.md").read_text(encoding="utf-8", errors="replace") if (bundle / "decisions.md").exists() else "No decisions captured.",
        "files_and_changes": "Captured in workspace-summary.md and workspace-state.json; the fresh-thread prompt embeds the concise summary.",
        "commands_and_results": "See workspace-state.json. Test/build results are unknown unless captured there.",
        "validation_status": "Fallback handoff generated without external synthesis.",
        "open_questions": (bundle / "open-items.md").read_text(encoding="utf-8", errors="replace") if (bundle / "open-items.md").exists() else "Unknown from captured evidence.",
        "blockers": [],
        "next_steps": ["Use the embedded Smart Handoff content in the fresh-thread prompt.", "Verify current filesystem state.", "Continue from the captured objective and open items."],
        "do_not_redo": [],
        "evidence_index": ["manifest.json", "workspace-summary.md", "workspace-state.json", "synthesis-input.md"],
        "confidence_notes": ["Generated by deterministic fallback because external synthesis did not produce a handoff."],
    }
    write_json(bundle / "handoff.json", data)
    write_text_private(bundle / "handoff.md", render_handoff_markdown(data))


def codex_verify(bundle: Path, codex_bin: str, timeout: int, model: str, effort: str) -> dict[str, Any] | None:
    new_thread_prompt = (
        (bundle / "new-thread-prompt.md").read_text(encoding="utf-8", errors="replace")
        if (bundle / "new-thread-prompt.md").exists()
        else "(new-thread-prompt.md missing)"
    )
    prompt = (
        (skill_root() / "references" / "verifier-prompt.md").read_text(encoding="utf-8")
        + "\n\n# Bundle Path\n"
        + str(bundle)
        + "\n\n# Handoff\n"
        + (bundle / "handoff.md").read_text(encoding="utf-8", errors="replace")
        + "\n\n# New Thread Prompt\n"
        + new_thread_prompt
        + "\n\n# Workspace Summary\n"
        + (bundle / "workspace-summary.md").read_text(encoding="utf-8", errors="replace")
    )
    output_path = temp_output_path(bundle)
    cmd = codex_cmd(codex_bin, bundle, output_path, model, effort)
    try:
        result = subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=timeout, check=False)
        if result.returncode != 0:
            write_cli_error(bundle, "codex-verifier-error.txt", result)
            return None
        return extract_json(read_model_output(output_path, result.stdout))
    except Exception as exc:  # noqa: BLE001 - verifier converts this to a bundle warning.
        write_text_private(bundle / "codex-verifier-error.txt", f"Codex verifier failed: {exc}\n")
        return None
    finally:
        cleanup(output_path)


def codex_json(prompt: str, bundle: Path, codex_bin: str, timeout: int, model: str, effort: str, label: str = "codex-json") -> dict[str, Any] | None:
    output_path = temp_output_path(bundle)
    cmd = codex_cmd(codex_bin, bundle, output_path, model, effort)
    try:
        result = subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=timeout, check=False)
        if result.returncode != 0:
            write_cli_error(bundle, f"{label}-error.txt", result)
            return None
        return extract_json(read_model_output(output_path, result.stdout))
    except Exception as exc:  # noqa: BLE001 - verifier converts this to a bundle warning.
        write_text_private(bundle / f"{label}-error.txt", f"{label} failed: {exc}\n")
        return None
    finally:
        cleanup(output_path)


def temp_output_path(bundle: Path) -> Path:
    handle = tempfile.NamedTemporaryFile(prefix=".codex-last-message-", suffix=".txt", dir=str(bundle), delete=False)
    handle.close()
    return Path(handle.name)


def codex_cmd(codex_bin: str, bundle: Path, output_path: Path, model: str, effort: str) -> list[str]:
    return [
        codex_bin,
        "exec",
        "--ephemeral",
        "--model",
        model,
        "-c",
        f"model_reasoning_effort={json.dumps(effort)}",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "--output-last-message",
        str(output_path),
        "-C",
        str(bundle),
        "-",
    ]


def read_model_output(output_path: Path, stdout: str) -> str:
    if output_path.exists():
        text = output_path.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            return text
    return stdout


def cleanup(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass


def write_cli_error(bundle: Path, filename: str, result: subprocess.CompletedProcess[str]) -> None:
    stderr = (result.stderr or "").strip()
    stdout = (result.stdout or "").strip()
    lines = [
        f"returncode: {result.returncode}",
        "",
        "stderr:",
        stderr or "(empty)",
        "",
        "stdout:",
        stdout[-4000:] if stdout else "(empty)",
    ]
    write_text_private(bundle / filename, "\n".join(lines).rstrip() + "\n")


def error_summary(bundle: Path) -> list[str]:
    summaries: list[str] = []
    for filename in ("codex-verifier-error.txt", "codex-synthesis-error.txt", "codex-repair-error.txt"):
        path = bundle / filename
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        first_detail = next((line.strip() for line in text.splitlines() if line.strip() and not line.startswith(("returncode:", "stderr:", "stdout:"))), "")
        if first_detail:
            summaries.append(f"{filename}: {first_detail[:240]}")
    return summaries


def codex_synthesize(bundle: Path, codex_bin: str, timeout: int, model: str, effort: str) -> bool:
    synthesis_input = (bundle / "synthesis-input.md").read_text(encoding="utf-8", errors="replace") if (bundle / "synthesis-input.md").exists() else ""
    prompt = (
        (skill_root() / "references" / "synthesis-prompt.md").read_text(encoding="utf-8")
        + "\n\n# Evidence\n\n"
        + synthesis_input
    )
    parsed = codex_json(prompt, bundle, codex_bin, timeout, model, effort, "codex-synthesis")
    if not parsed:
        return False
    handoff, markdown = normalize_model_handoff(parsed)
    write_json(bundle / "handoff.json", handoff)
    write_text_private(bundle / "handoff.md", markdown)
    update_synthesis_status(bundle, "codex", model, effort)
    return True


def codex_repair(bundle: Path, verification: dict[str, Any], codex_bin: str, timeout: int, model: str, effort: str) -> bool:
    synthesis_input = (bundle / "synthesis-input.md").read_text(encoding="utf-8", errors="replace") if (bundle / "synthesis-input.md").exists() else ""
    current_handoff = (bundle / "handoff.md").read_text(encoding="utf-8", errors="replace") if (bundle / "handoff.md").exists() else ""
    prompt = (
        (skill_root() / "references" / "synthesis-prompt.md").read_text(encoding="utf-8")
        + "\n\n# Repair Task\n"
        + "Repair the current Smart Handoff using the verifier issues. Return the full required JSON object with handoff_markdown.\n\n"
        + "# Verifier Issues\n"
        + json.dumps(verification.get("issues", []), indent=2)
        + "\n\n# Required Repairs\n"
        + json.dumps(verification.get("required_repairs", []), indent=2)
        + "\n\n# Current Handoff\n"
        + current_handoff
        + "\n\n# Evidence\n\n"
        + synthesis_input
    )
    parsed = codex_json(prompt, bundle, codex_bin, timeout, model, effort, "codex-repair")
    if not parsed:
        return False
    handoff, markdown = normalize_model_handoff(parsed)
    write_json(bundle / "handoff.json", handoff)
    write_text_private(bundle / "handoff.md", markdown)
    return True


def update_manifest(bundle: Path, verification: dict[str, Any], model: str, effort: str, external_verified: bool, allow_partial_create: bool) -> None:
    manifest_path = bundle / "manifest.json"
    manifest = read_json(manifest_path, {})
    manifest.setdefault("model_policy", {})
    manifest["model_policy"]["codex_model"] = model
    manifest["model_policy"]["codex_effort"] = effort
    manifest["model_policy"]["allow_partial_create"] = allow_partial_create
    manifest["verification_status"] = verification.get("status", "unknown")
    manifest["handoff_quality"] = verification.get("handoff_quality", "unknown")
    manifest["degraded_reasons"] = verification.get("degraded_reasons", [])
    manifest["verification_engine"] = "codex" if external_verified else "deterministic"
    manifest["verification_model"] = model if external_verified else None
    manifest["verification_effort"] = effort if external_verified else None
    if verification.get("issues"):
        manifest.setdefault("warnings", []).extend(str(x) for x in verification["issues"])
    write_json(manifest_path, manifest)


def update_synthesis_status(bundle: Path, status: str, model: str | None = None, effort: str | None = None) -> None:
    manifest_path = bundle / "manifest.json"
    manifest = read_json(manifest_path, {})
    manifest["synthesis_status"] = status
    manifest["synthesis_engine"] = status
    manifest["synthesis_model"] = model
    manifest["synthesis_effort"] = effort
    write_json(manifest_path, manifest)


def synthesis_status(bundle: Path) -> str:
    return str(read_json(bundle / "manifest.json", {}).get("synthesis_status", "unknown"))


def quality_for(bundle: Path, verification: dict[str, Any], external_verified: bool, deterministic_fallback: bool, allow_partial_create: bool) -> dict[str, Any]:
    reasons: list[str] = []
    status = verification.get("status", "unknown")
    synthesis = synthesis_status(bundle)
    model_synthesized = synthesis in {"claude", "codex"}

    if deterministic_fallback:
        reasons.append("handoff_generated_by_deterministic_fallback")
    if not model_synthesized:
        reasons.append("model_synthesis_unavailable")
    if not external_verified:
        reasons.append("model_verification_unavailable")
    if status == "warn":
        reasons.append("verification_warnings_present")
    if status == "fail":
        reasons.append("verification_failed")

    if status == "fail":
        quality = "failed"
        safe = False
    elif model_synthesized and external_verified and status == "pass":
        quality = "verified"
        safe = True
    elif model_synthesized and status in {"pass", "warn"}:
        quality = "partial"
        safe = allow_partial_create and verification.get("safe_to_create_thread") is not False
        if not allow_partial_create:
            reasons.append("partial_create_not_allowed")
    elif deterministic_fallback and not external_verified:
        quality = "failed"
        safe = False
        reasons.append("deterministic_only_handoff_not_safe_for_automatic_thread_creation")
    else:
        quality = "degraded"
        safe = False

    updated = dict(verification)
    updated["issues"] = list(verification.get("issues", []))
    updated["required_repairs"] = list(verification.get("required_repairs", []))
    updated["confidence_notes"] = list(verification.get("confidence_notes", []))
    updated["handoff_quality"] = quality
    updated["degraded_reasons"] = sorted(set(reasons))
    updated["safe_to_create_thread"] = safe
    if quality in {"failed", "degraded"} and "Smart Handoff quality is degraded." not in updated.get("issues", []):
        updated.setdefault("issues", []).append("Smart Handoff quality is degraded.")
        updated["status"] = "fail"
    if quality == "partial" and not safe:
        updated.setdefault("issues", []).append("Partial Smart Handoff requires SMART_HANDOFF_ALLOW_PARTIAL_CREATE=1 before automatic thread creation.")
        updated["status"] = "fail"
    return updated


def refresh_handoff_validation(bundle: Path, verification: dict[str, Any]) -> None:
    handoff_path = bundle / "handoff.json"
    if not handoff_path.exists():
        return
    handoff = read_json(handoff_path, {})
    handoff["validation_status"] = {
        "status": verification.get("status", "unknown"),
        "safe_to_create_thread": verification.get("safe_to_create_thread"),
        "issues": verification.get("issues", []),
        "required_repairs": verification.get("required_repairs", []),
        "source": "Smart Handoff verifier",
    }
    write_json(handoff_path, handoff)
    write_text_private(bundle / "handoff.md", render_handoff_markdown(handoff))


def ensure_new_thread_prompt(bundle: Path) -> bool:
    script = skill_root() / "scripts" / "build_new_thread_prompt.py"
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--bundle", str(bundle)],
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        if result.returncode == 0:
            return True
        write_text_private(
            bundle / "new-thread-prompt-error.txt",
            (result.stderr.strip() or result.stdout.strip() or f"prompt builder exited {result.returncode}") + "\n",
        )
    except Exception as exc:  # noqa: BLE001 - verifier reports this as unsafe.
        write_text_private(bundle / "new-thread-prompt-error.txt", f"Prompt builder failed: {exc}\n")
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Smart Handoff artifacts.")
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--codex-bin", default=os.environ.get("SMART_HANDOFF_CODEX_BIN") or shutil.which("codex") or "/opt/homebrew/bin/codex")
    parser.add_argument("--codex-model", default=os.environ.get("SMART_HANDOFF_CODEX_MODEL", DEFAULT_CODEX_MODEL))
    parser.add_argument("--codex-effort", default=os.environ.get("SMART_HANDOFF_CODEX_EFFORT", DEFAULT_CODEX_EFFORT))
    parser.add_argument("--allow-partial-create", action="store_true", default=env_bool("SMART_HANDOFF_ALLOW_PARTIAL_CREATE", False))
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--skip-external", action="store_true")
    args = parser.parse_args()

    bundle = Path(args.bundle).resolve()
    external_available = bool(args.codex_bin and Path(args.codex_bin).exists())
    deterministic_fallback = False
    if not (bundle / "handoff.json").exists() or not (bundle / "handoff.md").exists():
        if args.skip_external or not external_available or not codex_synthesize(bundle, args.codex_bin, args.timeout, args.codex_model, args.codex_effort):
            minimal_handoff(bundle)
            update_synthesis_status(bundle, "deterministic")
            manifest = read_json(bundle / "manifest.json", {})
            manifest["fallback_reason"] = "codex_synthesis_unavailable"
            write_json(bundle / "manifest.json", manifest)
            deterministic_fallback = True

    prompt_ready = ensure_new_thread_prompt(bundle)
    verification = deterministic_verify(bundle)
    if not prompt_ready:
        verification["status"] = "fail"
        verification["safe_to_create_thread"] = False
        verification.setdefault("issues", []).append("new-thread-prompt.md could not be built before verification.")
        verification.setdefault("required_repairs", []).append("Build a self-contained new-thread-prompt.md after handoff synthesis.")
    external = None
    if prompt_ready and not args.skip_external and external_available:
        external = codex_verify(bundle, args.codex_bin, args.timeout, args.codex_model, args.codex_effort)
    external_verified = external is not None
    if external and external.get("status") in {"pass", "warn", "fail"}:
        merged = external
        merged.setdefault("confidence_notes", []).append("Codex verifier completed.")
        if verification["status"] == "fail":
            merged["status"] = "fail"
            merged["safe_to_create_thread"] = False
            merged.setdefault("issues", []).extend(verification["issues"])
    else:
        merged = verification
        if not args.skip_external:
            merged.setdefault("confidence_notes", []).append("External Codex verifier unavailable; deterministic checks used.")
            merged.setdefault("confidence_notes", []).extend(error_summary(bundle))

    if (
        not args.skip_external
        and external_available
        and merged.get("status") in {"warn", "fail"}
        and merged.get("required_repairs")
        and codex_repair(bundle, merged, args.codex_bin, args.timeout, args.codex_model, args.codex_effort)
    ):
        prompt_ready = ensure_new_thread_prompt(bundle)
        repaired = deterministic_verify(bundle)
        repaired_external = codex_verify(bundle, args.codex_bin, args.timeout, args.codex_model, args.codex_effort) if prompt_ready else None
        if repaired_external and repaired_external.get("status") in {"pass", "warn", "fail"}:
            external_verified = True
            merged = repaired_external
            merged.setdefault("confidence_notes", []).append("Codex repair pass completed.")
            merged.setdefault("confidence_notes", []).append("External re-verification completed after repair.")
            if repaired.get("status") == "fail":
                merged["status"] = "fail"
                merged["safe_to_create_thread"] = False
                merged.setdefault("issues", []).extend(repaired.get("issues", []))
        elif repaired.get("status") == "pass" and prompt_ready:
            merged = {
                "status": "pass",
                "issues": [],
                "required_repairs": [],
                "safe_to_create_thread": True,
                "confidence_notes": [
                    "Codex repair pass completed.",
                    "Deterministic re-verification passed.",
                    "External re-verification unavailable after repair.",
                    *error_summary(bundle),
                ],
            }
        else:
            merged.setdefault("confidence_notes", []).append("Codex repair pass completed; residual verification warnings remain.")

    merged = quality_for(bundle, merged, external_verified, deterministic_fallback, args.allow_partial_create)

    write_json(bundle / "verification.json", merged)
    lines = [
        "# Smart Handoff Verification",
        "",
        f"- Status: `{merged.get('status')}`",
        f"- Handoff quality: `{merged.get('handoff_quality')}`",
        f"- Safe to create thread: `{merged.get('safe_to_create_thread')}`",
        "",
    ]
    lines.append("## Degraded Reasons")
    lines.extend(f"- {item}" for item in merged.get("degraded_reasons", []) or ["(none)"])
    lines += [""]
    lines.append("## Issues")
    lines.extend(f"- {item}" for item in merged.get("issues", []) or ["(none)"])
    lines += ["", "## Required Repairs"]
    lines.extend(f"- {item}" for item in merged.get("required_repairs", []) or ["(none)"])
    lines += ["", "## Confidence Notes"]
    lines.extend(f"- {item}" for item in merged.get("confidence_notes", []) or ["(none)"])
    write_text_private(bundle / "verification.md", "\n".join(lines) + "\n")
    refresh_handoff_validation(bundle, merged)
    update_manifest(bundle, merged, args.codex_model, args.codex_effort, external_verified, args.allow_partial_create)
    harden_bundle(bundle)
    print(f"Verification status: {merged.get('status')}")
    return 1 if merged.get("status") == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
