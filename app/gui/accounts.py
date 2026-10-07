from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QWidget, QHBoxLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView)
from app.gui.background import BackgroundJobs
from app.services.account_service import ROLES
from app.services.record_deletion_service import DELETABLE


class LoginDialog(QDialog):
    def __init__(self, auth):
        super().__init__()
        self.auth, self.token, self.setup = auth, None, False
        self.setWindowTitle('Student Hub · Sign in')
        self.setMinimumWidth(440)
        self.jobs = BackgroundJobs(self)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        self.title = QLabel('Welcome to Student Hub')
        self.title.setObjectName('pageTitle')
        root.addWidget(self.title)
        self.hint = QLabel('Checking account setup…')
        self.hint.setWordWrap(True)
        root.addWidget(self.hint)
        form = QFormLayout()
        form.setSpacing(12)
        self.username, self.name = QLineEdit(), QLineEdit()
        self.password, self.confirm = QLineEdit(), QLineEdit()
        for field in [self.password, self.confirm]:
            field.setEchoMode(QLineEdit.Password)
        self.name_label, self.confirm_label = QLabel('Your name'), QLabel('Confirm password')
        form.addRow('Username', self.username)
        form.addRow(self.name_label, self.name)
        form.addRow('Password', self.password)
        form.addRow(self.confirm_label, self.confirm)
        root.addLayout(form)
        self.submit = QPushButton('Sign in')
        self.submit.setProperty('primary', True)
        self.submit.setEnabled(False)
        self.submit.clicked.connect(self.sign_in)
        root.addWidget(self.submit)
        self.password.returnPressed.connect(self.sign_in)
        QTimer.singleShot(0, self.check_setup)

    def check_setup(self):
        def ready(setup):
            self.setup = setup
            for field in [self.name, self.name_label, self.confirm, self.confirm_label]:
                field.setVisible(setup)
            self.title.setText('Create the first Admin' if setup else 'Welcome back')
            self.hint.setText('Choose a username and a 15–128 character passphrase. This initial account will be the Admin.' if setup else 'Sign in with your school account.')
            self.submit.setText('Create Admin and sign in' if setup else 'Sign in')
            self.submit.setEnabled(True)
        self.jobs.submit(self.auth.needs_setup, ready, lambda message: self.hint.setText(message))

    def sign_in(self):
        if not self.submit.isEnabled():
            return
        username, password, name = self.username.text(), self.password.text(), self.name.text()
        if self.setup and password != self.confirm.text():
            self.hint.setText('The passwords do not match.')
            return
        self.submit.setEnabled(False)
        setup = self.setup
        def work():
            if setup:
                self.auth.create_account(username, name, password, 'admin', first_admin=True)
            return self.auth.authenticate(username, password)
        def done(token):
            self.token = token
            self.password.clear()
            self.confirm.clear()
            self.accept()
        def failed(message):
            self.hint.setText(message)
            self.submit.setEnabled(True)
        self.jobs.submit(work, done, failed)

    def closeEvent(self, event):
        self.jobs.detach()
        super().closeEvent(event)


class NewAccountDialog(QDialog):
    def __init__(self, parent, teachers):
        super().__init__(parent)
        self.setWindowTitle('Create school account')
        self.setMinimumWidth(460)
        form = QFormLayout(self)
        self.username, self.name, self.password, self.confirm = [QLineEdit() for _ in range(4)]
        self.password.setEchoMode(QLineEdit.Password)
        self.confirm.setEchoMode(QLineEdit.Password)
        self.role, self.teacher = QComboBox(), QComboBox()
        for role, label in ROLES.items():
            self.role.addItem(label, role)
        self.role.setCurrentIndex(self.role.findData('registrar'))
        for row in teachers:
            self.teacher.addItem(f'{row[0]} · {row[1]} {row[2]}', row[0])
        self.role.currentIndexChanged.connect(lambda: self.teacher.setEnabled(self.role.currentData() == 'teacher'))
        self.teacher.setEnabled(False)
        for label, field in [('Username', self.username), ('Full name', self.name), ('Password (15–128 characters)', self.password), ('Confirm password', self.confirm), ('Role', self.role), ('Teacher record', self.teacher)]:
            form.addRow(label, field)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)


