"""UI test fixtures (Playwright)."""
from __future__ import annotations

import pytest


def pytest_collection_modifyitems(config, items):
    """Auto-apply @pytest.mark.ui to every test under tests/ui/."""
    for item in items:
        if "tests/ui/" in str(item.fspath).replace("\\", "/"):
            item.add_marker(pytest.mark.ui)


@pytest.fixture(scope="session")
def base_url(live_server) -> str:
    """pytest-playwright reads `base_url` for `page.goto('/')`-style relative paths."""
    return live_server
