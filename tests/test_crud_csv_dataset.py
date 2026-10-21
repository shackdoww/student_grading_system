"""The document's final-state CSV snapshot must import and report correctly."""

import csv
from pathlib import Path

from psycopg import sql

from app.database.connection import audit_actor
from app.gui.checklist_reports import class_report, student_report
from app.gui.data_snapshot import load_snapshot
from app.services.school_data_import_service import (
    SchoolDataImportService,
    DATASETS,
    PK,
)
from tests.database_helpers import isolated_database
from tests.rubric_comparison import compare

DATA = Path(__file__).parents[1] / "test_data" / "crud_test_case"


def test_crud_csv_import_matches_final_appendix(monkeypatch):
    with isolated_database() as connect:
        monkeypatch.setattr(
            "app.services.school_data_import_service.get_connection", connect
        )
        monkeypatch.setattr("app.gui.data_snapshot.get_connection", connect)
        service = SchoolDataImportService()
        datasets = service.read_folder(DATA)
        assert not datasets.get("_legacy_evidence")
        with audit_actor("csv-import-tester"):
            assert service.validate(datasets) == []
            service.import_all(datasets)
        with connect() as c:
            comparison = compare(c)
            # This dataset retains the appendix's full explanatory Set by text;
            # the live-case fixture uses concise case references instead.
            for table, result in comparison.items():
                assert not [
                    d for d in result["differences"] if d.get("field") != "set_by"
                ], (table, result)
            for table, _, _ in DATASETS:
                if table == "class_meeting":
                    continue
                for row in datasets[table]:
                    saved = c.execute(
                        sql.SQL("SELECT set_by,created_by FROM {} WHERE {}=%s").format(
                            sql.Identifier(table), sql.Identifier(PK[table])
                        ),
                        (row[PK[table]],),
                    ).fetchone()
                    assert saved == (row["set_by"], "csv-import-tester")
            assert c.execute(
                "SELECT DISTINCT changed_by FROM audit_log"
            ).fetchall() == [("csv-import-tester",)]
            assert c.execute("SELECT count(*) FROM class_meeting").fetchone()[0] == 4
            assert (
                c.execute(
                    "SELECT count(*) FROM grade_component_score WHERE score_id='16'"
                ).fetchone()[0]
                == 0
            )
        snapshot = load_snapshot()
        assert [r[-2:] for r in class_report(snapshot, "1", True)["rows"]] == [
            ["2.50", "2.25"],
            ["1.00", "1.25"],
            ["5.00", "5.00"],
        ]
        report = student_report(snapshot, "2026-0001", "2026-2027", "1st")
        assert report["summary"] == [
            "Total Units: 5",
            "No. of Subjects: 2",
            "Grade Weighted Average: 2.05",
        ]
        # Re-importing the same snapshot does not duplicate records or audit events.
        with connect() as c:
            before = c.execute("SELECT count(*) FROM audit_log").fetchone()[0]
        with audit_actor("csv-import-tester"):
            service.import_all(datasets)
        with connect() as c:
            assert c.execute("SELECT count(*) FROM audit_log").fetchone()[0] == before
            assert c.execute("SELECT count(*) FROM grade").fetchone()[0] == 4


def test_snapshot_csv_has_doc_corrections_and_original_ids():
    def rows(filename):
        with (DATA / filename).open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    scores = {r["score_id"]: r for r in rows("school_grade_component_scores.csv")}
    assert scores["3"]["score"] == "75"
    assert "16" not in scores and scores["19"]["score"] == "48"
    students = {r["student_id"]: r for r in rows("school_students.csv")}
    assert students["2026-0003"]["program"] == "BSCS"
    assert "2026-0099" not in students
    assert students["2026-0004"]["last_name"] == "O'Brien"
    assert students["2026-0003"]["set_by"] == "ST-01; program BSIT → BSCS in ST-05"
