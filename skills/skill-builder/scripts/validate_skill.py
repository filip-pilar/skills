#!/usr/bin/env python3
"""Run deterministic structural checks for a Codex skill package."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

try:
    import yaml
except ImportError:  # pragma: no cover - environment-specific dependency failure
    print("ERROR: PyYAML is required; use the Python runtime bundled with Codex.", file=sys.stderr)
    raise SystemExit(2)


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
PLACEHOLDER_RE = re.compile(r"\[TODO(?::|\])", re.IGNORECASE)
SKILL_COMMAND_RE = re.compile(r"\$[a-z0-9]+(?:-[a-z0-9]+)*", re.IGNORECASE)
INVOCATION_POLICY_LABEL_RE = re.compile(r"\b(?:(?:explicit|manual)-only|user-invoked)\b", re.IGNORECASE)
INVOCATION_INSTRUCTION_RE = re.compile(
    r"(?:"
    r"\b(?:bare\s+invocation|re-?invocation|(?:invoke|re-?invoke|trigger|run|call|use)\s+(?:this|the)\s+skill)\b"
    r"|(?:\A|[.!?]\s+)(?:only\s+)?(?:invoke|re-?invoke|trigger|run|call|use)"
    r"(?:\s+(?:this|the)\s+skill)?\s+(?:only\s+)?when\b"
    r")",
    re.IGNORECASE,
)
ALLOWED_FRONTMATTER_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}
DEVELOPMENT_DEBRIS_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
DEVELOPMENT_ONLY_DIRS = {"evals"}
DEVELOPMENT_DEBRIS_FILES = {".DS_Store"}
DEVELOPMENT_DEBRIS_SUFFIXES = {".pyc", ".pyo"}
RESOURCE_DIRS = {"assets", "references", "scripts"}


def load_yaml(path: Path, text: str, errors: list[str]) -> object:
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        errors.append(f"{path}: invalid YAML: {exc}")
        return None


def check_markdown_links(path: Path, skill_dir: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for raw_target in LINK_RE.findall(text):
        target = raw_target.strip().strip("<>")
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target = unquote(target.split("#", 1)[0])
        if not target or Path(target).is_absolute():
            continue
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(skill_dir)
        except ValueError:
            errors.append(f"{path}: relative link escapes the skill directory: {raw_target}")
            continue
        if not resolved.exists():
            errors.append(f"{path}: broken relative link: {raw_target}")


def repeated_paragraphs(body: str) -> list[str]:
    seen: dict[str, str] = {}
    repeats: list[str] = []
    for paragraph in re.split(r"\n\s*\n", body):
        normalized = re.sub(r"\s+", " ", paragraph.strip().lower())
        if len(normalized) < 80 or normalized.startswith("```"):
            continue
        if normalized in seen:
            repeats.append(paragraph.strip().splitlines()[0][:80])
        else:
            seen[normalized] = paragraph
    return repeats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_directory", type=Path)
    args = parser.parse_args()

    skill_dir = args.skill_directory.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.is_file():
        print(f"ERROR: SKILL.md not found under {skill_dir}", file=sys.stderr)
        return 1

    content = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    if not match:
        errors.append(f"{skill_md}: missing or malformed YAML frontmatter")
        frontmatter: object = None
        body = content
    else:
        frontmatter = load_yaml(skill_md, match.group(1), errors)
        body = content[match.end() :]

    name = ""
    description = ""
    if isinstance(frontmatter, dict):
        unexpected = [key for key in frontmatter if not isinstance(key, str) or key not in ALLOWED_FRONTMATTER_KEYS]
        if unexpected:
            labels = ", ".join(sorted(str(key) for key in unexpected))
            allowed = ", ".join(sorted(ALLOWED_FRONTMATTER_KEYS))
            errors.append(f"{skill_md}: unexpected frontmatter key(s): {labels}; allowed: {allowed}")
        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            errors.append(f"{skill_md}: name must use lowercase hyphen-case")
            name = ""
        elif len(name) > 64:
            errors.append(f"{skill_md}: name exceeds 64 characters")
        elif name != skill_dir.name:
            errors.append(f"{skill_md}: name '{name}' does not match folder '{skill_dir.name}'")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{skill_md}: description must be a non-empty string")
            description = ""
        elif "<" in description or ">" in description:
            errors.append(f"{skill_md}: description cannot contain angle brackets")
        elif len(description) > 1024:
            errors.append(f"{skill_md}: description exceeds 1024 characters")
    elif match:
        errors.append(f"{skill_md}: frontmatter must be a YAML mapping")

    if not body.strip():
        errors.append(f"{skill_md}: instruction body is empty")
    if PLACEHOLDER_RE.search(content):
        errors.append(f"{skill_md}: unresolved TODO placeholder")

    metadata_path = skill_dir / "agents" / "openai.yaml"
    if metadata_path.exists():
        metadata = load_yaml(metadata_path, metadata_path.read_text(encoding="utf-8"), errors)
        if isinstance(metadata, dict):
            interface = metadata.get("interface", {})
            policy = metadata.get("policy", {})
            if not isinstance(interface, dict):
                errors.append(f"{metadata_path}: interface must be a mapping")
                interface = {}
            if not isinstance(policy, dict):
                errors.append(f"{metadata_path}: policy must be a mapping")
                policy = {}
            display = interface.get("display_name")
            if not isinstance(display, str) or not display.strip():
                errors.append(f"{metadata_path}: interface.display_name must be a non-empty string")
            short = interface.get("short_description")
            if not isinstance(short, str) or not short.strip():
                errors.append(f"{metadata_path}: interface.short_description must be a non-empty string")
            else:
                if not 25 <= len(short) <= 64:
                    warnings.append(f"{metadata_path}: short_description should be 25-64 characters")
                if SKILL_COMMAND_RE.search(short):
                    errors.append(
                        f"{metadata_path}: short_description must summarize capability, not contain a $skill command"
                    )
                if INVOCATION_POLICY_LABEL_RE.search(short) or INVOCATION_INSTRUCTION_RE.search(short):
                    errors.append(
                        f"{metadata_path}: short_description must summarize capability, not invocation policy or instructions"
                    )

            implicit = policy.get("allow_implicit_invocation", True)
            if not isinstance(implicit, bool):
                errors.append(f"{metadata_path}: allow_implicit_invocation must be boolean")

            prompt = interface.get("default_prompt")
            if not isinstance(prompt, str) or not prompt.strip():
                errors.append(f"{metadata_path}: interface.default_prompt must be a non-empty string")
            elif implicit is False and name and f"${name}" not in prompt:
                errors.append(f"{metadata_path}: manual-only default_prompt must mention ${name}")

            if isinstance(description, str) and description:
                if SKILL_COMMAND_RE.search(description):
                    errors.append(
                        f"{skill_md}: description must not contain $skill commands; "
                        "put explicit invocation in interface.default_prompt"
                    )
                if INVOCATION_POLICY_LABEL_RE.search(description):
                    errors.append(
                        f"{skill_md}: description must not restate invocation policy; "
                        "use policy.allow_implicit_invocation"
                    )
                if implicit is False and INVOCATION_INSTRUCTION_RE.search(description):
                    errors.append(
                        f"{skill_md}: manual-only description must not encode invocation or re-entry behavior; "
                        "put explicit invocation in interface.default_prompt and runtime behavior in the SKILL.md body"
                    )

    markdown_files = [skill_md]
    references = skill_dir / "references"
    if references.exists():
        markdown_files.extend(sorted(references.rglob("*.md")))
    for markdown in markdown_files:
        check_markdown_links(markdown, skill_dir, errors)
        if markdown != skill_md and PLACEHOLDER_RE.search(markdown.read_text(encoding="utf-8")):
            errors.append(f"{markdown}: unresolved TODO placeholder")

    for path in skill_dir.rglob("*"):
        relative = path.relative_to(skill_dir)
        if path.is_dir() and path.name in DEVELOPMENT_ONLY_DIRS:
            errors.append(f"{relative}: development evaluation directory must live outside the distributable skill")
            continue
        if path.is_dir() and path.name in DEVELOPMENT_DEBRIS_DIRS:
            errors.append(f"{relative}: development cache directory must not ship")
            continue
        if path.is_file() and (
            path.name in DEVELOPMENT_DEBRIS_FILES or path.suffix.lower() in DEVELOPMENT_DEBRIS_SUFFIXES
        ):
            if not any(part in DEVELOPMENT_DEBRIS_DIRS for part in relative.parts[:-1]):
                errors.append(f"{relative}: generated development artifact must not ship")
        if path.is_symlink():
            if not path.exists():
                errors.append(f"{path}: broken symlink")
            else:
                try:
                    path.resolve().relative_to(skill_dir)
                except ValueError:
                    errors.append(f"{path}: symlink escapes the skill directory")

    text_sources: dict[Path, str] = {}
    for path in skill_dir.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            text_sources[path] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

    resources: list[Path] = []
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(skill_dir)
        if not relative.parts or relative.parts[0] not in RESOURCE_DIRS:
            continue
        if relative.parts[0] == "scripts" and path.name.startswith(("test_", "mock_")):
            continue
        resources.append(path)

    reachable = {skill_md}
    changed = True
    while changed:
        changed = False
        reachable_text = "\n".join(text_sources.get(path, "") for path in reachable)
        for path in resources:
            relative = path.relative_to(skill_dir)
            if path not in reachable and (relative.as_posix() in reachable_text or path.name in reachable_text):
                reachable.add(path)
                changed = True

    for path in resources:
        if path not in reachable:
            relative = path.relative_to(skill_dir)
            errors.append(f"{relative}: bundled resource is not reachable from SKILL.md")

    for repeated in repeated_paragraphs(body):
        warnings.append(f"{skill_md}: repeated paragraph beginning: {repeated}")

    root_words = len(WORD_RE.findall(content))
    reference_words = sum(
        len(WORD_RE.findall(path.read_text(encoding="utf-8")))
        for path in sorted(references.rglob("*.md"))
    ) if references.exists() else 0

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"SKILL.md words: {root_words}")
    print(f"Conditional reference words: {reference_words}")

    if errors:
        print(f"Validation failed with {len(errors)} error(s) and {len(warnings)} warning(s).")
        return 1
    print(f"Validation passed with {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
