"""Reusable master/configuration editing without database access in the UI."""
from datetime import date

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QComboBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
)


# Field order matches the existing application-service contracts.
RECORDS = {
    'Teachers': ('teachers', 'teacher', 'teacher_id first_name last_name email department status'),
    'Subjects': ('subjects', 'subject', 'subject_id subject_code subject_name description units'),
    'Grading Periods': ('grading_periods', 'period', 'period_id name start_date end_date school_year semester period_order'),
    'Class Offerings': ('class_offerings', 'offering', 'offering_id class_code schedule section school_year semester room teacher_id subject_id'),
    'Weights': ('grade_percentages', 'percentage', 'percentage_id percentage offering_id'),
    'Components': ('grade_components', 'component', 'component_id name type max_score description period_id percentage_id'),
}
REFERENCES = {
    'teacher_id': ('teachers', 'teacher_id', 'last_name'),
    'subject_id': ('subjects', 'subject_id', 'subject_name'),
    'offering_id': ('class_offerings', 'offering_id', 'class_code'),
    'period_id': ('grading_periods', 'period_id', 'name'),
    'percentage_id': ('grade_percentages', 'percentage_id', 'percentage'),
}


class RecordDialog(QDialog):
    def __init__(self, parent, title, fields, records, record=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(460)
        self.fields = fields
        self.inputs = {}
        root = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)
        root.addLayout(form)
        for index, field in enumerate(fields):
            value = str((record or {}).get(field) or '')
            if index and field in REFERENCES:
                source, key, label = REFERENCES[field]
                widget = QComboBox()
                for row in records[source]:
                    widget.addItem(f"{row[key]} · {row[label]}", row[key])
                if value:
                    widget.setCurrentIndex(widget.findData(value))
            else:
                widget = QLineEdit(value)
                if not record and field == 'period_order':
                    widget.setText(str(len(records['grading_periods'])+1))
                if field == 'email':
                    widget.setPlaceholderText('Optional')
                if field.endswith('_date'):
                    widget.setPlaceholderText('YYYY-MM-DD')
                if record and index == 0:
                    widget.setReadOnly(True)
            form.addRow(field.replace('_', ' ').title(), widget)
            self.inputs[field] = widget
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def values(self):
        result = []
        for field in self.fields:
            widget = self.inputs[field]
            value = widget.currentData() if isinstance(widget, QComboBox) else widget.text().strip()
            if field.endswith('_date'):
                value = date.fromisoformat(value)
            result.append(value)
        return result


def add_editor_actions(layout, app, name, table):
    actions = QHBoxLayout()
    permission = 'grading' if name in ['Weights', 'Components'] else 'academic'
    for label, editing in [('Add', False), ('Edit selected', True)]:
        control = QPushButton(label)
        control.setEnabled(app.can(permission))
        control.clicked.connect(lambda checked=False, edit=editing: edit_record(app, name, table, edit))
        actions.addWidget(control)
    actions.addStretch()
    delete = QPushButton('Delete selected')
    delete.setEnabled(app.can('delete'))
    delete.clicked.connect(lambda: delete_record(app, name, table))
    actions.addWidget(delete)
    layout.addLayout(actions)


def selected_id(app, table):
    row = table.currentRow()
    if row < 0:
        app.warning('Select a record first.')
        return None
    return table.item(row, 0).text()


def edit_record(app, name, table, editing):
    source, method, field_names = RECORDS[name]
    fields = field_names.split()
    records = app.data.records()
    record = None
    if editing:
        identifier = selected_id(app, table)
        if identifier is None:
            return
        record = next((r for r in records[source] if r[fields[0]] == identifier), None)
        if record is None:
            return
    dialog = RecordDialog(app, f'{"Edit" if editing else "Add"} {name}', fields, records, record)
    if dialog.exec() != QDialog.Accepted:
        return
    try:
        values = dialog.values()
        if not editing and any(r[fields[0]] == values[0] for r in records[source]):
            raise ValueError('This ID already exists. Use Edit selected instead.')
        operation = getattr(app.academic_service, f'save_{method}')
        app.run_write(lambda: operation(*values), 'Record saved.')
    except (ValueError, TypeError) as error:
        app.error(str(error))


def delete_record(app, name, table):
    identifier = selected_id(app, table)
    if identifier is None:
        return
    if QMessageBox.question(app, 'Delete record', f'Delete {identifier}? Referenced records cannot be deleted.') != QMessageBox.Yes:
        return
    source, _, fields = RECORDS[name]
    app.run_write(lambda: app.academic_service.delete_unreferenced(source, identifier), 'Record deleted.')
