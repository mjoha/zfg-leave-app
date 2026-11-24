from alembic.runtime.migration import MigrationContext

from app.database import get_engine, init_database


def main() -> None:
    init_database()
    with get_engine().connect() as connection:
        revision = MigrationContext.configure(connection).get_current_revision()
    print(f"Database schema is ready at revision {revision}.")


if __name__ == "__main__":
    main()