class AccountsPage(QWidget):
    def __init__(self, app, table_factory, fill_table):
        super().__init__()
        self.app, self.fill_table = app, fill_table
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 20)
        title = QLabel('School accounts')
        title.setObjectName('pageTitle')
        root.addWidget(title)
        root.addWidget(QLabel('Admins manage access. Disable an account to revoke its sessions.'))
        actions = QHBoxLayout()
        create = QPushButton('Create account')
        create.clicked.connect(self.create)
        actions.addWidget(create)
        toggle = QPushButton('Enable / disable selected')
        toggle.clicked.connect(self.toggle)
        actions.addWidget(toggle)
        access = QPushButton('Change selected role')
        access.clicked.connect(self.change_role)
        actions.addWidget(access)
        actions.addStretch()
        root.addLayout(actions)
        self.list = table_factory(['Username', 'Name', 'Role', 'Teacher', 'Active'])
        self.list.setProperty('outputTitle', 'School accounts')
        root.addWidget(self.list, 1)
        self.rows = []

    def refresh(self):
        def done(rows):
            self.rows = rows
            self.fill_table(self.list, [(r['username'], r['full_name'], ROLES[r['role']], r['teacher_id'] or '—', 'Yes' if r['active'] else 'No') for r in rows])
        self.app.jobs.submit(lambda: self.app.auth.list_accounts(self.app.session), done, self.app.error)

    def create(self):
        dialog = NewAccountDialog(self, self.app.data.teachers())
        if dialog.exec() != QDialog.Accepted:
            return
        if dialog.password.text() != dialog.confirm.text():
            self.app.warning('The passwords do not match.')
            return
        args = (dialog.username.text(), dialog.name.text(), dialog.password.text(), dialog.role.currentData(),
                dialog.teacher.currentData() if dialog.role.currentData() == 'teacher' else None)
        dialog.password.clear()
        dialog.confirm.clear()
        self.app.run_write(lambda: self.app.auth.create_account(*args, token=self.app.session), 'Account created.', lambda _: self.refresh())

    def toggle(self):
        row = self.list.currentRow()
        if row < 0 or row >= len(self.rows):
            return
        account = self.rows[row]
        active = not account['active']
        if QMessageBox.question(self, 'Change account access', f'{"Enable" if active else "Disable"} {account["username"]}?') != QMessageBox.Yes:
            return
        self.app.run_write(lambda: self.app.auth.set_active(self.app.session, account['user_id'], active), 'Account access updated.', lambda _: self.refresh())

    def change_role(self):
        row = self.list.currentRow()
        if row < 0 or row >= len(self.rows):
            return
        account = self.rows[row]
        dialog = QDialog(self)
        dialog.setWindowTitle('Change account role')
        form = QFormLayout(dialog)
        form.addRow(QLabel(account['username']))
        role, teacher = QComboBox(), QComboBox()
        for key, label in ROLES.items():
            role.addItem(label, key)
        role.setCurrentIndex(role.findData(account['role']))
        for t in self.app.data.teachers():
            teacher.addItem(f'{t[0]} · {t[1]} {t[2]}', t[0])
        if account['teacher_id']:
            teacher.setCurrentIndex(teacher.findData(account['teacher_id']))
        teacher.setEnabled(role.currentData() == 'teacher')
        role.currentIndexChanged.connect(lambda: teacher.setEnabled(role.currentData() == 'teacher'))
        form.addRow('Role', role)
        form.addRow('Teacher record', teacher)
        form.addRow(QLabel('This change signs the account out of all sessions.'))
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.Accepted:
            return
        args = (self.app.session, account['user_id'], role.currentData(), teacher.currentData() if role.currentData() == 'teacher' else None)
        self.app.run_write(lambda: self.app.auth.change_role(*args), 'Account role updated.', lambda _: self.refresh())


