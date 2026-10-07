import ast
from pathlib import Path

from PySide6.QtWidgets import QApplication, QProgressBar
from app.gui.program_distribution import ProgramDistribution, program_counts


ROOT = Path(__file__).resolve().parents[1]


def test_single_launcher_and_no_tkinter_imports():
    assert not (ROOT / 'gui.py').exists()
    assert not (ROOT / 'app/gui/app.py').exists()
    assert not (ROOT / 'app/gui/modern_app.py').exists()
    for path in (ROOT / 'app').rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            modules = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ''] if isinstance(node, ast.ImportFrom) else []
            assert not any(m.split('.')[0] in {'tkinter', 'customtkinter'} for m in modules), path
    assert 'customtkinter' not in (ROOT / 'requirements.txt').read_text()


def students(programs):
    return [(str(i), 'First', 'Last', 'email', program, 'Active') for i, program in enumerate(programs)]


def test_program_distribution_keeps_totals_and_limits_rows():
    records = students(['CS'] * 3 + ['IT'] * 2 + ['IS', 'Math', 'Arts', 'Science'])
    counts = program_counts(records)
    assert len(counts) == 4
    assert counts[0] == ('CS', 3)
    assert counts[-1][0] == 'Other programs'
    assert sum(value for _, value in counts) == len(records)


def test_distribution_empty_state_and_reduced_motion(monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setenv('STUDENT_HUB_REDUCED_MOTION', '1')
    widget = ProgramDistribution()
    assert widget.root.count() == 1
    widget.set_counts(students(['CS', 'CS', 'IT', 'IT']))
    bars = widget.findChildren(QProgressBar)
    assert len(bars) == 2
    assert [bar.value() for bar in bars] == [500, 500]
    assert not widget.animations
    widget.close()
