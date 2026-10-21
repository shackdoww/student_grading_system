from pathlib import Path
import pytest
from psycopg import sql
from tests.database_helpers import isolated_database

FIXTURES=Path(__file__).parent/'fixtures/legacy_database'


def legacy(connect, grouped=1):
    with connect() as c:
        c.execute((FIXTURES/'schema.sql').read_text())
        for f in sorted(FIXTURES.glob('migration_*.sql')):
            c.execute(f.read_text())
        c.execute("INSERT INTO students(student_id,first_name,last_name,email,program,status) VALUES ('S','Juan','Dela Cruz',NULL,'BSCS','Active')")
        c.execute("INSERT INTO teachers VALUES ('T','Maria','Santos',NULL,'IT','Active')")
        c.execute("INSERT INTO subjects VALUES ('U','CS','OOP',NULL,3)")
        c.execute("INSERT INTO class_offerings VALUES ('C','CS-A','MWF','A','2026','1st','R','T','U')")
        c.execute("INSERT INTO grading_periods(period_id,name,start_date,end_date,school_year,semester) VALUES ('M','Midterm','2026-01-01','2026-06-01','2026','1st')")
        c.execute("INSERT INTO enrollments VALUES ('E',CURRENT_DATE,'Enrolled','S','C')")
        c.execute("INSERT INTO grade_percentages VALUES ('W',100,'C')")
        for i in range(grouped):
            c.execute("INSERT INTO grade_components VALUES (%s,%s,'Exam',100,NULL,'M','W')",(f'X{i}',f'Exam {i}'))
            c.execute("INSERT INTO grade_component_scores VALUES (%s,80,NULL,CURRENT_DATE,'E',%s)",(f'S{i}',f'X{i}'))
        c.execute("INSERT INTO grades VALUES ('G',80,'Legacy',CURRENT_DATE,'E')")


def test_fresh_and_repeat_install():
    from app.database.migrate_legacy import migrate
    with isolated_database(install=False) as connect:
        with connect() as c:
            assert migrate(c)['status']=='installed'
        with connect() as c:
            assert migrate(c)['status']=='current'
            assert c.execute('SELECT count(*) FROM student').fetchone()[0]==0


@pytest.mark.parametrize('grouped',[1,2])
def test_archive_convert_and_preserve_old_evidence(grouped):
    from app.database.migrate_legacy import migrate
    with isolated_database(install=False) as connect:
        legacy(connect,grouped)
        archive=None
        try:
            with connect() as c:
                report=migrate(c)
                archive=report['archive_schema']
            with connect() as c:
                assert c.execute('SELECT student_id,created_by,set_by FROM student').fetchone()==('S',None,None)
                assert c.execute('SELECT score FROM grade_component_score ORDER BY score_id').fetchall()==[(80,)]*grouped
                assert c.execute('SELECT percentage FROM grade_percentage').fetchall()==[(100/grouped,)]*grouped
                assert c.execute('SELECT count(*) FROM grade').fetchone()[0]==0
                assert c.execute(sql.SQL('SELECT count(*) FROM {}.grades').format(sql.Identifier(archive))).fetchone()[0]==1
                assert migrate(c)['status']=='current'
        finally:
            if archive:
                with connect() as c:
                    c.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(archive)))


def test_nonrepresentable_weights_stop_without_changes():
    from app.database.migrate_legacy import migrate
    with isolated_database(install=False) as connect:
        legacy(connect,3)
        with connect() as c:
            report=migrate(c,preflight_only=True)
            assert report['blockers']
            assert c.execute("SELECT to_regclass('students')").fetchone()[0]=='students'
        with pytest.raises(ValueError,match='W'):
            with connect() as c:
                migrate(c)
        with connect() as c:
            assert c.execute('SELECT count(*) FROM students').fetchone()[0]==1
            assert c.execute("SELECT to_regclass('student')").fetchone()[0] is None
