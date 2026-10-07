"""Spreadsheet export and native printing for the currently displayed records."""

import csv
from html import escape

from PySide6.QtCore import QMarginsF
from PySide6.QtGui import QPageLayout, QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PySide6.QtWidgets import QFileDialog, QMessageBox


def table_data(widget):
    headers = [widget.horizontalHeaderItem(c).text() for c in range(widget.columnCount())]
    rows = [[widget.item(r, c).text() if widget.item(r, c) else ""
             for c in range(widget.columnCount())]
            for r in range(widget.rowCount()) if not widget.isRowHidden(r)]
    return headers, rows


def spreadsheet_cell(value):
    # Treat untrusted identifiers and text as text, never spreadsheet formulas.
    if value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def write_csv(path, headers, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as output:
        writer = csv.writer(output)
        writer.writerow([spreadsheet_cell(str(value)) for value in headers])
        writer.writerows([[spreadsheet_cell(str(value)) for value in row] for row in rows])


def export_table(parent, widget, title):
    path, _ = QFileDialog.getSaveFileName(parent, "Export spreadsheet", title + ".csv", "CSV spreadsheet (*.csv)")
    if not path:
        return
    if not path.lower().endswith(".csv"):
        path += ".csv"
    try:
        headers, rows = table_data(widget)
        write_csv(path, headers, rows)
        QMessageBox.information(parent, "Export complete", f"Exported {len(rows)} records to:\n{path}")
    except OSError as error:
        QMessageBox.critical(parent, "Export failed", str(error))


def report_html(title, headers, rows):
    heading = "".join(f"<th>{escape(str(value))}</th>" for value in headers)
    body = "".join("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>" for row in rows)
    return ("<style>body {font-family: sans-serif; font-size: 10pt;} "
            "th {background: #e9eeff; text-align: left;} td, th {padding: 6px;} "
            "table {border-collapse: collapse;}</style>"
            f"<h1>Student Hub</h1><h2>{escape(title)}</h2><p>{len(rows)} records</p>"
            f'<table border="1" cellspacing="0" width="100%"><thead><tr>{heading}</tr></thead><tbody>{body}</tbody></table>')


def print_table(parent, widget, title):
    headers, rows = table_data(widget)
    document = QTextDocument()
    document.setHtml(report_html(title, headers, rows))
    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageOrientation(QPageLayout.Landscape)
    printer.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Millimeter)
    printer.setDocName(title)
    preview = QPrintPreviewDialog(printer, parent)
    preview.setWindowTitle(f"Print preview | {title}")
    preview.resize(1000, 720)
    preview.paintRequested.connect(document.print_)
    preview.exec()
