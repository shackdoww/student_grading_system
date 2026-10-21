"""All 52 rubric cases, real services/SQL, exact appendix comparison and restart."""

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import date
import psycopg
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from tests.database_helpers import isolated_database
from tests.rubric_comparison import compare
from app.services.student_service import StudentService
from app.services.academic_service import AcademicService
from app.services.enrollment_service import EnrollmentService
from app.services.score_service import ScoreService
from app.services.period_grading_service import PeriodGradingService
from app.services.account_service import AccountService
from app.services.access_control import AccessGuard, SecuredService
from app.services.record_deletion_service import RecordDeletionService
from app.gui.data_snapshot import load_snapshot
from app.gui.checklist_reports import class_report, student_report


@pytest.fixture
def school(monkeypatch):
    with isolated_database() as connect:
        for folder in ("repositories", "services"):
            for path in (Path(__file__).parents[1] / "app" / folder).glob("*.py"):
                module = importlib.import_module("app." + folder + "." + path.stem)
                if hasattr(module, "get_connection"):
                    monkeypatch.setattr(module, "get_connection", connect)
        monkeypatch.setattr("app.gui.data_snapshot.get_connection", connect)
        yield connect


def test_checklist_create_validate_recompute_report_and_persist(school, monkeypatch):
    auth = AccountService(school)
    auth.create_account(
        "tester",
        "Rubric Tester",
        "Testing Student Hub 2026!",
        "admin",
        first_admin=True,
    )
    token = auth.authenticate("tester", "Testing Student Hub 2026!")
    guard = AccessGuard(auth, token)
    students = SecuredService(StudentService(), guard)
    academic = SecuredService(AcademicService(), guard)
    enrollment = SecuredService(EnrollmentService(), guard)
    scores = SecuredService(ScoreService(), guard)
    periods = SecuredService(PeriodGradingService(connection_factory=school), guard)
    deletion = RecordDeletionService(guard)
    done = set()

    def mark(case):
        assert case not in done
        done.add(case)

    def reject(operation):
        with school() as c:
            before = {
                t: c.execute("SELECT count(*) FROM " + t).fetchone()[0]
                for t in (
                    "student",
                    "teacher",
                    "subject",
                    "class",
                    "enrollment",
                    "grade_component",
                    "grade_percentage",
                    "grade_component_score",
                    "grade",
                    "audit_log",
                )
            }
        with pytest.raises((ValueError, PermissionError, psycopg.Error)):
            operation()
        with school() as c:
            assert before == {
                t: c.execute("SELECT count(*) FROM " + t).fetchone()[0] for t in before
            }

    def student(sid, first, last, program="BSCS", year=2, source="ST-01"):
        students.create(
            sid, first, last, "", program, "Active", year, source_reference=source
        )

    def meetings(days, start, end):
        return [dict(weekday=d, start_time=start, end_time=end) for d in days]

    def save_class(
        cid,
        source="CL-01",
        schedule=None,
        room="CS-201",
        teacher="T-1001",
        subject="SUB-CS",
    ):
        academic.save_offering(
            cid,
            cid,
            schedule or meetings((1, 3, 5), "09:00", "10:00"),
            "A",
            "2026-2027",
            "1st",
            room,
            teacher,
            subject,
            source_reference=source,
        )

    def policy(cid):
        return dict(
            class_id=cid,
            midterm_period_id="M",
            final_period_id="F",
            midterm_weight=40,
            final_weight=60,
        )

    cids = ["MQ", "ML", "ME", "FQ", "FL", "FE"]

    def weights(mid=(20, 30, 50)):
        return [
            dict(component_id=cid, percentage=w)
            for cid, w in zip(cids, [*mid, 20, 30, 50])
        ]

    ids = ["2026-0001", "2026-0002", "2026-0003"]

    for sid, first, last, program in zip(
        ids,
        ["Juan", "Pedro", "Ana"],
        ["Dela Cruz", "Reyes", "Garcia"],
        ["BSCS", "BSCS", "BSIT"],
    ):
        student(sid, first, last, program)
    mark("ST-01")
    reject(lambda: student(ids[0], "Other", "Person"))
    mark("ST-02")
    reject(lambda: student("", "Blank", "Student"))
    reject(lambda: student("BLANK", "", "Student"))
    mark("ST-03")
    assert StudentService().get(ids[1])[2] == "Reyes"
    mark("ST-04")
    students.save(
        ids[2], "Ana", "Garcia", "", "BSCS", "Active", 2, source_reference="ST-05"
    )
    mark("ST-05")
    student("2026-0099", "Lea", "Ramos", "BSIT", 1, "ST-06")
    deletion.delete("student", "2026-0099", source_reference="ST-06")
    mark("ST-06")
    academic.create_teacher(
        "T-1001",
        "Maria",
        "Santos",
        "",
        "Computer Studies Department",
        "Active",
        source_reference="TE-01",
    )
    mark("TE-01")
    reject(
        lambda: academic.create_teacher(
            "T-1001", "Other", "Teacher", "", "IT", "Active"
        )
    )
    reject(lambda: academic.create_teacher("BAD", "", "Teacher", "", "IT", "Active"))
    mark("TE-02")
    assert AcademicService().get_teacher("T-1001")[1:3] == ("Maria", "Santos")
    mark("TE-03")
    academic.save_teacher(
        "T-1001",
        "Maria",
        "Santos",
        "",
        "Information Technology Department",
        "Active",
        source_reference="TE-04",
    )
    mark("TE-04")
    academic.save_subject(
        "SUB-CS",
        "CSPC 103",
        "Object Oriented Programming",
        "",
        3,
        source_reference="SU-01",
    )
    mark("SU-01")
    reject(lambda: academic.save_subject("DUP", "CSPC 103", "Duplicate", "", 3))
    reject(lambda: academic.save_subject("ZERO", "ZERO", "Invalid", "", 0))
    reject(lambda: academic.save_subject("NEG", "NEG", "Invalid", "", -1))
    mark("SU-02")
    assert AcademicService().get_subject("SUB-CS")[1] == "CSPC 103"
    mark("SU-03")
    academic.save_subject(
        "SUB-CS",
        "CSPC 103",
        "Object Oriented Programming",
        "Object-oriented analysis, design and programming in Java",
        3,
        source_reference="SU-04",
    )
    mark("SU-04")
    academic.save_subject("TEMP", "TEMP", "Temporary", "", 1, source_reference="SU-05")
    academic.delete_unreferenced("subject", "TEMP", source_reference="SU-05")
    save_class("CSPC103-A")
    mark("CL-01")
    reject(lambda: academic.delete_unreferenced("teacher", "T-1001"))
    with pytest.raises(ValueError, match="CSPC103-A"):
        academic.delete_unreferenced("teacher", "T-1001")
    mark("TE-05")
    reject(lambda: academic.delete_unreferenced("subject", "SUB-CS"))
    mark("SU-05")
    reject(
        lambda: academic.save_offering(
            "BAD",
            "BAD",
            meetings((1,), "12:00", "13:00"),
            "A",
            "",
            "1st",
            "",
            "T-1001",
            "SUB-CS",
        )
    )
    reject(
        lambda: academic.save_offering(
            "BAD",
            "BAD",
            meetings((1,), "12:00", "13:00"),
            "A",
            "2026-2027",
            "1st",
            "",
            "",
            "SUB-CS",
        )
    )
    reject(
        lambda: academic.save_offering(
            "BAD",
            "BAD",
            meetings((1,), "12:00", "13:00"),
            "A",
            "2026-2027",
            "1st",
            "",
            "T-1001",
            "",
        )
    )
    mark("CL-02")
    assert AcademicService().get_offerings()[0][0] == "CSPC103-A"
    mark("CL-03")
    save_class("CSPC103-A", "CL-04", meetings((2, 4), "13:00", "14:30"), "CS-202")
    mark("CL-04")
    eids = {
        sid: enrollment.enroll(sid, "CSPC103-A", source_reference="EN-01")
        for sid in ids
    }
    mark("EN-01")
    reject(lambda: deletion.delete("student", ids[0]))
    mark("ST-07")
    reject(lambda: academic.delete_unreferenced("class", "CSPC103-A"))
    mark("CL-05")
    reject(lambda: enrollment.enroll(ids[0], "CSPC103-A"))
    mark("EN-02")
    reject(lambda: enrollment.enroll("2026-9999", "CSPC103-A"))
    mark("EN-03")
    assert len(EnrollmentService().get_by_offering("CSPC103-A")) == 3
    mark("EN-04")
    enrollment.update_status(eids[ids[1]], "Dropped", source_reference="EN-05")
    enrollment.update_status(eids[ids[1]], "Enrolled", source_reference="EN-05")
    mark("EN-05")
    student("2026-0098", "Carlo", "Mendoza", "BSIT", 1, "EN-06")
    carlo = enrollment.enroll("2026-0098", "CSPC103-A", source_reference="EN-06")
    deletion.delete("enrollment", carlo, source_reference="EN-06")
    academic.save_period(
        "M",
        "Midterm",
        date(2026, 1, 1),
        date(2026, 5, 31),
        "2026-2027",
        "1st",
        1,
        source_reference="GP-01",
    )
    academic.save_period(
        "F",
        "Finals",
        date(2026, 6, 1),
        date(2026, 10, 31),
        "2026-2027",
        "1st",
        2,
        source_reference="GP-01",
    )
    mark("GP-01")
    names = [
        "Midterm Quiz",
        "Midterm Laboratory/Project",
        "Midterm Examination",
        "Final Quiz",
        "Final Laboratory/Project",
        "Final Examination",
    ]
    for i, (cid, name) in enumerate(zip(cids, names)):
        academic.save_component(
            cid,
            name,
            ["Quiz", "Laboratory", "Exam"][i % 3],
            [50, 100, 100][i % 3],
            "",
            "M" if i < 3 else "F",
            source_reference="GC-01",
        )
    mark("GC-01")
    periods.save_policy(policy("CSPC103-A"), weights(), source_reference="GW-01")
    mark("GW-01")
    reject(lambda: periods.save_policy(policy("CSPC103-A"), weights((20, 30, 40))))
    mark("GW-02")
    reject(lambda: periods.save_policy(policy("CSPC103-A"), weights((-1, 30, 71))))
    reject(lambda: periods.save_policy(policy("CSPC103-A"), weights(("", 30, 70))))
    mark("GW-03")
    assert len(AcademicService().get_components("CSPC103-A")) == 6
    mark("GC-02")
    raw = [
        [40, 90, 57, 45, 85, 80],
        [20, 60, 55, 30, 70, 65],
        [50, 100, 100, 48, 95, 92],
    ]
    for sid, values in zip(ids, raw):
        for cid, value in zip(cids, values):
            scores.record_score(
                sid + "-" + cid, eids[sid], cid, value, source_reference="SC-01"
            )
    mark("SC-01")
    reject(lambda: deletion.delete("enrollment", eids[ids[0]]))
    mark("EN-06")
    reject(lambda: academic.delete_unreferenced("grade_component", "MQ"))
    mark("GC-03")
    reject(lambda: scores.record_score("BAD", eids[ids[0]], "MQ", 55))
    mark("SC-02")
    reject(lambda: scores.record_score("BAD", eids[ids[0]], "MQ", -5))
    mark("SC-03")
    reject(lambda: scores.record_score("BAD", carlo, "MQ", 30))
    mark("SC-04")
    assert len(ScoreService().get_scores(eids[ids[0]])) == 6
    mark("SC-05")
    scores.record_score("IGNORED", eids[ids[0]], "ME", 75, source_reference="SC-06")
    mark("SC-06")
    deletion.delete("grade_component_score", ids[2] + "-FQ", source_reference="SC-07")
    with pytest.raises(ValueError, match="Missing score"):
        periods.calculate_and_save(eids[ids[2]])
    scores.record_score(
        "REENTERED-A-FQ", eids[ids[2]], "FQ", 48, source_reference="SC-07"
    )
    mark("SC-07")
    for sid, value in zip(ids, [80.5, 53.5, 100]):
        assert (
            periods.calculate_and_save(
                eids[sid], period="midterm", source_reference="GR-01"
            )["midterm"]
            == value
        )
    mark("GR-01")
    for sid, value in zip(ids, [82.3, 60.7, 96.22]):
        assert (
            periods.calculate_and_save(eids[sid], source_reference="GR-02")["overall"]
            == value
        )
    mark("GR-02")
    with school() as c:
        original = c.execute(
            "SELECT score_id,score FROM grade_component_score ORDER BY score_id"
        ).fetchall()
    periods.save_policy(
        policy("CSPC103-A"), weights((30, 30, 40)), source_reference="GR-03"
    )
    for sid, value in zip(ids, [82.5, 60.1, 96.22]):
        assert (
            periods.calculate_and_save(eids[sid], source_reference="GR-03")["overall"]
            == value
        )
    with school() as c:
        assert (
            c.execute(
                "SELECT score_id,score FROM grade_component_score ORDER BY score_id"
            ).fetchall()
            == original
        )
    mark("GR-03")
    with school() as c:
        events = c.execute(
            "SELECT table_name,action,source_reference,old_value,new_value,changed_by FROM audit_log WHERE source_reference IN ('SC-06','SC-07','GR-03')"
        ).fetchall()
        assert all(r[-1] == "tester" for r in events)
        assert (
            sum(
                r[0] == "GRADE_COMPONENT_SCORE"
                and r[1] == "UPDATE"
                and r[3]["score"] == 57
                and r[4]["score"] == 75
                for r in events
            )
            == 1
        )
        assert (
            sum(r[0] == "GRADE_COMPONENT_SCORE" and r[1] == "DELETE" for r in events)
            == 1
        )
        assert (
            sum(r[0] == "GRADE_COMPONENT_SCORE" and r[1] == "INSERT" for r in events)
            == 1
        )
        assert sum(r[0] == "GRADE_PERCENTAGE" and r[1] == "UPDATE" for r in events) == 2
        assert sum(r[0] == "GRADE" and r[1] == "UPDATE" for r in events) == 2
    mark("GR-04")
    snapshot = load_snapshot()
    roster = class_report(snapshot, "CSPC103-A")
    assert roster["rows"] == [
        [1, "Dela Cruz, Juan", "BSCS"],
        [2, "Garcia, Ana", "BSCS"],
        [3, "Reyes, Pedro", "BSCS"],
    ]
    assert any(
        "Information Technology Department" in line for line in roster["metadata"]
    )
    assert any(
        "CS-202" in line and "TTh 1:00–2:30" in line for line in roster["metadata"]
    )
    mark("RP-01")
    assert [row[-2:] for row in class_report(snapshot, "CSPC103-A", True)["rows"]] == [
        ["2.50", "2.25"],
        ["1.00", "1.25"],
        ["5.00", "5.00"],
    ]
    mark("RP-02")
    academic.create_teacher(
        "T-1002",
        "Jose",
        "Ramos",
        "",
        "Physical Education Department",
        "Active",
        source_reference="Report setup",
    )
    academic.save_subject(
        "SUB-PE",
        "PATHFIT 3",
        "Physical Activity Towards Health and Fitness 3",
        "",
        2,
        source_reference="Report setup",
    )
    save_class(
        "PATHFIT3-A",
        "Report setup",
        meetings((2, 4), "15:00", "17:00"),
        "Gym",
        "T-1002",
        "SUB-PE",
    )
    pe = enrollment.enroll(ids[0], "PATHFIT3-A", source_reference="Report setup")
    periods.save_policy(
        policy("PATHFIT3-A"), weights(), source_reference="Report setup"
    )
    for cid, value in zip(cids, [45, 90, 90, 45, 90, 90]):
        scores.record_score(
            "PE-" + cid, pe, cid, value, source_reference="Report setup"
        )
    periods.calculate_and_save(pe, source_reference="Report setup")
    snapshot = load_snapshot()
    report = student_report(snapshot, ids[0], "2026-2027", "1st")
    assert [r[-2:] for r in report["rows"]] == [[3, "2.25"], [2, "1.75"]]
    mark("RP-03")
    assert report["summary"] == [
        "Total Units: 5",
        "No. of Subjects: 2",
        "Grade Weighted Average: 2.05",
    ]
    mark("RP-04")
    env = dict(
        os.environ,
        CHECKLIST_SCHEMA=school.schema_name,
        CHECKLIST_TEST_TOKEN=token,
        QT_QPA_PLATFORM="offscreen",
    )
    probe = subprocess.run(
        [sys.executable, "-m", "tests.checklist_restart_probe"],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert probe.returncode == 0, probe.stdout + probe.stderr
    mark("PS-01")
    student("2026-0004", "Kevin", "O'Brien", "BSIT", 1, "PS-02")
    app = QApplication.instance() or QApplication([])
    from app.gui.pyside_app import StudentHub

    monkeypatch.setattr("app.gui.pyside_app.load_snapshot", load_snapshot)
    window = StudentHub(token, auth)
    errors = []
    window.error = errors.append
    try:
        for _ in range(300):
            if window._data_version:
                break
            QTest.qWait(10)
        assert window._data_version and not errors, errors
        for key in window.pages:
            window.show_page(key)
            app.processEvents()
        assert not errors, errors
        window.show_page('dashboard')
        window.dashboard.search.setText("Reyes")
        assert window.dashboard.student_table.rowCount() == 1
        window.dashboard.search.setText("' OR '1'='1")
        assert window.dashboard.student_table.rowCount() == 0
        assert StudentService().get("2026-0004")[2] == "O'Brien"
    finally:
        window.close()
    mark("PS-02")
    assert len(done) == 52, sorted(done)
    with school() as c:
        comparison = compare(c)
        assert not any(r["differences"] for r in comparison.values()), json.dumps(
            comparison, indent=2, default=str
        )
        assert (
            c.execute(
                "SELECT count(*) FROM student WHERE student_id='2026-0099'"
            ).fetchone()[0]
            == 0
        )
        assert (
            c.execute(
                "SELECT count(*) FROM enrollment WHERE student_id IN ('2026-0098','2026-9999')"
            ).fetchone()[0]
            == 0
        )
        assert (
            c.execute(
                "SELECT count(*) FROM grade_component_score WHERE score_id=%s",
                (ids[2] + "-FQ",),
            ).fetchone()[0]
            == 0
        )
    artifact = Path(
        os.getenv("RUBRIC_COMPARISON_PATH", "/tmp/student-rubric-comparison.json")
    )
    artifact.write_text(
        json.dumps(
            {"cases_passed": sorted(done), "tables": comparison}, indent=2, default=str
        )
        + "\n"
    )