class DataRecordsPage(QWidget):
    def __init__(self, app, table_factory, fill_table):
        super().__init__()
        self.app, self.fill_table = app, fill_table
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 20)
        heading = QLabel('Data records')
        heading.setObjectName('pageTitle')
        root.addWidget(heading)
        hint = QLabel('Admin only. Delete grades and scores before enrollments, then dependent configuration before master records. No automatic cascades or backups.')
        hint.setWordWrap(True)
        root.addWidget(hint)
        self.kind = QComboBox()
        for name in ['period_grade_results', 'grades', 'grade_component_scores', 'enrollments', 'students', 'grading_policies', 'grade_components', 'grade_percentages', 'class_offerings', 'grading_periods', 'subjects', 'teachers']:
            self.kind.addItem(name.replace('_', ' ').title(), name)
        self.kind.currentIndexChanged.connect(self.refresh)
        root.addWidget(self.kind)
        actions = QHBoxLayout()
        self.select_all = QPushButton('Select all')
        self.clear_selection = QPushButton('Clear selection')
        self.select_all.clicked.connect(lambda: self.set_checked(True))
        self.clear_selection.clicked.connect(lambda: self.set_checked(False))
        actions.addWidget(self.select_all)
        actions.addWidget(self.clear_selection)
        actions.addStretch()
        self.selection_count = QLabel('0 selected')
        actions.addWidget(self.selection_count)
        root.addLayout(actions)
        self.list = table_factory(['Records'])
        self.list.itemChanged.connect(self.update_selection)
        self.list.setProperty('outputTitle', 'Data records')
        root.addWidget(self.list, 1)
        self.delete_button = QPushButton('Delete selected records permanently')
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.delete)
        root.addWidget(self.delete_button)
        self.rows = []
        self._dataset = None

    def checked_keys(self):
        return [self.list.item(row, 0).data(Qt.UserRole)
                for row in range(self.list.rowCount())
                if self.list.item(row, 0) is not None
                and self.list.item(row, 0).checkState() == Qt.Checked]

    def update_selection(self, *_):
        count = len(self.checked_keys())
        self.selection_count.setText(f'{count} of {self.list.rowCount()} selected')
        self.delete_button.setEnabled(count > 0)
        self.select_all.setEnabled(self.list.rowCount() > 0)
        self.clear_selection.setEnabled(count > 0)

    def set_checked(self, checked):
        blocked = self.list.blockSignals(True)
        for row in range(self.list.rowCount()):
            self.list.item(row, 0).setCheckState(Qt.Checked if checked else Qt.Unchecked)
        self.list.blockSignals(blocked)
        self.update_selection()

    def refresh(self):
        name = self.kind.currentData()
        selected = set(self.checked_keys()) if name == self._dataset else set()
        self._dataset = name
        self.rows = self.app.data.records()[name]
        fields = list(self.rows[0]) if self.rows else [DELETABLE[name][0]]
        blocked = self.list.blockSignals(True)
        self.list.setColumnCount(len(fields) + 1)
        self.list.setHorizontalHeaderLabels(['Select'] + [k.replace('_', ' ').title() for k in fields])
        self.fill_table(self.list, [[''] + [row[k] for k in fields] for row in self.rows])
        key_field = DELETABLE[name][0]
        for index, row in enumerate(self.rows):
            item = self.list.item(index, 0)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
            item.setData(Qt.UserRole, row[key_field])
            item.setToolTip(f'Select {row[key_field]} for deletion')
            item.setCheckState(Qt.Checked if row[key_field] in selected else Qt.Unchecked)
        self.list.horizontalHeader().setMinimumSectionSize(52)
        self.list.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.list.horizontalHeader().setSectionResizeMode(len(fields), QHeaderView.Stretch)
        self.list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.list.setColumnWidth(0, 64)
        self.list.blockSignals(blocked)
        self.update_selection()

    def delete(self):
        keys = tuple(self.checked_keys())
        if not keys:
            return
        name = self.kind.currentData()
        related = '\nThis also removes the policy’s category-weight configuration.' if name == 'grading_policies' else ''
        confirmation = QMessageBox(self)
        confirmation.setWindowTitle('Permanent batch deletion')
        confirmation.setIcon(QMessageBox.Warning)
        confirmation.setText(f'Delete {len(keys)} selected {name.replace("_", " ")} record(s)?')
        preview = ', '.join(str(key) for key in keys[:10])
        if len(keys) > 10:
            preview += f' and {len(keys) - 10} more (see details)'
        confirmation.setInformativeText(f'{preview}{related}\nThis cannot be undone. No backup will be made.\nIf any record is blocked, the entire batch will be cancelled.')
        confirmation.setDetailedText('\n'.join(str(key) for key in keys))
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirmation.setDefaultButton(QMessageBox.No)
        if confirmation.exec() != QMessageBox.Yes:
            return
        self.app.run_write(lambda: self.app.deletion_service.delete_many(name, keys),
                           lambda count: f'{count} record(s) deleted.',
                           lambda _: self.set_checked(False))
