"""
run.py

Flask entrypoint for the web container.
Binds to 0.0.0.0:8080 for Docker.
"""

from __future__ import annotations

import os

from src.app import create_app


def main() -> None:
    """Start the Flask dev server in Docker."""
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "8080"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes", "y")

    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":  # pragma: no cover
    main()