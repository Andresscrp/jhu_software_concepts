"""
run.py

Entry point for running the Flask application locally.

This module checks that DATABASE_URL is set, creates the Flask app, and starts the
development server.
"""

import os

from src.app import create_app


def main() -> None:
    """
    Run the Flask development server.

    Raises:
        RuntimeError: If DATABASE_URL is not set in the environment.
    """
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is not set. Set it before running the app.")

    app = create_app()
    app.run(debug=True)


if __name__ == "__main__":
    main()
