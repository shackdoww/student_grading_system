"""Transaction interleavings for assignment/score integrity."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event
import psycopg
import pytest
from tests.database_helpers import configure


def test_assignment_removal_cannot_race_a_score_insert(school):
    configure(school)
    inserted = Event()
    release = Event()

    def record_score():
        try:
            with school() as c:
                c.execute(
                    "INSERT INTO grade_component_score(enrollment_id,component_id,score) VALUES ('E','MQ',40)"
                )
                inserted.set()
                assert release.wait(5)
            return "saved"
        except psycopg.Error:
            return "rejected"

    with school() as editor:
        editor.execute(
            "DELETE FROM grade_percentage WHERE class_id='C' AND component_id='MQ'"
        )
        editor.execute(
            "UPDATE grade_percentage SET percentage=50 WHERE class_id='C' AND component_id='ML'"
        )
        with ThreadPoolExecutor(max_workers=1) as pool:
            score = pool.submit(record_score)
            # The fixed insert waits for the assignment deletion and then rejects.
            inserted.wait(0.5)
            try:
                editor.commit()
            finally:
                release.set()
            score.result(timeout=5)
    with school() as c:
        orphan = c.execute("""SELECT count(*) FROM grade_component_score s JOIN enrollment e USING(enrollment_id)
            WHERE NOT EXISTS(SELECT 1 FROM grade_percentage w WHERE w.class_id=e.class_id AND w.component_id=s.component_id)""").fetchone()[
            0
        ]
        assert orphan == 0, "Concurrent writes must not leave an unassigned score."


def test_older_serializable_policy_snapshot_cannot_remove_new_score_assignment(school):
    configure(school)
    with school() as editor:
        editor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        editor.execute("SELECT * FROM class WHERE class_id='C' FOR UPDATE")
        with school() as scorer:
            scorer.execute(
                "INSERT INTO grade_component_score(enrollment_id,component_id,score) VALUES ('E','MQ',40)"
            )
        with pytest.raises(psycopg.Error):
            editor.execute(
                "DELETE FROM grade_percentage WHERE class_id='C' AND component_id='MQ'"
            )
            editor.execute(
                "UPDATE grade_percentage SET percentage=50 WHERE class_id='C' AND component_id='ML'"
            )
            editor.commit()
        editor.rollback()
    with school() as c:
        assert (
            c.execute(
                "SELECT count(*) FROM grade_percentage WHERE component_id='MQ'"
            ).fetchone()[0]
            == 1
        )
        assert (
            c.execute("SELECT count(*) FROM grade_component_score").fetchone()[0] == 1
        )
