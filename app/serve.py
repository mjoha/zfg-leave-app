import os
import sys

from app.seed import seed_database


def main() -> None:
    """Initialize the local database, load demo data, then serve HTTP."""
    seed_database()
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
    )


if __name__ == "__main__":
    main()
