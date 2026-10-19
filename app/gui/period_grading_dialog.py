from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox,
                              QDoubleSpinBox, QDialogButtonBox, QLabel)


class PeriodPolicyDialog(QDialog):
    def __init__(self, parent, offering_id, records):
        super().__init__(parent)
        self.setWindowTitle('Configure period grading')
        self.setMinimumWidth(520)
        self.oid = offering_id
        self.records = records
        policy = next((r for r in records['grading_policies'] if r['offering_id'] == offering_id), {})
        offering = next(r for r in records['class_offerings'] if r['offering_id'] == offering_id)
        root = QVBoxLayout(self)
        self.form = QFormLayout()
        root.addLayout(self.form)
        self.periods, self.overall = {}, {}
        for key, label in [('midterm', 'Midterm'), ('final', 'Final')]:
            combo = QComboBox()
            for period in records['grading_periods']:
                if period['school_year'] == offering['school_year'] and period['semester'] == offering['semester']:
                    combo.addItem(period['name'], period['period_id'])
            combo.setCurrentIndex(combo.findData(policy.get(key + '_period_id')))
            self.periods[key] = combo
            self.form.addRow(label + ' period', combo)
            weight = QDoubleSpinBox()
            weight.setRange(0.01, 99.99)
            weight.setSuffix('%')
            weight.setValue(float(policy.get(key + '_weight', 40 if key=='midterm' else 60)))
            self.overall[key] = weight
            self.form.addRow(label + ' overall weight', weight)
        self.categories = QFormLayout()
        root.addLayout(self.categories)
        root.addWidget(QLabel('Each period’s category weights and the overall weights must total 100%.'))
        self.inputs = []
        for combo in self.periods.values():
            combo.currentIndexChanged.connect(self.rebuild)
        self.rebuild()
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def rebuild(self):
        while self.categories.rowCount():
            self.categories.removeRow(0)
        self.inputs = []
        source = {r['percentage_id']: r for r in self.records['grade_percentages'] if r['offering_id'] == self.oid}
        for key, combo in self.periods.items():
            pid = combo.currentData()
            groups = {}
            for c in self.records['grade_components']:
                if c['period_id'] == pid and c['percentage_id'] in source:
                    groups.setdefault(c['percentage_id'], []).append(c['name'])
            for cid, names in groups.items():
                saved = next((r['weight'] for r in self.records['period_category_weights'] if
                              r['offering_id'] == self.oid and r['period_id'] == pid and r['percentage_id'] == cid), source[cid]['percentage'])
                spin = QDoubleSpinBox()
                spin.setRange(0.01, 100)
                spin.setSuffix('%')
                spin.setValue(float(saved))
                self.categories.addRow(f'{key.title()} · {cid} ({", ".join(names)})', spin)
                self.inputs.append((pid, cid, spin))

    def values(self):
        policy = {'offering_id': self.oid}
        for key in self.periods:
            policy[key + '_period_id'] = self.periods[key].currentData()
            policy[key + '_weight'] = self.overall[key].value()
        weights = [{'period_id': pid, 'percentage_id': cid, 'weight': spin.value()} for pid, cid, spin in self.inputs]
        return policy, weights
