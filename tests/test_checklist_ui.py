from PySide6.QtWidgets import QApplication

from app.gui.pyside_app import StudentDialog, ScoreDialog


def test_student_editor_preserves_id_and_year_level():
    app = QApplication.instance() or QApplication([])
    dialog = StudentDialog(student=('2026-0001','Juan','Dela Cruz',None,'BSCS','Active',2))
    assert dialog.fields['student_id'].isReadOnly()
    assert dialog.values()['email'] == ''
    assert int(dialog.values()['year_level']) == 2
    dialog.close()


def test_score_editor_reloads_saved_values_for_correction():
    app = QApplication.instance() or QApplication([])
    component = ('C','Midterm Exam','Exam',100)
    saved = [dict(component_id='C',score_id='original-score',score=57,remarks='Check')]
    dialog = ScoreDialog(None,'E',[component],scores=saved)
    assert dialog.score.text() == '57'
    dialog.score.setText('75')
    assert dialog.values() == ('original-score','C','75','Check')
    dialog.close()
