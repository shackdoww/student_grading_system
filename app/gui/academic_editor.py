"""Reusable master/configuration editing without database access in the UI."""
from datetime import date

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QComboBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
)


# Field order matches the existing application-service contracts.
RECORDS = {
    'Teachers': ('teacher', 'teacher', 'teacher_id first_name last_name email department status'),
    'Subjects': ('subject', 'subject', 'subject_id subject_code subject_name description units'),
    'Grading Periods': ('grading_period', 'period', 'period_id name start_date end_date school_year semester period_order'),
    'Class Offerings': ('class', 'offering', 'class_id class_code schedule section school_year semester room teacher_id subject_id'),
    'Components': ('grade_component', 'component', 'component_id name type max_score description period_id'),
}
REFERENCES = {
    'teacher_id': ('teacher', 'teacher_id', 'last_name'),
    'subject_id': ('subject', 'subject_id', 'subject_name'),
    'class_id': ('class', 'class_id', 'class_code'),
    'period_id': ('grading_period', 'period_id', 'name'),
    'percentage_id': ('grade_percentage', 'percentage_id', 'percentage'),
}


class RecordDialog(QDialog):
    def __init__(self, parent, title, fields, records, record=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        # Weekdays, two AM/PM controls and Remove block stay visible even when
        # the dialog is resized to its minimum width.
        self.setMinimumWidth(680 if 'schedule' in fields else 460)
        self.fields = fields
        self.inputs = {}
        root = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)
        root.addLayout(form)
        for index, field in enumerate(fields):
            value = str((record or {}).get(field) or '')
            if field == 'schedule':
                from app.gui.schedule_editor import ScheduleEditor
                meetings=[r for r in records.get('class_meeting',[]) if r['class_id']==(record or {}).get('class_id')]
                widget=ScheduleEditor(self,meetings,value)
            elif index and field in REFERENCES:
                source, key, label = REFERENCES[field]
                widget = QComboBox()
                for row in records[source]:
                    widget.addItem(f"{row[key]} · {row[label]}", row[key])
                if value:
                    widget.setCurrentIndex(widget.findData(value))
            else:
                widget = QLineEdit(value)
                if not record and field == 'period_order':
                    widget.setText(str(len(records['grading_period'])+1))
                if field == 'email':
                    widget.setPlaceholderText('Optional')
                if field.endswith('_date'):
                    widget.setPlaceholderText('YYYY-MM-DD')
                if record and index == 0:
                    widget.setReadOnly(True)
            form.addRow(field.replace('_', ' ').title(), widget)
            self.inputs[field] = widget
        self.source = QLineEdit()
        self.source.setPlaceholderText('Optional source / reference')
        form.addRow('Source / reference', self.source)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def values(self):
        result = []
        for field in self.fields:
            widget = self.inputs[field]
            if field == 'schedule':
                result.append(widget.values())
                continue
            value = widget.currentData() if isinstance(widget, QComboBox) else widget.text().strip()
            if field.endswith('_date'):
                value = date.fromisoformat(value)
            result.append(value)
        return result


def add_editor_actions(layout, app, name, table):
    actions = QHBoxLayout()
    permission = 'academic'
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
        operation = getattr(app.academic_service, 'create_teacher' if name=='Teachers' and not editing else f'save_{method}')
        reference=dialog.source.text().strip() or None
        app.run_write(lambda: operation(*values,source_reference=reference), 'Record saved.')
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
