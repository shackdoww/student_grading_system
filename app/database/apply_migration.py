import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


def get_connection():
    load_dotenv()
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def main():
    migration_path = Path(__file__).with_name("migration_001_backend_validation.sql")
    sql = migration_path.read_text(encoding="utf-8")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)

    print("Migration 001 applied successfully.")


if __name__ == "__main__":
    main()
