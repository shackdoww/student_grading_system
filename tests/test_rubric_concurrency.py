from concurrent.futures import ThreadPoolExecutor
import pytest
from app.services.enrollment_service import EnrollmentService
from app.services.student_service import StudentService


def test_concurrent_enrollment_preserves_single_membership(school):
    with school() as c:
        c.execute("DELETE FROM enrollment WHERE enrollment_id='E'")

    def add():
        try:
            return EnrollmentService().enroll("S", "C")
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: add(), range(2)))
    assert sum(r is not None for r in results) == 1
    with school() as c:
        assert c.execute("SELECT count(*) FROM enrollment").fetchone()[0] == 1


def test_concurrent_student_creation_never_overwrites(school):
    def add(name):
        try:
            StudentService().create("NEW", name, "Student", "", "BSCS", "Active", 2)
            return name
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(add, ["First", "Second"]))
    winner = next(r for r in results if r)
    assert sum(r is not None for r in results) == 1
    with school() as c:
        assert (
            c.execute(
                "SELECT first_name FROM student WHERE student_id='NEW'"
            ).fetchone()[0]
            == winner
        )
