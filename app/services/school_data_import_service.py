import csv
import os
from datetime import date
from decimal import Decimal, InvalidOperation

from app.database.connection import get_connection


DATASETS = [
    ("students", "school_students.csv", ["student_id", "first_name", "last_name", "email", "program", "status"]),
    ("teachers", "school_teachers.csv", ["teacher_id", "first_name", "last_name", "email", "department", "status"]),
    ("subjects", "school_subjects.csv", ["subject_id", "subject_code", "subject_name", "description", "units"]),
    ("grading_periods", "school_grading_periods.csv", ["period_id", "name", "start_date", "end_date", "school_year", "semester"]),
    ("class_offerings", "school_class_offerings.csv", ["offering_id", "class_code", "schedule", "section", "school_year", "semester", "room", "teacher_id", "subject_id"]),
    ("grade_percentages", "school_grade_percentages.csv", ["percentage_id", "percentage", "offering_id"]),
    ("grade_components", "school_grade_components.csv", ["component_id", "name", "type", "max_score", "description", "period_id", "percentage_id"]),
    ("enrollments", "school_enrollments.csv", ["enrollment_id", "enroll_date", "status", "student_id", "offering_id"]),
    ("grade_component_scores", "school_grade_component_scores.csv", ["score_id", "score", "remarks", "date_recorded", "enrollment_id", "component_id"]),
    ("grades", "school_grades.csv", ["grade_id", "final_grade", "remarks", "date_encoded", "enrollment_id"]),
]

UPSERTS = {
    "students": ("student_id", ["first_name", "last_name", "email", "program", "status"]),
    "teachers": ("teacher_id", ["first_name", "last_name", "email", "department", "status"]),
    "subjects": ("subject_id", ["subject_code", "subject_name", "description", "units"]),
    "grading_periods": ("period_id", ["name", "start_date", "end_date", "school_year", "semester"]),
    "class_offerings": ("offering_id", ["class_code", "schedule", "section", "school_year", "semester", "room", "teacher_id", "subject_id"]),
    "grade_percentages": ("percentage_id", ["percentage", "offering_id"]),
    "grade_components": ("component_id", ["name", "type", "max_score", "description", "period_id", "percentage_id"]),
    "enrollments": ("enrollment_id", ["enroll_date", "status", "student_id", "offering_id"]),
    "grade_component_scores": ("score_id", ["score", "remarks", "date_recorded", "enrollment_id", "component_id"]),
    "grades": ("grade_id", ["final_grade", "remarks", "date_encoded", "enrollment_id"]),
}


