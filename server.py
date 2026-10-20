"""IR Tabletop Exercise Platform — Server Entry Point

Run with:
    python3 server.py

Or with auto-reload for development:
    python3 server.py --reload
"""
from __future__ import annotations

import argparse
import logging
import sys

import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="IR Tabletop Exercise Platform")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    logger.info("Starting IR Tabletop Platform on http://%s:%d", args.host, args.port)
    logger.info("Admin UI: http://localhost:%d", args.port)
    logger.info("API docs: http://localhost:%d/docs", args.port)

    uvicorn.run(
        "api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
