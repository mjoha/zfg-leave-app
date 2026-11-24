"""CI-equivalent checks that stay on this machine.

No network, no database server, and no external service. The command uses the
current interpreter, compiles the application, runs Ruff and mypy, and runs pytest.
"""

from __future__ import annotations

import compileall
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require_python_312() -> None:
    version = sys.version_info
    if version[:2] != (3, 12):
        found = ".".join(str(part) for part in version[:3])
        print(f"ci_local: Python 3.12 is required, found {found}", file=sys.stderr)
        raise SystemExit(1)


def main() -> int:
    require_python_312()
    print(f"ci_local: Python {sys.version.split()[0]}", flush=True)
    print("ci_local: compile app", flush=True)
    if not compileall.compile_dir(str(ROOT / "app"), quiet=1):
        print("ci_local: failed", file=sys.stderr)
        return 1
    print("ci_local: compile tests", flush=True)
    if not compileall.compile_dir(str(ROOT / "tests"), quiet=1):
        print("ci_local: failed", file=sys.stderr)
        return 1
    print("ci_local: ruff check", flush=True)
    ruff = subprocess.run([sys.executable, "-m", "ruff", "check", "app", "tests", "scripts"], cwd=ROOT)
    if ruff.returncode != 0:
        print("ci_local: failed", file=sys.stderr)
        return ruff.returncode
    print("ci_local: mypy", flush=True)
    mypy = subprocess.run([sys.executable, "-m", "mypy", "app"], cwd=ROOT)
    if mypy.returncode != 0:
        print("ci_local: failed", file=sys.stderr)
        return mypy.returncode
    print("ci_local: pytest -q", flush=True)
    completed = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
    if completed.returncode != 0:
        print("ci_local: failed", file=sys.stderr)
        return completed.returncode
    print("ci_local: passed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
