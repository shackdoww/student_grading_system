"""Opt-in PostgreSQL integration test in an isolated disposable schema."""
from pathlib import Path
from uuid import uuid4
from psycopg import sql

from app.database.connection import get_connection
from app.services.period_grading_service import PeriodGradingService


def main():
    schema = 'test_period_' + uuid4().hex
    assert schema.startswith('test_period_') and len(schema) == 44
    root = Path(__file__).resolve().parents[1]
    with get_connection() as connection:
        connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))

    def connect():
        connection = get_connection()
        connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
        connection.commit()
        return connection

    try:
        with connect() as connection:
            connection.execute((root / 'app/database/schema.sql').read_text(encoding='utf-8'))
            migration = (root / 'app/database/migration_002_period_grading.sql').read_text(encoding='utf-8')
            connection.execute(migration)
            connection.execute(migration)  # Repeatable installation.
            accounts_migration = (root / 'app/database/migration_003_accounts.sql').read_text(encoding='utf-8')
            connection.execute(accounts_migration)
            connection.execute(accounts_migration)
            checklist_migration = (root / 'app/database/migration_004_checklist.sql').read_text(encoding='utf-8')
            connection.execute(checklist_migration)
            connection.execute(checklist_migration)
            connection.execute('INSERT INTO students (student_id,first_name,last_name,email,program,status) VALUES (%s,%s,%s,%s,%s,%s)', ('S', 'Test', 'Student', 'test@example.test', 'CS', 'Active'))
            connection.execute('INSERT INTO teachers VALUES (%s,%s,%s,%s,%s,%s)', ('T', 'Test', 'Teacher', 'teacher@example.test', 'CS', 'Active'))
            connection.execute('INSERT INTO subjects VALUES (%s,%s,%s,%s,%s)', ('SUB', 'CS', 'Computing', '', 3))
            connection.execute('INSERT INTO class_offerings VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)', ('O', 'CS-A', 'Monday', 'A', '2026', '1', 'R', 'T', 'SUB'))
            connection.execute('INSERT INTO enrollments VALUES (%s,CURRENT_DATE,%s,%s,%s)', ('E', 'Active', 'S', 'O'))
            for pid in ['M', 'F']:
                connection.execute('INSERT INTO grading_periods (period_id,name,start_date,end_date,school_year,semester) VALUES (%s,%s,CURRENT_DATE,CURRENT_DATE,%s,%s)', (pid, pid, '2026', '1'))
            connection.execute('INSERT INTO grade_percentages VALUES (%s,%s,%s)', ('P', 100, 'O'))
            for pid, score in [('M', 40), ('F', 45)]:
                connection.execute('INSERT INTO grade_components VALUES (%s,%s,%s,%s,%s,%s,%s)', (pid+'C', pid+'Exam', 'Exam', 50, '', pid, 'P'))
                connection.execute('INSERT INTO grade_component_scores VALUES (%s,%s,%s,CURRENT_DATE,%s,%s)', (pid+'S', score, '', 'E', pid+'C'))
            connection.execute('INSERT INTO grades VALUES (%s,%s,%s,CURRENT_DATE,%s)', ('G', 85, 'Legacy evidence', 'E'))

        service = PeriodGradingService(connection_factory=connect)
        policy = dict(offering_id='O', midterm_period_id='M', final_period_id='F', midterm_weight=40, final_weight=60)
        weights = [dict(period_id=pid, percentage_id='P', weight=100) for pid in ['M', 'F']]
        service.save_policy(policy, weights)
        assert service.calculate_and_save('E') == dict(midterm=80, final=90, overall=86)
        # A new connection reads durable results after the save connection closed.
        with connect() as connection:
            assert float(connection.execute('SELECT overall_grade FROM period_grade_results').fetchone()[0]) == 86
        policy.update(midterm_weight=60, final_weight=40)
        service.save_policy(policy, weights)
        assert service.calculate_and_save('E')['overall'] == 84
        try:
            invalid = [dict(weights[0], weight=90), weights[1]]
            service.save_policy(policy, invalid)
            raise AssertionError('Invalid policy was accepted')
        except ValueError:
            pass
        with connect() as connection:
            assert float(connection.execute('SELECT overall_grade FROM period_grade_results').fetchone()[0]) == 84
            assert float(connection.execute('SELECT final_grade FROM grades').fetchone()[0]) == 85
            assert connection.execute('SELECT COUNT(*) FROM grade_component_scores').fetchone()[0] == 2
            assert float(connection.execute('SELECT weight FROM period_category_weights WHERE period_id=%s', ('M',)).fetchone()[0]) == 100
        from unittest.mock import patch
        from PySide6.QtWidgets import QApplication
        from PySide6.QtTest import QTest
        import app.gui.pyside_app as gui
        from app.gui.data_snapshot import load_snapshot
        from app.gui.period_grading_dialog import PeriodPolicyDialog
        from app.gui.table_output import table_data
        from tests.ui_helpers import admin_window
        with patch('app.gui.data_snapshot.get_connection', connect):
            snapshot = load_snapshot()
        app = QApplication.instance() or QApplication([])
        app.setStyle('Fusion')
        app.setStyleSheet(gui.STYLE)
        with patch.object(gui, 'load_snapshot', lambda: snapshot):
            window = admin_window()
            window.error = lambda message: (_ for _ in ()).throw(AssertionError(message))
            window.show()
            for _ in range(100):
                if window._data_version:
                    break
                QTest.qWait(10)
            window.show_page('grades')
            page = window.pages['grades']
            assert page.grade_sheet.rowCount() == 1
            assert page.roster.item(0, 0).text() == 'S'
            assert page.roster.item(0, 0).data(gui.ENROLLMENT_ROLE) == 'E'
            from unittest.mock import MagicMock
            window.grading_service = MagicMock()
            window.period_service = MagicMock()
            window.run_write = lambda operation, message: operation()
            page.roster.selectRow(0)
            page.save_grade()
            page.save_period_grades()
            window.grading_service.calculate_and_save_grade.assert_called_once_with('E')
            window.period_service.calculate_and_save.assert_called_once_with('E')
            assert not hasattr(window.enrollments, 'enrollment_id')
            headers, rows = table_data(page.grade_sheet)
            assert 'Enrollment' not in headers
            assert headers == ['No.','Student','Course','MG','FG']
            assert rows[0][headers.index('FG')] == '2.25'
            dialog = PeriodPolicyDialog(window, 'O', snapshot.records())
            read_policy, read_weights = dialog.values()
            assert read_policy['midterm_weight'] == 60
            assert len(read_weights) == 2
            dialog.close()
            window.show_page('reports')
            report = window.pages['reports']
            assert report.list.item(0, 5).text() == '2.25'
            window.close()
        from app.services.enrollment_service import EnrollmentService
        with connect() as connection:
            connection.execute('INSERT INTO students (student_id,first_name,last_name,email,program,status) VALUES (%s,%s,%s,%s,%s,%s)', ('S2', 'Another', 'Student', 'second@example.test', 'CS', 'Active'))
        with patch('app.repositories.student_repository.get_connection', connect), \
             patch('app.repositories.class_offering_repository.get_connection', connect), \
             patch('app.repositories.enrollment_repository.get_connection', connect):
            enrollment_service = EnrollmentService()
            generated = enrollment_service.enroll('S2', 'O')
            assert enrollment_service.get(generated)[0] == generated
            try:
                enrollment_service.enroll('S2', 'O')
                raise AssertionError('Duplicate enrollment was accepted')
            except ValueError as error:
                assert 'already enrolled' in str(error)
        with connect() as connection:
            assert connection.execute('SELECT enrollment_id FROM enrollments WHERE student_id=%s', ('S',)).fetchone()[0] == 'E'
        print('Automatic enrollment IDs, duplicate protection and hidden grading links passed.')
        from tests.verify_accounts import verify_accounts
        verify_accounts(connect)
        print('PySide6 period setup, grade sheet export values and student report passed.')
        print('Migration repeatability, configured calculation, persistence, recalculation, invalid-policy rollback and legacy preservation passed.')
    finally:
        # The exact generated test schema is the only deletion target.
        with get_connection() as connection:
            connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
        print('Isolated test schema removed; school records were not modified.')


if __name__ == '__main__':
    main()
