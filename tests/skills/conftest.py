"""Load hyphen-named skill scripts by file path (they are not import packages)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPTS = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "ttx-report-generator"
    / "scripts"
)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / f"{name}.py")
    assert spec and spec.loader, f"cannot load {name}"
    module = importlib.util.module_from_spec(spec)
    # Register before exec_module so dataclasses can resolve string annotations
    # (Python 3.13 does sys.modules[cls.__module__].__dict__ during @dataclass).
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def vtt_parser():
    return _load("vtt_parser")


@pytest.fixture
def render_aar():
    return _load("render_aar")
