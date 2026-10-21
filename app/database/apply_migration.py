"""Unified safe installer; --preflight makes no schema or record changes."""
import argparse
import json
from app.database.connection import get_connection
from app.database.migrate_legacy import migrate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all',action='store_true',help='Install or migrate to the current schema.')
    parser.add_argument('--preflight',action='store_true',help='Report conversion blockers without changing data.')
    for name in ('period-grading','accounts','checklist'):
        parser.add_argument('--'+name,action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    with get_connection() as connection:
        report=migrate(connection,preflight_only=args.preflight)
    print(json.dumps(report,indent=2,default=str))


if __name__=='__main__':
    main()
