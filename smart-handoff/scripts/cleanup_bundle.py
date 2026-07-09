#!/usr/bin/env python3
"""Safely delete a temporary Smart Handoff scratch bundle."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path


def allowed_roots() -> list[Path]:
    roots = [
        Path(os.environ.get("SMART_HANDOFF_TMPDIR", "/private/tmp")).resolve() / "codex-smart-handoff",
        Path(tempfile.gettempdir()).resolve() / "codex-smart-handoff",
        Path("/private/tmp").resolve() / "codex-smart-handoff",
    ]
    unique: list[Path] = []
    for root in roots:
        if root not in unique:
            unique.append(root)
    return unique


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def read_manifest(bundle: Path) -> dict:
    path = bundle / "manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete a temporary Smart Handoff scratch bundle.")
    parser.add_argument("--bundle", required=True)
    args = parser.parse_args()

    bundle = Path(args.bundle).resolve()
    manifest = read_manifest(bundle)
    if not bundle.exists():
        print(f"Scratch bundle already absent: {bundle}")
        return 0
    if not any(is_relative_to(bundle, root) for root in allowed_roots()):
        print(f"Refusing to clean non-temporary bundle path: {bundle}")
        return 2
    if manifest.get("bundle_storage") != "temporary_scratch":
        print(f"Refusing to clean bundle without temporary_scratch manifest marker: {bundle}")
        return 2
    if bundle.name in {"", ".", ".."} or len(bundle.name) < 8:
        print(f"Refusing to clean suspicious bundle path: {bundle}")
        return 2

    shutil.rmtree(bundle)
    print(f"Smart Handoff scratch bundle cleaned: {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