class SchoolDataImportService:
    def read_folder(self, folder):
        datasets = {}
        errors = []

        for table, filename, required in DATASETS:
            path = os.path.join(folder, filename)
            if not os.path.isfile(path):
                errors.append(f"{filename}: file not found.")
                continue

            try:
                with open(path, "r", encoding="utf-8-sig", newline="") as file:
                    reader = csv.DictReader(file)
                    headers = [h.strip() if h else "" for h in (reader.fieldnames or [])]
                    missing = [h for h in required if h not in headers]
                    if missing:
                        errors.append(f"{filename}: missing column(s): {', '.join(missing)}.")
                        continue

                    rows = []
                    for line, raw in enumerate(reader, start=2):
                        row = {key: (raw.get(key) or "").strip() for key in required}
                        row["_line"] = line
                        rows.append(row)
                    datasets[table] = rows
            except UnicodeDecodeError:
                errors.append(f"{filename}: save the CSV as UTF-8.")
            except csv.Error as error:
                errors.append(f"{filename}: {error}")

        if errors:
            raise ValueError("\n".join(errors))
        return datasets

    def validate(self, datasets):
        errors = []

        def required(table, fields):
            for row in datasets[table]:
                missing = [f for f in fields if not row[f]]
                if missing:
                    errors.append(f"{table} row {row['_line']}: missing {', '.join(missing)}.")

        for table, _, fields in DATASETS:
            required(table, fields)

        self._unique(errors, datasets["students"], "student_id", "students")
        self._unique(errors, datasets["students"], "email", "students")
        self._unique(errors, datasets["teachers"], "teacher_id", "teachers")
        self._unique(errors, datasets["teachers"], "email", "teachers")
        self._unique(errors, datasets["subjects"], "subject_id", "subjects")
        self._unique(errors, datasets["subjects"], "subject_code", "subjects")
        self._unique(errors, datasets["grading_periods"], "period_id", "grading_periods")
        self._unique(errors, datasets["class_offerings"], "offering_id", "class_offerings")
        self._unique(errors, datasets["grade_percentages"], "percentage_id", "grade_percentages")
        self._unique(errors, datasets["grade_components"], "component_id", "grade_components")
        self._unique(errors, datasets["enrollments"], "enrollment_id", "enrollments")
        self._unique(errors, datasets["grade_component_scores"], "score_id", "grade_component_scores")
        self._unique(errors, datasets["grades"], "grade_id", "grades")

        self._numbers(errors, datasets)
        self._dates(errors, datasets)
        self._foreign_keys(errors, datasets)

        percentage_by_offering = {}
        for row in datasets["grade_percentages"]:
            try:
                percentage_by_offering.setdefault(row["offering_id"], Decimal(row["percentage"]))
            except InvalidOperation:
                continue
        for offering_id in list(percentage_by_offering):
            percentage_by_offering[offering_id] = sum(
                Decimal(r["percentage"]) for r in datasets["grade_percentages"]
                if r["offering_id"] == offering_id
                and self._is_decimal(r["percentage"])
            )
        for offering_id, total in percentage_by_offering.items():
            if total > Decimal("100"):
                errors.append(f"grade_percentages: offering {offering_id} totals {total}%, above 100%.")

        pct_ids = {r["percentage_id"] for r in datasets["grade_percentages"]}
        period_ids = {r["period_id"] for r in datasets["grading_periods"]}
        component_limits = {}
        for row in datasets["grade_components"]:
            if self._is_decimal(row["max_score"]):
                component_limits[row["component_id"]] = Decimal(row["max_score"])
            if row["percentage_id"] not in pct_ids:
                errors.append(f"grade_components row {row['_line']}: unknown percentage_id '{row['percentage_id']}'.")
            if row["period_id"] not in period_ids:
                errors.append(f"grade_components row {row['_line']}: unknown period_id '{row['period_id']}'.")

        for row in datasets["grade_component_scores"]:
            if self._is_decimal(row["score"]) and row["component_id"] in component_limits:
                score = Decimal(row["score"])
                if score < 0 or score > component_limits[row["component_id"]]:
                    errors.append(
                        f"grade_component_scores row {row['_line']}: score {score} exceeds "
                        f"component {row['component_id']} maximum {component_limits[row['component_id']]}."
                    )

        self._unique_pair(errors, datasets["enrollments"], "student_id", "offering_id", "enrollments")
        self._unique_pair(errors, datasets["grade_component_scores"], "enrollment_id", "component_id", "grade_component_scores")
        self._unique(errors, datasets["grades"], "enrollment_id", "grades")

        if errors:
            return errors

        # Check database-level unique conflicts that an upsert cannot safely resolve.
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                for table, field in [("students", "email"), ("teachers", "email"), ("subjects", "subject_code")]:
                    values = [r[field] for r in datasets[table]]
                    if not values:
                        continue
                    cursor.execute(f"SELECT {field}, {self._pk(table)} FROM {table} WHERE {field} = ANY(%s)", (values,))
                    existing = cursor.fetchall()
                    incoming_pk = {r[self._pk_index(table)]: r for r in datasets[table]}
                    for unique_value, existing_pk in existing:
                        row = next((r for r in datasets[table] if r[field] == unique_value), None)
                        if row and row[self._pk(table)] != existing_pk:
                            errors.append(
                                f"{table}: {field} '{unique_value}' already belongs to '{existing_pk}', "
                                f"but the CSV uses '{row[self._pk(table)]}'."
                            )
        finally:
            connection.close()

        return errors

    @staticmethod
    def _pk(table):
        return next(pk for t, _, _ in DATASETS if t == table for pk in [UPSERTS[t][0]])

    @staticmethod
    def _pk_index(table):
        return 0

    @staticmethod
    def _unique(errors, rows, field, table):
        seen = set()
        for row in rows:
            value = row[field]
            if value in seen:
                errors.append(f"{table} row {row['_line']}: duplicate {field} '{value}'.")
            seen.add(value)

    @staticmethod
    def _unique_pair(errors, rows, first, second, table):
        seen = set()
        for row in rows:
            pair = (row[first], row[second])
            if pair in seen:
                errors.append(f"{table} row {row['_line']}: duplicate ({first}, {second}) pair.")
            seen.add(pair)

    @staticmethod
    def _is_decimal(value):
        try:
            Decimal(value)
            return True
        except (InvalidOperation, ValueError):
            return False

    def _numbers(self, errors, datasets):
        for row in datasets["subjects"]:
            try:
                if int(row["units"]) <= 0:
                    errors.append(f"subjects row {row['_line']}: units must be greater than 0.")
            except ValueError:
                errors.append(f"subjects row {row['_line']}: units must be an integer.")
        for row in datasets["grade_percentages"]:
            try:
                value = Decimal(row["percentage"])
                if value <= 0 or value > 100:
                    errors.append(f"grade_percentages row {row['_line']}: percentage must be > 0 and <= 100.")
            except InvalidOperation:
                errors.append(f"grade_percentages row {row['_line']}: invalid percentage.")
        for row in datasets["grade_components"]:
            try:
                if Decimal(row["max_score"]) <= 0:
                    errors.append(f"grade_components row {row['_line']}: max_score must be > 0.")
            except InvalidOperation:
                errors.append(f"grade_components row {row['_line']}: invalid max_score.")
        for row in datasets["grade_component_scores"]:
            if not self._is_decimal(row["score"]) or Decimal(row["score"]) < 0:
                errors.append(f"grade_component_scores row {row['_line']}: score must be numeric and >= 0.")
        for row in datasets["grades"]:
            try:
                value = Decimal(row["final_grade"])
                if value < 0 or value > 100:
                    errors.append(f"grades row {row['_line']}: final_grade must be between 0 and 100.")
            except InvalidOperation:
                errors.append(f"grades row {row['_line']}: invalid final_grade.")

    def _dates(self, errors, datasets):
        for table, field in [
            ("grading_periods", "start_date"), ("grading_periods", "end_date"),
            ("enrollments", "enroll_date"), ("grade_component_scores", "date_recorded"),
            ("grades", "date_encoded")
        ]:
            for row in datasets[table]:
                try:
                    date.fromisoformat(row[field])
                except ValueError:
                    errors.append(f"{table} row {row['_line']}: invalid {field}.")

        for row in datasets["grading_periods"]:
            if self._valid_date(row["start_date"]) and self._valid_date(row["end_date"]) and row["end_date"] < row["start_date"]:
                errors.append(f"grading_periods row {row['_line']}: end_date is before start_date.")

    @staticmethod
    def _valid_date(value):
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False

    def _foreign_keys(self, errors, d):
        checks = [
            ("class_offerings", "teacher_id", "teachers", "teacher_id"),
            ("class_offerings", "subject_id", "subjects", "subject_id"),
            ("grade_percentages", "offering_id", "class_offerings", "offering_id"),
            ("grade_components", "period_id", "grading_periods", "period_id"),
            ("grade_components", "percentage_id", "grade_percentages", "percentage_id"),
            ("enrollments", "student_id", "students", "student_id"),
            ("enrollments", "offering_id", "class_offerings", "offering_id"),
            ("grade_component_scores", "enrollment_id", "enrollments", "enrollment_id"),
            ("grade_component_scores", "component_id", "grade_components", "component_id"),
            ("grades", "enrollment_id", "enrollments", "enrollment_id"),
        ]
        for table, field, parent, parent_field in checks:
            parent_values = {r[parent_field] for r in d[parent]}
            for row in d[table]:
                if row[field] not in parent_values:
                    errors.append(f"{table} row {row['_line']}: unknown {field} '{row[field]}'.")

    def import_all(self, datasets):
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                for table, _, fields in DATASETS:
                    pk, updates = UPSERTS[table]
                    columns = fields
                    placeholders = ", ".join(["%s"] * len(columns))
                    assignments = ", ".join(f"{field} = EXCLUDED.{field}" for field in updates)
                    sql = (
                        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
                        f"ON CONFLICT ({pk}) DO UPDATE SET {assignments}"
                    )
                    for row in datasets[table]:
                        values = [row[field] for field in columns]
                        cursor.execute(sql, values)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
