from PySide6.QtWidgets import QApplication
from tests.test_rubric_services import policy, weights
from app.services.period_grading_service import PeriodGradingService
from app.services.score_service import ScoreService
from app.gui.data_snapshot import load_snapshot
from app.gui.checklist_reports import class_report, student_report


def test_canonical_snapshot_and_saved_reports(school, monkeypatch):
    monkeypatch.setattr("app.gui.data_snapshot.get_connection", school)
    service = PeriodGradingService(connection_factory=school)
    service.save_policy(policy(), weights())
    for cid, value in zip(
        ["MQ", "ML", "ME", "FQ", "FL", "FE"], [40, 90, 75, 45, 85, 80]
    ):
        ScoreService().record_score("S-" + cid, "E", cid, value)
    service.calculate_and_save("E")
    snapshot = load_snapshot()
    report = class_report(snapshot, "C", True)
    assert report["headers"] == ["No.", "Student", "Course", "MG", "FG"]
    assert report["rows"] == [[1, "Dela Cruz, Juan", "BSCS", "2.50", "2.25"]]
    assert (
        student_report(snapshot, "S", "2026-2027", "1st")["summary"][-1]
        == "Grade Weighted Average: 2.25"
    )
    ScoreService().delete_score("S-FQ")
    snapshot = load_snapshot()
    assert class_report(snapshot, "C", True)["rows"][0][-1] == "Incomplete"


def test_component_editor_and_source_input():
    from app.gui.academic_editor import RECORDS, RecordDialog

    app = QApplication.instance() or QApplication([])
    fields = RECORDS["Components"][2].split()
    assert "percentage_id" not in fields
    dialog = RecordDialog(None, "Add component", fields, {"grading_period": []})
    assert hasattr(dialog, "source")
    assert dialog.source.text() == ""
    dialog.close()


def test_policy_dialog_reuses_shared_components(school):
    from psycopg.rows import dict_row
    from app.gui.period_grading_dialog import PeriodPolicyDialog

    app = QApplication.instance() or QApplication([])
    with school() as c:
        with c.cursor(row_factory=dict_row) as cur:
            records = {}
            for table in (
                "class",
                "grading_period",
                "grade_component",
                "grade_percentage",
                "grading_policy",
            ):
                cur.execute("SELECT * FROM " + table)
                records[table] = cur.fetchall()
    dialog = PeriodPolicyDialog(None, "C", records)
    dialog.periods["midterm"].setCurrentIndex(dialog.periods["midterm"].findData("M"))
    dialog.periods["final"].setCurrentIndex(dialog.periods["final"].findData("F"))
    assert len(dialog.inputs) == 6
    assert all(len(item) == 3 for item in dialog.inputs)
    dialog.close()
