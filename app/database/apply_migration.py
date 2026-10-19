import argparse
from pathlib import Path
from app.database.connection import get_connection


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--period-grading', action='store_true')
    parser.add_argument('--accounts', action='store_true')
    parser.add_argument('--checklist', action='store_true')
    parser.add_argument('--all', action='store_true', help='Apply every additive migration in order.')
    args = parser.parse_args()
    filename = 'migration_004_checklist.sql' if args.checklist else 'migration_003_accounts.sql' if args.accounts else 'migration_002_period_grading.sql' if args.period_grading else 'migration_001_backend_validation.sql'
    paths = sorted(Path(__file__).parent.glob('migration_*.sql')) if args.all else [Path(__file__).with_name(filename)]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for path in paths:
                cursor.execute(path.read_text(encoding='utf-8'))

    print('Applied: ' + ', '.join(path.name for path in paths))


if __name__ == "__main__":
    main()
