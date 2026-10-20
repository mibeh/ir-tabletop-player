"""Session-wide test fixtures.

DATABASE_URL is set at module load time — before any `api.*` or `src.*`
import — because pydantic-settings caches values at first instantiation.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

# --- Must run before any app import -------------------------------------
_TMP_DIR = Path(tempfile.mkdtemp(prefix="ttx-tests-"))
_DB_PATH = _TMP_DIR / "test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB_PATH}"
os.environ["LOG_LEVEL"] = "WARNING"
# ------------------------------------------------------------------------

import pytest
import pytest_asyncio


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _init_db():
    """Run Alembic migrations once per session against the temp DB."""
    from src.database import engine, init_db

    try:
        await init_db()
        yield
    finally:
        try:
            await engine.dispose()
        finally:
            shutil.rmtree(_TMP_DIR)


def pytest_sessionfinish(session, exitstatus):
    """Remove the temp directory even if setup fails before _init_db runs."""
    if _TMP_DIR.exists():
        shutil.rmtree(_TMP_DIR)


from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def api_client() -> AsyncClient:
    """In-process HTTP client backed by ASGITransport. No socket, no server."""
    from api.app import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


import socket
import subprocess
import time
import urllib.error
import urllib.request


def _free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture(scope="session")
def live_server(_init_db):
    """Run `uvicorn api.app:app` in a subprocess for the duration of the session."""
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()  # DATABASE_URL/LOG_LEVEL already set at module load.
    proc = subprocess.Popen(
        [
            "uv", "run", "uvicorn", "api.app:app",
            "--host", "127.0.0.1", "--port", str(port),
            "--log-level", "warning",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    deadline = time.time() + 30
    last_err: Exception | None = None
    while time.time() < deadline:
        if proc.poll() is not None:
            output = proc.stdout.read().decode("utf-8", errors="replace") if proc.stdout else ""
            raise RuntimeError(f"uvicorn exited early (code={proc.returncode}):\n{output}")
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=1) as r:
                if r.status == 200:
                    break
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            last_err = e
            time.sleep(0.2)
    else:
        proc.terminate()
        raise RuntimeError(f"uvicorn did not become healthy in 30s; last error: {last_err!r}")

    yield base_url

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


from tests.fixtures.seeds import (  # noqa: E402, F401
    seeded_scenario,
    seeded_exercise,
    running_exercise,
    debrief_exercise,
)
