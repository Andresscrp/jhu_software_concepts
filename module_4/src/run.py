import os
from src.app import create_app

def main() -> None:
    # optional: fail fast if missing
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is not set. Set it before running the app.")

    app = create_app()
    app.run(debug=True)

if __name__ == "__main__":
    main()
