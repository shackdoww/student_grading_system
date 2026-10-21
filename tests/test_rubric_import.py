import pytest
from app.services.school_data_import_service import SchoolDataImportService, DATASETS


@pytest.mark.parametrize("email", ["", "kevin@example.edu"])
def test_optional_emails_and_nonfinite_csv_values(school, email):
    service = SchoolDataImportService()
    datasets = {table: [] for table, *_ in DATASETS}
    datasets["student"] = [
        dict(
            student_id="S2",
            first_name="Kevin",
            last_name="O'Brien",
            email=email,
            program="BSIT",
            year_level=1,
            status="Active",
            source_reference="PS-02",
        )
    ]
    assert service.validate(datasets) == []
    service.import_all(datasets)
    with school() as c:
        assert c.execute(
            "SELECT last_name,email,set_by FROM student WHERE student_id='S2'"
        ).fetchone() == ("O'Brien", email or None, "PS-02")
    datasets["grade_component"] = [
        dict(
            component_id="BAD", name="Quiz", type="Quiz", period_id="M", max_score="NaN"
        )
    ]
    assert any("finite" in e.lower() for e in service.validate(datasets))


def test_import_failure_rolls_back_all_rows(school):
    service = SchoolDataImportService()
    datasets = {table: [] for table, *_ in DATASETS}
    datasets["student"] = [
        dict(
            student_id="S2",
            first_name="Kevin",
            last_name="O'Brien",
            program="BSIT",
            year_level=1,
            status="Active",
        )
    ]
    datasets["enrollment"] = [
        dict(enrollment_id="BAD", student_id="UNKNOWN", class_id="C", status="Enrolled")
    ]
    with pytest.raises(ValueError):
        service.import_all(datasets)
    with school() as c:
        assert (
            c.execute("SELECT count(*) FROM student WHERE student_id='S2'").fetchone()[
                0
            ]
            == 0
        )


def test_bundled_legacy_dataset_has_documented_conversion(school):
    from pathlib import Path

    service = SchoolDataImportService()
    datasets = service.read_folder(Path(__file__).parents[1] / "test_data")
    assert "grade_component" in datasets
    assert all("percentage_id" not in c for c in datasets["grade_component"])
    assert all("component_id" in w for w in datasets["grade_percentage"])
    # Fresh import must not replace historic percentages with fabricated period grades.
    assert datasets["grade"] == []
    assert datasets.get("_legacy_evidence")


def test_canonical_class_import_requires_explicit_times(school):
    service = SchoolDataImportService()
    datasets = {table: [] for table, *_ in DATASETS}
    datasets["class"] = [
        dict(
            class_id="NEW",
            class_code="NEW",
            subject_id="U",
            teacher_id="T",
            section="B",
            school_year="2026-2027",
            semester="1st",
            schedule="MWF 9:00-10:00",
        )
    ]
    assert service.validate(datasets), (
        "Ambiguous text must not bypass timetable checks."
    )


def test_duplicate_csv_primary_keys_are_rejected_without_overwriting(school):
    service = SchoolDataImportService()
    datasets = {table: [] for table, *_ in DATASETS}
    datasets["student"] = [
        dict(
            student_id="NEW",
            first_name=first,
            last_name="Student",
            program="BSCS",
            status="Active",
            year_level=2,
        )
        for first in ("First", "Second")
    ]
    assert any("duplicate" in e.lower() for e in service.validate(datasets))
    with pytest.raises(ValueError):
        service.import_all(datasets)
    with school() as c:
        assert (
            c.execute("SELECT count(*) FROM student WHERE student_id='NEW'").fetchone()[
                0
            ]
            == 0
        )


@pytest.mark.parametrize("include_class", [True, False])
def test_import_replaces_meeting_set_and_display_together(school, include_class):
    service = SchoolDataImportService()
    with school() as c:
        c.execute(
            "INSERT INTO class_meeting(meeting_id,class_id,weekday,start_time,end_time) VALUES ('OLD','C',1,'09:00','10:00')"
        )
    datasets = {table: [] for table, *_ in DATASETS}
    datasets["class"] = [
        dict(
            class_id="C",
            class_code="CSPC103-A",
            subject_id="U",
            teacher_id="T",
            section="A",
            school_year="2026-2027",
            semester="1st",
            schedule="Friday",
            room="ROOM",
        )
    ]
    datasets["class_meeting"] = [
        dict(
            meeting_id="NEW",
            class_id="C",
            weekday=5,
            start_time="11:00",
            end_time="12:00",
        )
    ]
    if not include_class:
        datasets["class"] = []
    service.import_all(datasets)
    with school() as c:
        assert c.execute("SELECT weekday FROM class_meeting").fetchall() == [(5,)]
        assert (
            c.execute("SELECT schedule FROM class WHERE class_id='C'").fetchone()[0]
            == "F 11:00–12:00"
        )


def test_import_can_clear_previously_supplied_optional_values(school):
    service = SchoolDataImportService()
    with school() as c:
        c.execute("UPDATE student SET email='old@example.edu' WHERE student_id='S'")
    datasets = {table: [] for table, *_ in DATASETS}
    datasets["student"] = [
        dict(
            student_id="S",
            first_name="Juan",
            last_name="Dela Cruz",
            program="BSCS",
            status="Active",
            year_level=2,
            email="",
        )
    ]
    service.import_all(datasets)
    with school() as c:
        assert (
            c.execute("SELECT email FROM student WHERE student_id='S'").fetchone()[0]
            is None
        )
