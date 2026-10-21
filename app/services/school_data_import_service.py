"""Canonical CSV import with atomic validation and explicit legacy conversion."""

import csv
import json
from pathlib import Path
from datetime import date, time
from decimal import Decimal
from psycopg import sql
from psycopg.types.json import Jsonb
from app.database.connection import get_connection
from app.database.provenance import source_reference
from app.database.migration_preflight import component_weights
from app.calculator.period_calculator import number

# Optional fields may be absent. Relationships, required text and totals are also
# checked by the same PostgreSQL constraints as normal application writes.
DATASETS = [
    (
        "student",
        "school_students.csv",
        "student_id first_name last_name email program status year_level",
    ),
    (
        "teacher",
        "school_teachers.csv",
        "teacher_id first_name last_name email department status",
    ),
    (
        "subject",
        "school_subjects.csv",
        "subject_id subject_code subject_name description units",
    ),
    (
        "grading_period",
        "school_grading_periods.csv",
        "period_id name start_date end_date school_year semester period_order",
    ),
    (
        "class",
        "school_class_offerings.csv",
        "class_id class_code subject_id teacher_id section school_year semester schedule room",
    ),
    (
        "class_meeting",
        "school_class_meetings.csv",
        "meeting_id class_id weekday start_time end_time",
    ),
    (
        "grade_component",
        "school_grade_components.csv",
        "component_id period_id name type max_score description",
    ),
    (
        "grade_percentage",
        "school_grade_percentages.csv",
        "percentage_id class_id component_id percentage",
    ),
    (
        "grading_policy",
        "school_grading_policies.csv",
        "class_id midterm_period_id final_period_id midterm_weight final_weight",
    ),
    (
        "enrollment",
        "school_enrollments.csv",
        "enrollment_id student_id class_id enroll_date status",
    ),
    (
        "grade_component_score",
        "school_grade_component_scores.csv",
        "score_id enrollment_id component_id score remarks date_recorded",
    ),
    (
        "grade",
        "school_grades.csv",
        "grade_id enrollment_id midterm_grade finals_grade overall_grade midterm_equiv finals_equiv final_equiv remarks date_encoded",
    ),
]
DATASETS = [(t, f, fields.split()) for t, f, fields in DATASETS]
NUMBERS = {
    "max_score",
    "score",
    "percentage",
    "midterm_weight",
    "final_weight",
    "midterm_grade",
    "finals_grade",
    "overall_grade",
    "midterm_equiv",
    "finals_equiv",
    "final_equiv",
}
INTEGERS = {"units", "year_level", "period_order", "weekday"}
NULLABLE = {
    "email",
    "description",
    "room",
    "remarks",
    "year_level",
    "midterm_grade",
    "finals_grade",
    "overall_grade",
    "midterm_equiv",
    "finals_equiv",
    "final_equiv",
}
PK = {t: fields[0] for t, _, fields in DATASETS}
PK["class_meeting"] = "meeting_id"


