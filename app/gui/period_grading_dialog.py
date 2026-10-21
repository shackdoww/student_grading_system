from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QDoubleSpinBox,
    QDialogButtonBox,
    QLabel,
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
)


class PeriodPolicyDialog(QDialog):
    def __init__(self, parent, class_id, records):
        super().__init__(parent)
        self.setWindowTitle("Configure class grading")
        self.setMinimumWidth(560)
        self.oid = class_id
        self.records = records
        policy = next(
            (r for r in records["grading_policy"] if r["class_id"] == class_id), {}
        )
        offering = next(r for r in records["class"] if r["class_id"] == class_id)
        root = QVBoxLayout(self)
        self.form = QFormLayout()
        root.addLayout(self.form)
        self.periods = {}
        self.overall = {}
        for key, label in [("midterm", "Midterm"), ("final", "Final")]:
            combo = QComboBox()
            for p in sorted(records["grading_period"], key=lambda r: r["period_order"]):
                if (p["school_year"], p["semester"]) == (
                    offering["school_year"],
                    offering["semester"],
                ):
                    combo.addItem(p["name"], p["period_id"])
            index = combo.findData(policy.get(key + "_period_id"))
            combo.setCurrentIndex(
                index
                if index >= 0
                else (0 if key == "midterm" else min(1, combo.count() - 1))
            )
            self.periods[key] = combo
            self.form.addRow(label + " period", combo)
            weight = QDoubleSpinBox()
            weight.setRange(0, 100)
            weight.setSuffix("%")
            weight.setValue(
                float(policy.get(key + "_weight", 40 if key == "midterm" else 60))
            )
            self.overall[key] = weight
            self.form.addRow(label + " overall weight", weight)
        self.categories = QFormLayout()
        root.addLayout(self.categories)
        root.addWidget(
            QLabel("Select shared components; weights must total 100% for each period.")
        )
        self.source = QLineEdit()
        self.source.setPlaceholderText("Optional source / reference")
        self.form.addRow("Source / reference", self.source)
        self.inputs = []
        for combo in self.periods.values():
            combo.currentIndexChanged.connect(self.rebuild)
        self.rebuild()
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def rebuild(self):
        previous = {
            cid: (check.isChecked(), spin.value()) for cid, check, spin in self.inputs
        }
        while self.categories.rowCount():
            self.categories.removeRow(0)
        self.inputs = []
        source = {
            r["component_id"]: r
            for r in self.records["grade_percentage"]
            if r["class_id"] == self.oid
        }
        for key, combo in self.periods.items():
            for component in sorted(
                self.records["grade_component"], key=lambda r: r["component_id"]
            ):
                if component["period_id"] != combo.currentData():
                    continue
                cid = component["component_id"]
                saved = source.get(cid)
                check = QCheckBox(component["name"])
                check.setChecked(previous.get(cid, (bool(saved), 0))[0])
                spin = QDoubleSpinBox()
                spin.setRange(0, 100)
                spin.setSuffix("%")
                spin.setValue(
                    previous.get(
                        cid, (False, float(saved["percentage"]) if saved else 0)
                    )[1]
                )
                row = QHBoxLayout()
                row.addWidget(check)
                row.addWidget(spin)
                self.categories.addRow(key.title(), row)
                self.inputs.append((cid, check, spin))

    def values(self):
        policy = {"class_id": self.oid}
        for key in self.periods:
            policy[key + "_period_id"] = self.periods[key].currentData()
            policy[key + "_weight"] = self.overall[key].value()
        return policy, [
            {"component_id": cid, "percentage": spin.value()}
            for cid, check, spin in self.inputs
            if check.isChecked()
        ]
