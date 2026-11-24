"""Fail when a template or static file would load a remote asset.

XML namespace URLs are identifiers, not requests, so they are ignored.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = (ROOT / "app" / "templates", ROOT / "app" / "static")
SCAN_SUFFIXES = {".html", ".css", ".js", ".svg"}
NAMESPACE = re.compile(r'\sxmlns(?::\w+)?="http://www\.w3\.org/[^"]*"')
REMOTE = re.compile(
    r"(?:(?:src|href)\s*=\s*|url\(\s*|@import\s+)['\"]?(?:https?:)?//",
    re.IGNORECASE,
)


def line_loads_remote_asset(line: str) -> bool:
    return REMOTE.search(NAMESPACE.sub("", line)) is not None


def find_remote_assets() -> list[str]:
    findings: list[str] = []
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*")):
            if path.suffix.lower() not in SCAN_SUFFIXES or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for number, line in enumerate(text.splitlines(), start=1):
                if line_loads_remote_asset(line):
                    findings.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    return findings


def main() -> int:
    findings = find_remote_assets()
    if findings:
        print("audit_assets: remote asset references found", file=sys.stderr)
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    print("audit_assets: no remote assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
