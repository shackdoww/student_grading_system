from decimal import Decimal
import pytest
from app.services.academic_service import AcademicService
from app.services.period_grading_service import PeriodGradingService
from app.services.score_service import ScoreService
from app.services.account_service import AccountService
from app.services.access_control import AccessGuard, SecuredService


def policy(class_id="C"):
    return dict(
        class_id=class_id,
        midterm_period_id="M",
        final_period_id="F",
        midterm_weight=40,
        final_weight=60,
    )


def weights():
    return [
        dict(component_id=p + c, percentage=w)
        for p in ("M", "F")
        for c, w in [("Q", 20), ("L", 30), ("E", 50)]
    ]


def test_normal_services_save_canonical_grade_and_recompute_in_place(school):
    service = PeriodGradingService(connection_factory=school)
    service.save_policy(policy(), weights())
    scores = ScoreService()
    for cid, value in zip(
        ["MQ", "ML", "ME", "FQ", "FL", "FE"], [40, 90, 57, 45, 85, 80]
    ):
        scores.record_score("S-" + cid, "E", cid, value)
    scores.record_score("ignored-new-id", "E", "ME", 75)
    assert service.calculate_and_save("E") == dict(
        midterm=80.5, final=83.5, overall=82.3
    )
    updated = weights()
    updated[0]["percentage"] = 30
    updated[2]["percentage"] = 40
    service.save_policy(policy(), updated)
    service.calculate_and_save("E")
    with school() as c:
        assert c.execute(
            "SELECT midterm_grade,finals_grade,overall_grade,midterm_equiv,final_equiv FROM grade"
        ).fetchone() == (
            81,
            Decimal("83.50"),
            Decimal("82.50"),
            Decimal("2.5"),
            Decimal("2.25"),
        )
        assert c.execute("SELECT count(*) FROM grade").fetchone()[0] == 1
        assert c.execute(
            "SELECT score_id,score FROM grade_component_score WHERE component_id='ME'"
        ).fetchone() == ("S-ME", 75)
        assert c.execute("SELECT count(*) FROM grade_percentage").fetchone()[0] == 6


def test_midterm_save_without_finals_and_missing_full_grade(school):
    service = PeriodGradingService(connection_factory=school)
    service.save_policy(policy(), weights())
    for cid, value in [("MQ", 40), ("ML", 90), ("ME", 75)]:
        ScoreService().record_score("S-" + cid, "E", cid, value)
    result = service.calculate_and_save("E", period="midterm")
    assert result["midterm"] == 80.5
    with school() as c:
        assert c.execute(
            "SELECT midterm_equiv,final_equiv,overall_grade FROM grade"
        ).fetchone() == (Decimal("2.5"), None, None)
    with pytest.raises(ValueError, match="Missing score"):
        service.calculate_and_save("E")


def test_shared_component_contract_has_no_percentage_parent(school):
    AcademicService().save_component("NEW", "Additional Quiz", "Quiz", 25, "", "M")
    with school() as c:
        assert c.execute(
            "SELECT period_id,max_score FROM grade_component WHERE component_id='NEW'"
        ).fetchone() == ("M", 25)


def test_secured_writes_capture_source_and_actual_actor(school):
    auth = AccountService(connection_factory=school)
    auth.create_account(
        "admin", "Admin", "Testing Student Hub 2026!", "admin", first_admin=True
    )
    token = auth.authenticate("admin", "Testing Student Hub 2026!")
    secured = SecuredService(
        PeriodGradingService(connection_factory=school), AccessGuard(auth, token)
    )
    secured.save_policy(policy(), weights(), source_reference="GW-01")
    updated = weights()
    updated[0]["percentage"] = 30
    updated[2]["percentage"] = 40
    secured.save_policy(policy(), updated, source_reference="GR-03")
    with school() as c:
        assert c.execute(
            "SELECT set_by,created_by,updated_by FROM grade_percentage WHERE component_id='MQ'"
        ).fetchone() == ("GW-01; GR-03", "admin", "admin")
        events = c.execute(
            "SELECT changed_by,source_reference,old_value->>'percentage',new_value->>'percentage' FROM audit_log WHERE table_name='GRADE_PERCENTAGE' AND action='UPDATE'"
        ).fetchall()
        assert len(events) == 2
        assert all(r[:2] == ("admin", "GR-03") for r in events)


def test_teacher_cannot_edit_shared_definitions(school):
    auth = AccountService(connection_factory=school)
    auth.create_account(
        "admin", "Admin", "Testing Student Hub 2026!", "admin", first_admin=True
    )
    token = auth.authenticate("admin", "Testing Student Hub 2026!")
    auth.create_account(
        "teacher", "Teacher", "Testing Student Hub 2026!", "teacher", "T", token=token
    )
    teacher = auth.authenticate("teacher", "Testing Student Hub 2026!")
    service = SecuredService(AcademicService(), AccessGuard(auth, teacher))
    with pytest.raises(PermissionError):
        service.save_component("MQ", "Changed", "Quiz", 50, "", "M")
