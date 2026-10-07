import argparse
from pathlib import Path
from app.database.connection import get_connection


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--period-grading', action='store_true')
    parser.add_argument('--accounts', action='store_true')
    args = parser.parse_args()
    filename = 'migration_003_accounts.sql' if args.accounts else 'migration_002_period_grading.sql' if args.period_grading else 'migration_001_backend_validation.sql'
    migration_path = Path(__file__).with_name(filename)
    sql = migration_path.read_text(encoding="utf-8")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)

    print(f"{filename} applied successfully.")


if __name__ == "__main__":
    main()
