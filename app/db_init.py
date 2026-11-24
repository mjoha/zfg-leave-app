from app.database import init_database


def main() -> None:
    init_database()
    print("Database schema is ready.")


if __name__ == "__main__":
    main()
