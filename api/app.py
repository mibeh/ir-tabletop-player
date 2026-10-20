"""IR Tabletop Exercise Platform — FastAPI Application."""
from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.database import init_db

from .routes import exercises, scenarios

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    logger.info("Database initialised")
    yield


app = FastAPI(
    title="IR Tabletop Exercise Platform",
    description="Incident response tabletop exercise player",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(exercises.router)
app.include_router(scenarios.router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/present.html", include_in_schema=False)
async def present() -> FileResponse:
    return FileResponse(os.path.join(static_dir, "present.html"))


@app.get("/facilitate.html", include_in_schema=False)
async def facilitate() -> FileResponse:
    return FileResponse(os.path.join(static_dir, "facilitate.html"))


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
