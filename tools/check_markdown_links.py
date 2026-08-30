from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)")


def find_missing_links(root: Path) -> list[str]:
    missing: list[str] = []
    for path in root.rglob("*.md"):
        relative_parts = path.relative_to(root).parts
        if any(part in {".venv", ".git", "managed_components"} for part in relative_parts):
            continue
        if any(part == "build" or part.startswith("build-") for part in relative_parts):
            continue
        for target in LINK.findall(path.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("mailto:"):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                missing.append(f"{path.relative_to(root)} -> {target}")
    return sorted(missing)


def main() -> int:
    missing = find_missing_links(ROOT)
    if missing:
        print("\n".join(missing))
        return 1
    print("Markdown links: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
