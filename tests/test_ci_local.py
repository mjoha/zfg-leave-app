import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ci_local.py"
_SPEC = importlib.util.spec_from_file_location("ci_local", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
ci_local = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ci_local)


def test_ci_command_accepts_python_312():
    ci_local.require_python_312()


def test_ci_command_rejects_other_python_versions(monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 10, 6, "final", 0))
    with pytest.raises(SystemExit) as caught:
        ci_local.require_python_312()
    assert caught.value.code == 1
