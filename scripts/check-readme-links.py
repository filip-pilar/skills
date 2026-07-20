#!/usr/bin/env python3
"""Check that repository-relative Markdown links in README.md resolve locally."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    readme = repo / "README.md"
    errors: list[str] = []

    for raw_target in LINK_RE.findall(readme.read_text(encoding="utf-8")):
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

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("readme_links=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
