#!/usr/bin/env python3
"""Check that repository-relative Markdown links in README.md resolve locally."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
CATALOG_RE = re.compile(r"^## Skills\s*$\n(.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)
SKILL_TARGET_RE = re.compile(r"^skills/([a-z0-9]+(?:-[a-z0-9]+)*)/?$")


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    readme = repo / "README.md"
    errors: list[str] = []

    readme_text = readme.read_text(encoding="utf-8")
    for raw_target in LINK_RE.findall(readme_text):
        target = raw_target.strip().strip("<>")
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target = unquote(target.split("#", 1)[0])
        resolved = (readme.parent / target).resolve()
        try:
            resolved.relative_to(repo)
        except ValueError:
            errors.append(f"README.md link escapes the repository: {raw_target}")
            continue
        if not resolved.exists():
            errors.append(f"README.md contains a broken relative link: {raw_target}")

    public_skills = {
        path.parent.name
        for path in (repo / "skills").glob("*/SKILL.md")
        if path.is_file()
    }
    catalog_match = CATALOG_RE.search(readme_text)
    if not catalog_match:
        errors.append("README.md is missing a '## Skills' catalogue section")
    else:
        catalog_skills: list[str] = []
        for raw_target in LINK_RE.findall(catalog_match.group(1)):
            target = unquote(raw_target.strip().strip("<>").split("#", 1)[0])
            skill_match = SKILL_TARGET_RE.fullmatch(target)
            if skill_match:
                catalog_skills.append(skill_match.group(1))

        catalog_set = set(catalog_skills)
        missing = sorted(public_skills - catalog_set)
        unexpected = sorted(catalog_set - public_skills)
        duplicates = sorted(name for name in catalog_set if catalog_skills.count(name) > 1)
        if missing:
            errors.append(f"README.md catalogue omits public skills: {', '.join(missing)}")
        if unexpected:
            errors.append(f"README.md catalogue lists unknown skills: {', '.join(unexpected)}")
        if duplicates:
            errors.append(f"README.md catalogue lists skills more than once: {', '.join(duplicates)}")

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("readme_links=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
