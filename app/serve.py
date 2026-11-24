import os
import sys

import uvicorn

from app.db_init import main as initialize_database


def main() -> None:
    """Initialize the local database, then replace this process with uvicorn."""
    initialize_database()
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
