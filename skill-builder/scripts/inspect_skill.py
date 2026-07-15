#!/usr/bin/env python3
"""Inventory a Codex skill and report context-relevant size without modifying it."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


TEXT_SUFFIXES = {
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".txt",
    ".py",
    ".sh",
    ".js",
    ".mjs",
    ".ts",
}
WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def word_count(path: Path) -> int | None:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return None
    try:
        return len(WORD_RE.findall(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError):
        return None


def category(relative: Path) -> str:
    if relative.as_posix() == "SKILL.md":
        return "root"
    if relative.parts[0] == "references":
        return "conditional"
    if relative.parts[0] == "evals":
        return "development"
    if relative.parts[0] == "agents":
        return "metadata"
    if relative.parts[0] == "scripts":
        return "script"
    if relative.parts[0] == "assets":
        return "asset"
    return "other"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_directory", type=Path)
    parser.add_argument(
        "--load",
        action="append",
        default=[],
        metavar="RELATIVE_PATH",
        help="add a selectively loaded file to the reported runtime path; repeat as needed",
    )
    args = parser.parse_args()

    skill_dir = args.skill_directory.expanduser().resolve()
    if not (skill_dir / "SKILL.md").is_file():
        parser.error(f"SKILL.md not found under {skill_dir}")

    loaded: list[Path] = []
    for raw_path in args.load:
        path = (skill_dir / raw_path).resolve()
        try:
            relative = path.relative_to(skill_dir)
        except ValueError:
            parser.error(f"loaded path escapes the skill directory: {raw_path}")
        if not path.is_file():
            parser.error(f"loaded path is not a file: {raw_path}")
        if relative.as_posix() != "SKILL.md" and relative not in loaded:
            loaded.append(relative)

    rows: list[tuple[str, Path, int | None, int]] = []
    totals: dict[str, int] = {}
    for path in sorted(skill_dir.rglob("*")):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(skill_dir)
        kind = category(relative)
        words = word_count(path)
        size = path.stat().st_size
        rows.append((kind, relative, words, size))
        if words is not None:
            totals[kind] = totals.get(kind, 0) + words

    print(f"Skill: {skill_dir}")
    print("category     words   bytes  path")
    for kind, relative, words, size in rows:
        word_label = "-" if words is None else str(words)
        link = ""
        source = skill_dir / relative
        if source.is_symlink():
            target = source.readlink()
            link = f" -> {target}"
        print(f"{kind:12} {word_label:>6} {size:>7}  {relative}{link}")

    print("\nWord totals by loading role:")
    for kind in ("root", "conditional", "metadata", "script", "development", "asset", "other"):
        if kind in totals:
            print(f"- {kind}: {totals[kind]}")

    root_words = word_count(skill_dir / "SKILL.md") or 0
    selected_words = root_words
    selected_bytes = (skill_dir / "SKILL.md").stat().st_size
    selected_labels = ["SKILL.md"]
    for relative in loaded:
        words = word_count(skill_dir / relative)
        if words is None:
            parser.error(f"loaded path is not countable text: {relative}")
        selected_words += words
        selected_bytes += (skill_dir / relative).stat().st_size
        selected_labels.append(relative.as_posix())

    print("\nSelected runtime loading path:")
    print(f"- words: {selected_words}")
    print(f"- bytes: {selected_bytes}")
    print(f"- files: {', '.join(selected_labels)}")
    if totals.get("conditional", 0):
        print(f"- all conditional references (inventory, not one implied path): {totals['conditional']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
