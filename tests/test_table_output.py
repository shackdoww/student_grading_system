import csv

from app.gui.table_output import report_html, write_csv


def test_csv_preserves_unicode_and_quotes_and_neutralizes_formulas(tmp_path):
    path = tmp_path / 'records.csv'
    write_csv(path, ['Name', 'Remarks'], [['José, Cruz', 'line one\nline two'], ['Student', '=HYPERLINK("bad")']])
    with path.open(encoding='utf-8-sig', newline='') as source:
        rows = list(csv.reader(source))
    assert rows[1] == ['José, Cruz', 'line one\nline two']
    assert rows[2][1].startswith("'=")


def test_print_report_escapes_school_record_text():
    result = report_html('Grades <2026>', ['Student'], [['<img src="bad">']])
    assert '<img' not in result
    assert '&lt;img' in result
    assert 'Grades &lt;2026&gt;' in result
