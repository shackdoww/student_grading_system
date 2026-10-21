from datetime import time
import importlib
from pathlib import Path
import pytest
import psycopg
from tests.database_helpers import isolated_database, master_records


def test_selectable_schedule_formats_rubric_and_rejects_bad_times():
    from app.services.scheduling import format_schedule, normalize_meetings

    meetings = normalize_meetings(
        [{"weekday": d, "start_time": "13:00", "end_time": "14:30"} for d in (2, 4)]
    )
    assert format_schedule(meetings) == "TTh 1:00–2:30"
    with pytest.raises(ValueError, match="end"):
        normalize_meetings([{"weekday": 1, "start_time": "15:00", "end_time": "14:00"}])
    with pytest.raises(ValueError):
        normalize_meetings([])


@pytest.fixture
def timetable(monkeypatch):
    with isolated_database() as connect:
        for folder in ("repositories", "services"):
            for path in (Path(__file__).parents[1] / "app" / folder).glob("*.py"):
                module = importlib.import_module("app." + folder + "." + path.stem)
                if hasattr(module, "get_connection"):
                    monkeypatch.setattr(module, "get_connection", connect)
        master_records(connect)
        with connect() as c:
            c.execute(
                "INSERT INTO class_meeting(class_id,weekday,start_time,end_time) VALUES ('C',1,'09:00','10:00')"
            )
        yield connect


def add_class(connect, cid="C2", teacher="T", room="OTHER", semester="1st"):
    with connect() as c:
        c.execute(
            """INSERT INTO class(class_id,class_code,subject_id,teacher_id,section,school_year,semester,schedule,room)
          VALUES (%s,%s,'U',%s,'B','2026-2027',%s,'Monday',%s)""",
            (cid, cid, teacher, semester, room),
        )


def test_teacher_conflict_and_back_to_back(timetable):
    add_class(timetable)
    with pytest.raises(psycopg.Error, match="conflict"):
        with timetable() as c:
            c.execute(
                "INSERT INTO class_meeting(class_id,weekday,start_time,end_time) VALUES ('C2',1,'09:30','10:30')"
            )
    with timetable() as c:
        c.execute(
            "INSERT INTO class_meeting(class_id,weekday,start_time,end_time) VALUES ('C2',1,'10:00','11:00')"
        )


def test_room_and_student_conflicts_and_dropped_exemption(timetable):
    with timetable() as c:
        c.execute("UPDATE class SET room='CS-202' WHERE class_id='C'")
        c.execute(
            "INSERT INTO teacher(teacher_id,first_name,last_name,department,status) VALUES ('T2','Jose','Ramos','PE','Active')"
        )
    add_class(timetable, teacher="T2", room=" cs-202 ")
    with pytest.raises(psycopg.Error, match="conflict"):
        with timetable() as c:
            c.execute(
                "INSERT INTO class_meeting(class_id,weekday,start_time,end_time) VALUES ('C2',1,'09:30','10:30')"
            )
    with timetable() as c:
        c.execute("UPDATE class SET room='GYM' WHERE class_id='C2'")
        c.execute(
            "INSERT INTO class_meeting(class_id,weekday,start_time,end_time) VALUES ('C2',1,'09:30','10:30')"
        )
    with pytest.raises(psycopg.Error, match="conflict"):
        with timetable() as c:
            c.execute(
                "INSERT INTO enrollment(student_id,class_id,status) VALUES ('S','C2','Enrolled')"
            )
    with timetable() as c:
        c.execute(
            "INSERT INTO enrollment(enrollment_id,student_id,class_id,status) VALUES ('E2','S','C2','Dropped')"
        )
    with pytest.raises(psycopg.Error, match="conflict"):
        with timetable() as c:
            c.execute(
                "UPDATE enrollment SET status='Enrolled' WHERE enrollment_id='E2'"
            )


def test_class_editor_has_day_and_time_controls():
    from PySide6.QtWidgets import QApplication, QTimeEdit, QCheckBox
    from app.gui.academic_editor import RecordDialog, RECORDS

    app = QApplication.instance() or QApplication([])
    records = {"teacher": [], "subject": []}
    dialog = RecordDialog(
        None, "Add class", RECORDS["Class Offerings"][2].split(), records
    )
    assert len(dialog.findChildren(QTimeEdit)) >= 2
    assert len(dialog.findChildren(QCheckBox)) >= 7
    dialog.close()
