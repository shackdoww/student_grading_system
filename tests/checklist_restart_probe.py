"""Fresh-process GUI persistence check used by the isolated acceptance test."""
import os
from unittest.mock import patch

import psycopg
from psycopg import sql
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.gui.data_snapshot import load_snapshot
from app.gui.pyside_app import StudentHub
from app.services.account_service import AccountService


def main():
    schema=os.environ['CHECKLIST_SCHEMA']
    if not schema.startswith('test_checklist_') or not schema.replace('_','').isalnum():
        raise ValueError('This probe only reads the generated checklist test schema.')
    def connect():
        connection=psycopg.connect(os.environ['CHECKLIST_TEST_DSN'])
        connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
        connection.commit()
        return connection
    with patch('app.gui.data_snapshot.get_connection',connect):
        snapshot=load_snapshot()
    app=QApplication([])
    with patch('app.gui.pyside_app.load_snapshot',lambda:snapshot):
        window=StudentHub(os.environ['CHECKLIST_TEST_TOKEN'],AccountService(connect))
        window.show()
        try:
            for _ in range(300):
                if window._data_version:
                    break
                QTest.qWait(10)
            assert window._data_version
            window.show_page('grades')
            assert window.grades.grade_sheet.item(0,4).text()=='2.25'
            window.show_page('reports')
            window.reports.student.setCurrentIndex(window.reports.student.findData('2026-0001'))
            assert '2.05' in window.reports.summary.text()
        finally:
            window.close()
    print('Fresh-process grade sheet and weighted student report verified.')


if __name__=='__main__':
    main()
