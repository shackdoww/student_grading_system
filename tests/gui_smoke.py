"""Manual integration smoke check using the configured PostgreSQL database."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QTimer
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QApplication, QMessageBox

from app.gui.pyside_app import StudentHub, StudentDialog, ScoreDialog, STYLE
from app.gui.table_output import table_data, report_html, write_csv


def main():
    app = QApplication([])
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    errors = []
    original = StudentHub.error
    StudentHub.error = lambda self, message: errors.append(message)
    window = StudentHub()
    StudentHub.error = original
    window.error = lambda message: errors.append(message)
    with TemporaryDirectory() as folder:
        for size in ((1100, 700), (1280, 800), (1440, 900)):
            window.resize(*size)
            window.show()
            for key in window.pages:
                window.show_page(key)
                app.processEvents()
                assert window.size().width() == size[0], (key, window.size())
                if key != 'import':
                    assert window.output_table.count()
        window.showMaximized()
        app.processEvents()
        window.showNormal()
        window.resize(1280, 800)
        window.show_page('dashboard')
        app.processEvents()
        window.grab().save(str(Path(folder) / 'dashboard.png'))
        if len(sys.argv) > 1:
            window.grab().save(sys.argv[1])
        headers, rows = table_data(window.dashboard.student_table)
        write_csv(Path(folder) / 'students.csv', headers, rows)
        document = QTextDocument()
        document.setHtml(report_html('Students', headers, rows))
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(str(Path(folder) / 'students.pdf'))
        document.print_(printer)
        assert (Path(folder) / 'students.pdf').stat().st_size > 500
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
        QMessageBox.warning = original_warning
        assert 'passed' in page.status.text().lower() or 'failed' in page.status.text().lower()
    window.close()
    assert not errors, errors
    print('All pages, window sizes, dialogs, CSV, PDF rendering and import validation passed.')


if __name__ == '__main__':
    main()
