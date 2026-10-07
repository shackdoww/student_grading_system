from datetime import date
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication, QLineEdit

from app.services.enrollment_service import EnrollmentService
from app.gui.pyside_app import ScoreDialog


def service():
    result = EnrollmentService()
    result.repository = MagicMock()
    result.student_repository = MagicMock()
    result.offering_repository = MagicMock()
    result.repository.find_by_student_and_offering.return_value = None
    return result


def test_enrollment_keys_are_generated_unique_and_create_only():
    subject = service()
    keys = [subject.enroll('S1', f'O{i}') for i in range(50)]
    assert len(set(keys)) == 50
    assert all(k.startswith('E-') and len(k) == 34 for k in keys)
    assert subject.repository.create.call_count == 50
    subject.repository.save.assert_not_called()
    assert subject.repository.create.call_args.args[1] == date.today()


def test_duplicate_enrollment_does_not_create_or_leak_internal_key():
    subject = service()
    subject.repository.find_by_student_and_offering.return_value = 'internal-key'
    with pytest.raises(ValueError, match='already enrolled') as error:
        subject.enroll('S1', 'O1')
    assert 'internal-key' not in str(error.value)
    subject.repository.create.assert_not_called()


@pytest.mark.parametrize('missing', ['student', 'offering'])
def test_invalid_membership_does_not_create(missing):
    subject = service()
    getattr(subject, missing + '_repository').find_by_id.return_value = None
    with pytest.raises(ValueError):
        subject.enroll('S1', 'O1')
    subject.repository.create.assert_not_called()


def test_score_dialog_requires_no_manual_key():
    app = QApplication.instance() or QApplication([])
    component = ('C', 'Quiz', 'Quiz', 20)
    dialog = ScoreDialog(None, 'internal-enrollment', [component])
    assert len(dialog.findChildren(QLineEdit)) == 2  # Score and remarks only.
    dialog.score.setText('18')
    key, cid, score, remarks = dialog.values()
    assert key.startswith('SC-') and 'internal-enrollment' not in key
    assert (cid, score, remarks) == ('C', '18', '')
    assert dialog.values()[0] == key
    dialog.close()
