"""Every static page loads without uncaught JS errors."""
from __future__ import annotations


def _collect_console_errors(page):
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    return errors


def test_index_loads_without_errors(page, base_url):
    errors = _collect_console_errors(page)
    response = page.goto(f"{base_url}/")
    assert response.status == 200
    page.wait_for_load_state("networkidle")
    assert errors == [], f"console/page errors on /: {errors}"


def test_present_html_loads_without_errors(page, base_url):
    errors = _collect_console_errors(page)
    response = page.goto(f"{base_url}/present.html")
    assert response.status == 200
    page.wait_for_load_state("networkidle")
    assert errors == [], f"console/page errors on /present.html: {errors}"


def test_facilitate_html_loads_without_errors(page, base_url):
    errors = _collect_console_errors(page)
    response = page.goto(f"{base_url}/facilitate.html")
    assert response.status == 200
    page.wait_for_load_state("networkidle")
    assert errors == [], f"console/page errors on /facilitate.html: {errors}"
