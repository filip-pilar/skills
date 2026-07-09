#!/usr/bin/env python3
"""Check Smart Handoff model/tool policy before synthesis."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from smart_handoff_common import harden_bundle, model_policy, write_json_private, write_text_private

CLAUDE_UNAVAILABLE_WARNING = "Claude unavailable; Smart Handoff will use the configured Codex fallback."
CODEX_NEEDS_ESCALATION_WARNING = "Required Codex fallback access appears sandbox-blocked; rerun Smart Handoff preflight with shell escalation before continuing."
LEGACY_PREFLIGHT_WARNINGS = {
    "Claude unavailable; Smart Handoff will require configured Codex fallback.",
    "Model CLI access appears sandbox-blocked; rerun Smart Handoff preflight with shell escalation before treating auth/model access as unavailable.",
}

SANDBOX_FAILURE_PATTERNS = (
    "attempt to write a readonly database",
    "readonly database",
    "operation not permitted",
    "permission denied",
    "os error 1",
    "failed to open state db",
    "failed to initialize state runtime",
    "could not create path aliases",
)

AUTH_FAILURE_PATTERNS = (
    "not logged in",
    "login required",
    "please run /login",
    "unauthorized",
)

NETWORK_FAILURE_PATTERNS = (
    "could not resolve",
    "connection refused",
    "network is unreachable",
    "operation timed out",
    "timed out",
    "timeout",
)


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def model_supports(model: str, effort: str) -> tuple[bool, str]:
    cache = codex_home() / "models_cache.json"
    data = read_json(cache, {})
    for item in data.get("models", []):
        if item.get("slug") != model:
            continue
        efforts = {entry.get("effort") for entry in item.get("supported_reasoning_levels", [])}
        if effort in efforts:
            return True, f"{model} supports {effort}"
        return False, f"{model} does not list reasoning effort {effort}"
    return False, f"{model} not found in {cache}"


def run_command(cmd: list[str], prompt: str, timeout: int) -> tuple[bool, str]:
    try:
        result = subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=timeout, check=False)
    except Exception as exc:  # noqa: BLE001 - preflight should report compactly.
        return False, str(exc)
    if result.returncode == 0:
        return True, "ok"
    detail = (result.stderr.strip() or result.stdout.strip() or f"exited {result.returncode}")
    return False, detail[:500]


def classify_failure(detail: str, *, auth_may_be_sandbox: bool, after_escalation: bool) -> str:
    lowered = detail.lower()
    if any(pattern in lowered for pattern in SANDBOX_FAILURE_PATTERNS):
        return "needs_escalation"
    if any(pattern in lowered for pattern in AUTH_FAILURE_PATTERNS):
        if auth_may_be_sandbox and not after_escalation:
            return "needs_escalation"
        return "auth_unavailable"
    if any(pattern in lowered for pattern in NETWORK_FAILURE_PATTERNS):
        if not after_escalation:
            return "needs_escalation"
        return "network_unavailable"
    return "unknown_failure"


def live_check(ok: bool, detail: str, *, auth_may_be_sandbox: bool, after_escalation: bool) -> dict[str, Any]:
    check: dict[str, Any] = {"ok": ok, "detail": detail}
    if not ok:
        check["classification"] = classify_failure(detail, auth_may_be_sandbox=auth_may_be_sandbox, after_escalation=after_escalation)
    return check


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight Smart Handoff model and tool policy.")
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--claude-bin", default=os.environ.get("SMART_HANDOFF_CLAUDE_BIN") or shutil.which("claude") or "/Users/phil/.local/bin/claude")
    parser.add_argument("--codex-bin", default=os.environ.get("SMART_HANDOFF_CODEX_BIN") or shutil.which("codex") or "/opt/homebrew/bin/codex")
    parser.add_argument("--claude-model", default=os.environ.get("SMART_HANDOFF_CLAUDE_MODEL", model_policy()["claude_model"]))
    parser.add_argument("--claude-effort", default=os.environ.get("SMART_HANDOFF_CLAUDE_EFFORT", model_policy()["claude_effort"]))
    parser.add_argument("--codex-model", default=os.environ.get("SMART_HANDOFF_CODEX_MODEL", model_policy()["codex_model"]))
    parser.add_argument("--codex-effort", default=os.environ.get("SMART_HANDOFF_CODEX_EFFORT", model_policy()["codex_effort"]))
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--skip-live", action="store_true", help="Skip live auth/model smoke calls; still validate local policy and binaries.")
    parser.add_argument("--after-escalation", action="store_true", help="Mark this run as already retried with shell escalation so real auth failures are not reported as sandbox-blocked.")
    args = parser.parse_args()

    bundle = Path(args.bundle).resolve()
    manifest_path = bundle / "manifest.json"
    manifest = read_json(manifest_path, {})
    policy = {
        "claude_model": args.claude_model,
        "claude_effort": args.claude_effort,
        "codex_model": args.codex_model,
        "codex_effort": args.codex_effort,
        "allow_partial_create": model_policy()["allow_partial_create"],
    }
    checks: dict[str, dict[str, Any]] = {}

    claude_exists = bool(args.claude_bin and Path(args.claude_bin).exists())
    checks["claude_binary"] = {"ok": claude_exists, "detail": args.claude_bin if claude_exists else f"not found: {args.claude_bin}"}
    codex_exists = bool(args.codex_bin and Path(args.codex_bin).exists())
    checks["codex_binary"] = {"ok": codex_exists, "detail": args.codex_bin if codex_exists else f"not found: {args.codex_bin}"}

    model_ok, model_detail = model_supports(args.codex_model, args.codex_effort)
    checks["codex_model_policy"] = {"ok": model_ok, "detail": model_detail}

    if not args.skip_live and claude_exists:
        ok, detail = run_command(
            [
                args.claude_bin,
                "-p",
                "--model",
                args.claude_model,
                "--effort",
                args.claude_effort,
                "--permission-mode",
                "dontAsk",
                "--tools",
                "",
            ],
            'Return exactly this JSON: {"ok":true}\n',
            args.timeout,
        )
        checks["claude_live"] = live_check(ok, detail, auth_may_be_sandbox=True, after_escalation=args.after_escalation)
    else:
        checks["claude_live"] = {"ok": None, "detail": "skipped" if args.skip_live else "claude binary unavailable"}

    if not args.skip_live and codex_exists and model_ok:
        handle = tempfile.NamedTemporaryFile(prefix=".codex-preflight-", suffix=".txt", dir=str(bundle), delete=False)
        handle.close()
        output_path = Path(handle.name)
        try:
            ok, detail = run_command(
                codex_cmd(args.codex_bin, bundle, output_path, args.codex_model, args.codex_effort),
                'Return exactly this JSON: {"ok":true}\n',
                args.timeout,
            )
        finally:
            output_path.unlink(missing_ok=True)
        checks["codex_live"] = live_check(ok, detail, auth_may_be_sandbox=True, after_escalation=args.after_escalation)
    else:
        reason = "skipped" if args.skip_live else "codex binary/model policy unavailable"
        checks["codex_live"] = {"ok": None, "detail": reason}

    blocking = [
        name
        for name in ("codex_binary", "codex_model_policy", "codex_live")
        if checks.get(name, {}).get("ok") is False
    ]
    codex_needs_escalation = [
        name
        for name in ("codex_live",)
        if checks.get(name, {}).get("classification") == "needs_escalation"
    ]
    warnings = []
    if codex_needs_escalation:
        warnings.append(CODEX_NEEDS_ESCALATION_WARNING)
    if checks["claude_binary"]["ok"] is False or (
        checks["claude_live"]["ok"] is False
    ):
        warnings.append(CLAUDE_UNAVAILABLE_WARNING)
    status = "needs_escalation" if codex_needs_escalation else "fail" if blocking else "warn" if warnings else "pass"

    manifest["model_policy"] = policy
    manifest["preflight"] = {"status": status, "checks": checks}
    manifest["warnings"] = [
        item
        for item in manifest.get("warnings", [])
        if item not in {CLAUDE_UNAVAILABLE_WARNING, CODEX_NEEDS_ESCALATION_WARNING, *LEGACY_PREFLIGHT_WARNINGS}
    ]
    if warnings:
        manifest.setdefault("warnings", []).extend(warnings)
    write_json_private(manifest_path, manifest)
    write_json_private(bundle / "preflight-status.json", {"status": status, "checks": checks, "warnings": warnings})
    if status in {"fail", "needs_escalation"}:
        error_names = codex_needs_escalation or blocking
        write_text_private(
            bundle / "preflight-error.txt",
            "\n".join(
                f"{name}: {checks[name]['detail']} [{checks[name].get('classification', 'blocking')}]"
                for name in error_names
            )
            + "\n",
        )
    else:
        (bundle / "preflight-error.txt").unlink(missing_ok=True)
    harden_bundle(bundle)
    print(f"Smart Handoff preflight: {status}")
    if status == "needs_escalation":
        return 2
    return 1 if status == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