class SchoolDataImportService:
    def read_folder(self, folder):
        folder = Path(folder)
        datasets = {}
        for table, filename, fields in DATASETS:
            path = folder / filename
            if not path.is_file():
                if table in ("class_meeting", "grading_policy"):
                    datasets[table] = []
                    continue
                raise ValueError(f"{filename}: file not found.")
            with path.open(encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                if not reader.fieldnames:
                    raise ValueError(f"{filename}: header is required.")
                datasets[table] = [
                    dict({k: (v or "").strip() for k, v in row.items() if k}, _line=i)
                    for i, row in enumerate(reader, 2)
                ]
        if any("percentage_id" in r for r in datasets["grade_component"]):
            return self._legacy(datasets)
        return datasets

    def _legacy(self, datasets):
        original = json.loads(json.dumps(datasets))
        categories = [
            dict(r, offering_id=r.get("offering_id", r.get("class_id")))
            for r in datasets["grade_percentage"]
        ]
        weights, blockers = component_weights(
            {
                "grade_components": datasets["grade_component"],
                "grade_percentages": categories,
            }
        )
        if blockers:
            raise ValueError(" ".join(blockers))
        for table in ("class", "enrollment"):
            for row in datasets[table]:
                row["class_id"] = row.pop("offering_id", row.get("class_id"))
        for row in datasets["grade_component"]:
            row.pop("percentage_id", None)
        datasets["grade_percentage"] = weights
        for i, row in enumerate(datasets["grading_period"], 1):
            row["period_order"] = i
        datasets["grade"] = []
        datasets["_legacy_evidence"] = original
        return datasets

    def _clean(self, table, row, fields):
        clean = {}
        for field in fields:
            if field not in row:
                continue
            value = row[field]
            if value is None or value == "":
                if field in NULLABLE:
                    clean[field] = None
                    continue
                raise ValueError(f"{table}: {field} is required when supplied.")
            if field in NUMBERS:
                value = number(value)
            elif field in INTEGERS:
                try:
                    value = int(value)
                except (ValueError, TypeError) as error:
                    raise ValueError(f"{field} must be an integer.") from error
            elif field.endswith("_date") or field in ("date_recorded", "date_encoded"):
                if not isinstance(value, date):
                    value = date.fromisoformat(str(value))
            elif field.endswith("_time"):
                if not isinstance(value, time):
                    value = time.fromisoformat(str(value))
            clean[field] = value
        return clean

    def _execute(self, c, datasets):
        base_source = source_reference()
        from app.services.scheduling import normalize_meetings, format_schedule

        meeting_groups = {}
        for meeting in datasets.get("class_meeting", []):
            meeting_groups.setdefault(meeting.get("class_id"), []).append(meeting)
        normalized = {
            cid: normalize_meetings(rows) for cid, rows in meeting_groups.items()
        }
        class_rows = []
        for row in datasets.get("class", []):
            selected = normalized.get(row.get("class_id"))
            if not selected:
                selected = [
                    dict(weekday=d, start_time=a, end_time=b)
                    for d, a, b in c.execute(
                        "SELECT weekday,start_time,end_time FROM class_meeting WHERE class_id=%s",
                        (row.get("class_id"),),
                    )
                ]
            if selected:
                row = dict(row, schedule=format_schedule(selected))
            elif not datasets.get("_legacy_evidence"):
                raise ValueError(
                    f"Class {row.get('class_id')}: explicit weekdays and start/end times are required; review its schedule."
                )
            class_rows.append(row)
        datasets = dict(datasets, **{"class": class_rows})
        for table, _, fields in DATASETS:
            if table == "class_meeting":
                # A provided class's meeting rows are its complete replacement set.
                # Validation rolls these changes back; actual imports commit atomically.
                for cid in normalized:
                    c.execute("DELETE FROM class_meeting WHERE class_id=%s", (cid,))
            for row in datasets.get(table, []):
                clean = self._clean(table, row, fields)
                if not clean:
                    raise ValueError(f"{table}: empty row.")
                c.execute(
                    "SELECT set_config('app.source',%s,true)",
                    (row.get("source_reference") or row.get("set_by") or base_source,),
                )
                columns = list(clean)
                pk = PK[table]
                updates = [k for k in columns if k != pk]
                conflict = (
                    sql.SQL(" DO NOTHING")
                    if not updates
                    else sql.SQL(" DO UPDATE SET ")
                    + sql.SQL(",").join(
                        sql.SQL("{}=EXCLUDED.{}").format(
                            sql.Identifier(k), sql.Identifier(k)
                        )
                        for k in updates
                    )
                )
                c.execute(
                    sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({})").format(
                        sql.Identifier(table),
                        sql.SQL(",").join(map(sql.Identifier, columns)),
                        sql.SQL(",").join(sql.Placeholder() for _ in columns),
                        sql.Identifier(pk),
                    )
                    + conflict,
                    list(clean.values()),
                )
        # Also cover meeting-only imports: display and conflict data must agree.
        c.execute("SELECT set_config('app.source',%s,true)", (base_source,))
        for cid, meetings in normalized.items():
            c.execute(
                "UPDATE class SET schedule=%s WHERE class_id=%s",
                (format_schedule(meetings), cid),
            )
        c.execute("SET CONSTRAINTS ALL IMMEDIATE")
        if datasets.get("_legacy_evidence"):
            c.execute(
                "INSERT INTO import_archive(payload,imported_by) VALUES (%s,%s)",
                (
                    Jsonb(datasets["_legacy_evidence"]),
                    c.execute("SELECT current_setting('app.actor',true)").fetchone()[0],
                ),
            )

    def validate(self, datasets):
        try:
            for table, _, fields in DATASETS:
                seen = set()
                for row in datasets.get(table, []):
                    clean = self._clean(table, row, fields)
                    key = clean.get(PK[table])
                    if key is not None:
                        key = str(key)
                        if key in seen:
                            raise ValueError(
                                f"{table}: duplicate {PK[table]} {key!r} in CSV input."
                            )
                        seen.add(key)
            with get_connection() as c:
                with c.transaction(force_rollback=True):
                    self._execute(c, datasets)
        except Exception as error:
            # psycopg errors carry database messages; expose no credentials.
            return [str(error).split("\nCONTEXT:")[0]]
        return []

    def import_all(self, datasets):
        errors = self.validate(datasets)
        if errors:
            raise ValueError("\n".join(errors))
        with get_connection() as c:
            self._execute(c, datasets)
        return sum(len(datasets.get(t, [])) for t, _, _ in DATASETS)
