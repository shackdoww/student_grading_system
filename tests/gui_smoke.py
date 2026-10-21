"""Manual integration smoke check using the configured PostgreSQL database."""
import sys
from time import perf_counter
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QApplication, QMessageBox

from app.gui.pyside_app import StudentHub, StudentDialog, ScoreDialog, STYLE
from tests.ui_helpers import admin_window
from app.gui.table_output import table_data, report_html, write_csv


def main():
    app = QApplication([])
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    errors = []
    original = StudentHub.error
    StudentHub.error = lambda self, message: errors.append(message)
    started = perf_counter()
    window = admin_window()
    print(f'Window construction: {perf_counter() - started:.3f}s')
    StudentHub.error = original
    window.error = lambda message: errors.append(message)
    window.show()
    deadline = perf_counter() + 20
    while window._data_version == 0 and not errors and perf_counter() < deadline:
        QTest.qWait(10)
    assert window._data_version > 0, errors or 'Data loading timed out'
    print(f'Initial data ready: {perf_counter() - started:.3f}s')
    assert window.windowFlags() & Qt.FramelessWindowHint
    with TemporaryDirectory() as folder:
        for size in ((1100, 700), (1280, 800), (1440, 900)):
            window.resize(*size)
            window.show()
            for key in window.pages:
                switched = perf_counter()
                window.show_page(key)
                print(f'{size}: {key} switch {1000 * (perf_counter() - switched):.1f}ms')
                app.processEvents()
                assert window.size().width() == size[0], (key, window.size())
                if key != 'import':
                    assert window.output_table.count()
        window.showMaximized()
        app.processEvents()
        window.showNormal()
        window.resize(1280, 800)
        window.show_page('dashboard')
        QTest.qWait(260)
        window.grab().save(str(Path(folder) / 'dashboard.png'))
        if len(sys.argv) > 1:
            if len(sys.argv) > 2:
                window.show_page(sys.argv[2])
                QTest.qWait(260)
            window.grab().save(sys.argv[1])
        headers, rows = table_data(window.dashboard.student_table)
        write_csv(Path(folder) / 'student.csv', headers, rows)
        document = QTextDocument()
        document.setHtml(report_html('Students', headers, rows))
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(str(Path(folder) / 'student.pdf'))
        document.print_(printer)
        assert (Path(folder) / 'student.pdf').stat().st_size > 500
        for dialog in (StudentDialog(window), ScoreDialog(window, 'smoke', [])):
            dialog.show()
            app.processEvents()
            dialog.reject()
        # Validate import UI without executing any database writes.
        page = window.import_page
        page.folder = str(Path(__file__).resolve().parents[1] / 'test_data')
        original_warning = QMessageBox.warning
        QMessageBox.warning = lambda *args: QMessageBox.Ok
        page.validate()
        deadline = perf_counter() + 20
        while getattr(page, '_validating', False) and perf_counter() < deadline:
            QTest.qWait(10)
        QMessageBox.warning = original_warning
        assert 'passed' in page.status.text().lower() or 'failed' in page.status.text().lower()
    window.close()
    assert not errors, errors
    print('All pages, window sizes, dialogs, CSV, PDF rendering and import validation passed.')


if __name__ == '__main__':
    main()
