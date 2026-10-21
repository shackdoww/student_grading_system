import pytest
import psycopg
from tests.database_helpers import isolated_database, master_records, configure


@pytest.fixture
def db():
    with isolated_database() as connect:
        yield connect


def test_physical_appendix_tables_and_columns(db):
    required = {
        "student": {"student_id", "year_level", "set_by", "created_by", "updated_by"},
        "class": {"class_id", "subject_id", "teacher_id"},
        "grade_component": {"component_id", "period_id", "max_score"},
        "grade_percentage": {"percentage_id", "class_id", "component_id", "percentage"},
        "grade": {
            "grade_id",
            "enrollment_id",
            "midterm_grade",
            "finals_grade",
            "overall_grade",
            "midterm_equiv",
            "finals_equiv",
            "final_equiv",
            "date_encoded",
        },
        "audit_log": {
            "table_name",
            "record_id",
            "old_value",
            "new_value",
            "changed_by",
            "changed_at",
            "source_reference",
        },
    }
    with db() as c:
        for table, columns in required.items():
            actual = {
                r[0]
                for r in c.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=%s",
                    (table,),
                )
            }
            assert columns <= actual, (table, columns - actual)


def test_six_shared_components_allow_independent_class_weights(db):
    master_records(db)
    configure(db)
    with db() as c:
        c.execute(
            "INSERT INTO class(class_id,class_code,subject_id,teacher_id,section,school_year,semester,schedule) VALUES ('C2','PATHFIT-A','U','T','A','2026-2027','1st','TTh')"
        )
    configure(db, "C2")
    with db() as c:
        c.execute(
            "UPDATE grade_percentage SET percentage=CASE component_id WHEN 'MQ' THEN 30 WHEN 'ME' THEN 40 ELSE percentage END WHERE class_id='C'"
        )
    with db() as c:
        assert c.execute("SELECT count(*) FROM grade_component").fetchone()[0] == 6
        assert c.execute("SELECT count(*) FROM grade_percentage").fetchone()[0] == 12
        assert (
            c.execute(
                "SELECT percentage FROM grade_percentage WHERE class_id='C2' AND component_id='MQ'"
            ).fetchone()[0]
            == 20
        )


def test_invalid_policy_rolls_back_weights_and_audit(db):
    master_records(db)
    configure(db)
    with db() as c:
        before = c.execute("SELECT count(*) FROM audit_log").fetchone()[0]
    with pytest.raises(psycopg.Error, match="100"):
        with db() as c:
            c.execute(
                "UPDATE grade_percentage SET percentage=40 WHERE component_id='ME'"
            )
    with db() as c:
        assert (
            c.execute(
                "SELECT percentage FROM grade_percentage WHERE component_id='ME'"
            ).fetchone()[0]
            == 50
        )
        assert c.execute("SELECT count(*) FROM audit_log").fetchone()[0] == before


@pytest.mark.parametrize("score", [-1, 51, "NaN", "Infinity"])
def test_bad_score_rejected_by_database(db, score):
    master_records(db)
    configure(db)
    with pytest.raises(psycopg.Error):
        with db() as c:
            c.execute(
                "INSERT INTO grade_component_score(enrollment_id,component_id,score,date_recorded) VALUES ('E','MQ',%s,CURRENT_DATE)",
                (score,),
            )


def test_unassigned_score_and_invalidating_component_edit_rejected(db):
    master_records(db)
    with pytest.raises(psycopg.Error):
        with db() as c:
            c.execute(
                "INSERT INTO grade_component_score(enrollment_id,component_id,score,date_recorded) VALUES ('E','MQ',40,CURRENT_DATE)"
            )
    configure(db)
    with db() as c:
        c.execute(
            "INSERT INTO grade_component_score(enrollment_id,component_id,score,date_recorded) VALUES ('E','MQ',40,CURRENT_DATE)"
        )
    with pytest.raises(psycopg.Error):
        with db() as c:
            c.execute("UPDATE grade_component SET max_score=30 WHERE component_id='MQ'")
    with pytest.raises(psycopg.Error):
        with db() as c:
            c.execute("DELETE FROM student WHERE student_id='S'")


def test_actor_source_history_and_noop_audit(db):
    from app.database.connection import audit_actor
    from app.database.provenance import write_source

    with audit_actor("registrar"), write_source("ST-01"):
        master_records(db)
    with audit_actor("admin"), write_source("ST-05"):
        with db() as c:
            c.execute(
                "UPDATE student SET program='BSIT',updated_by='forged' WHERE student_id='S'"
            )
    with db() as c:
        assert c.execute(
            "SELECT set_by,created_by,updated_by FROM student WHERE student_id='S'"
        ).fetchone() == ("ST-01; ST-05", "registrar", "admin")
        before = c.execute("SELECT count(*) FROM audit_log").fetchone()[0]
        c.execute("UPDATE student SET program='BSIT' WHERE student_id='S'")
        assert c.execute("SELECT count(*) FROM audit_log").fetchone()[0] == before
