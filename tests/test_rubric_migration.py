from pathlib import Path
import pytest
from psycopg import sql
from tests.database_helpers import isolated_database

FIXTURES = Path(__file__).parent / "fixtures/legacy_database"


def legacy(connect, grouped=1):
    with connect() as c:
        c.execute((FIXTURES / "schema.sql").read_text())
        for f in sorted(FIXTURES.glob("migration_*.sql")):
            c.execute(f.read_text())
        c.execute(
            "INSERT INTO students(student_id,first_name,last_name,email,program,status) VALUES ('S','Juan','Dela Cruz',NULL,'BSCS','Active')"
        )
        c.execute(
            "INSERT INTO teachers VALUES ('T','Maria','Santos',NULL,'IT','Active')"
        )
        c.execute("INSERT INTO subjects VALUES ('U','CS','OOP',NULL,3)")
        c.execute(
            "INSERT INTO class_offerings VALUES ('C','CS-A','MWF','A','2026','1st','R','T','U')"
        )
        c.execute(
            "INSERT INTO grading_periods(period_id,name,start_date,end_date,school_year,semester) VALUES ('M','Midterm','2026-01-01','2026-06-01','2026','1st')"
        )
        c.execute(
            "INSERT INTO enrollments VALUES ('E',CURRENT_DATE,'Enrolled','S','C')"
        )
        c.execute("INSERT INTO grade_percentages VALUES ('W',100,'C')")
        for i in range(grouped):
            c.execute(
                "INSERT INTO grade_components VALUES (%s,%s,'Exam',100,NULL,'M','W')",
                (f"X{i}", f"Exam {i}"),
            )
            c.execute(
                "INSERT INTO grade_component_scores VALUES (%s,80,NULL,CURRENT_DATE,'E',%s)",
                (f"S{i}", f"X{i}"),
            )
        c.execute("INSERT INTO grades VALUES ('G',80,'Legacy',CURRENT_DATE,'E')")


def test_fresh_and_repeat_install():
    from app.database.migrate_legacy import migrate

    with isolated_database(install=False) as connect:
        with connect() as c:
            assert migrate(c)["status"] == "installed"
        with connect() as c:
            assert migrate(c)["status"] == "current"
            assert c.execute("SELECT count(*) FROM student").fetchone()[0] == 0


@pytest.mark.parametrize("grouped", [1, 2])
def test_archive_convert_and_preserve_old_evidence(grouped):
    from app.database.migrate_legacy import migrate

    with isolated_database(install=False) as connect:
        legacy(connect, grouped)
        archive = None
        try:
            with connect() as c:
                report = migrate(c)
                archive = report["archive_schema"]
            with connect() as c:
                assert c.execute(
                    "SELECT student_id,created_by,set_by FROM student"
                ).fetchone() == ("S", None, None)
                assert (
                    c.execute(
                        "SELECT score FROM grade_component_score ORDER BY score_id"
                    ).fetchall()
                    == [(80,)] * grouped
                )
                assert (
                    c.execute("SELECT percentage FROM grade_percentage").fetchall()
                    == [(100 / grouped,)] * grouped
                )
                assert c.execute("SELECT count(*) FROM grade").fetchone()[0] == 0
                assert (
                    c.execute(
                        sql.SQL("SELECT count(*) FROM {}.grades").format(
                            sql.Identifier(archive)
                        )
                    ).fetchone()[0]
                    == 1
                )
                assert migrate(c)["status"] == "current"
        finally:
            if archive:
                with connect() as c:
                    c.execute(
                        sql.SQL("DROP SCHEMA {} CASCADE").format(
                            sql.Identifier(archive)
                        )
                    )


def test_nonrepresentable_weights_stop_without_changes():
    from app.database.migrate_legacy import migrate

    with isolated_database(install=False) as connect:
        legacy(connect, 3)
        with connect() as c:
            report = migrate(c, preflight_only=True)
            assert report["blockers"]
            assert (
                c.execute("SELECT to_regclass('students')").fetchone()[0] == "students"
            )
        with pytest.raises(ValueError, match="W"):
            with connect() as c:
                migrate(c)
        with connect() as c:
            assert c.execute("SELECT count(*) FROM students").fetchone()[0] == 1
            assert c.execute("SELECT to_regclass('student')").fetchone()[0] is None


def test_period_results_accounts_and_timestamps_survive_conversion():
    from app.database.migrate_legacy import migrate
    from app.services.account_service import AccountService

    with isolated_database(install=False) as connect:
        legacy(connect)
        auth = AccountService(connect)
        auth.create_account(
            "migration-admin",
            "Admin",
            "Testing Student Hub 2026!",
            "admin",
            first_admin=True,
        )
        token = auth.authenticate("migration-admin", "Testing Student Hub 2026!")
        with connect() as c:
            c.execute(
                "INSERT INTO grading_periods(period_id,name,start_date,end_date,school_year,semester) VALUES ('F','Finals','2026-06-02','2026-12-01','2026','1st')"
            )
            c.execute(
                "INSERT INTO grade_components VALUES ('FC','Final Exam','Exam',100,NULL,'F','W')"
            )
            c.execute(
                "INSERT INTO grade_component_scores VALUES ('FS',90,NULL,CURRENT_DATE,'E','FC')"
            )
            c.execute("INSERT INTO grading_policies VALUES ('C','M','F',40,60)")
            c.execute(
                "INSERT INTO period_category_weights VALUES ('C','M','W',100),('C','F','W',100)"
            )
            c.execute(
                "INSERT INTO period_grade_results(enrollment_id,midterm_grade,final_grade,overall_grade,calculated_at,midterm_equiv,finals_equiv,final_equiv,remarks) VALUES ('E',80,90,86,'2026-10-19T12:00:00Z',2.5,1.75,2,'Passed')"
            )
        archive = None
        try:
            with connect() as c:
                archive = migrate(c)["archive_schema"]
            assert auth.resolve(token)["username"] == "migration-admin"
            with connect() as c:
                row = c.execute(
                    "SELECT midterm_grade,finals_grade,overall_grade,final_equiv,date_encoded,created_by FROM grade"
                ).fetchone()
                assert tuple(float(v) for v in row[:4]) == (80, 90, 86, 2)
                assert str(row[4]) == "2026-10-19"
                assert row[5] is None
                assert (
                    c.execute("SELECT count(*) FROM grade_component_score").fetchone()[
                        0
                    ]
                    == 2
                )
        finally:
            if archive:
                with connect() as c:
                    c.execute(
                        sql.SQL("DROP SCHEMA {} CASCADE").format(
                            sql.Identifier(archive)
                        )
                    )


def test_partial_legacy_layout_reports_blockers_without_changes():
    from app.database.migrate_legacy import migrate

    with isolated_database(install=False) as connect:
        with connect() as c:
            c.execute("CREATE TABLE students(student_id TEXT PRIMARY KEY)")
            report = migrate(c, preflight_only=True)
            assert report["blockers"]
        with pytest.raises(ValueError, match="Migration blocked"):
            with connect() as c:
                migrate(c)
        with connect() as c:
            assert c.execute("SELECT to_regclass('student')").fetchone()[0] is None
