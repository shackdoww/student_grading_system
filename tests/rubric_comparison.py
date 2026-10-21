"""Compare persisted appendix records using natural keys, not surrogate numbers."""

import json
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
from psycopg.rows import dict_row

QUERIES = {
    "student": "SELECT * FROM student",
    "teacher": "SELECT * FROM teacher",
    "subject": "SELECT * FROM subject",
    "class": "SELECT c.*,s.subject_code FROM class c JOIN subject s USING(subject_id)",
    "enrollment": "SELECT e.*,c.class_code FROM enrollment e JOIN class c USING(class_id)",
    "grading_period": "SELECT * FROM grading_period",
    "grade_component": "SELECT c.*,p.name AS period_name FROM grade_component c JOIN grading_period p USING(period_id)",
    "grade_percentage": "SELECT w.*,c.class_code,g.name AS component_name FROM grade_percentage w JOIN class c USING(class_id) JOIN grade_component g USING(component_id)",
    "grade_component_score": "SELECT s.*,e.student_id,c.class_code,g.name AS component_name FROM grade_component_score s JOIN enrollment e USING(enrollment_id) JOIN class c USING(class_id) JOIN grade_component g USING(component_id)",
    "grade": "SELECT g.*,e.student_id,c.class_code FROM grade g JOIN enrollment e USING(enrollment_id) JOIN class c USING(class_id)",
}


def compare(connection):
    expected = json.loads(
        (Path(__file__).parent / "fixtures/rubric_expected.json").read_text()
    )
    test_date = connection.execute("SELECT CURRENT_DATE").fetchone()[0].isoformat()
    result = {}

    def clean(value):
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value

    with connection.cursor(row_factory=dict_row) as cur:
        for table, spec in expected.items():
            cur.execute(QUERIES[table])
            rows = cur.fetchall()
            actual = {tuple(r[k] for k in spec["key"]): r for r in rows}
            differences = []
            for row in spec["rows"]:
                key = tuple(row[k] for k in spec["key"])
                saved = actual.get(key)
                if saved is None:
                    differences.append({"key": key, "missing": True})
                    continue
                for field, value in row.items():
                    value = test_date if value == "$test_date" else value
                    if clean(saved.get(field)) != value:
                        differences.append(
                            {
                                "key": key,
                                "field": field,
                                "expected": value,
                                "actual": clean(saved.get(field)),
                            }
                        )
            if len(rows) != len(spec["rows"]):
                differences.append(
                    {"row_count": len(rows), "expected": len(spec["rows"])}
                )
            result[table] = {
                "expected_count": len(spec["rows"]),
                "actual_count": len(rows),
                "differences": differences,
            }
        cur.execute("SELECT count(*) AS count FROM audit_log")
        count = cur.fetchone()["count"]
        result["audit_log"] = {
            "minimum_count": 7,
            "actual_count": count,
            "differences": [] if count >= 7 else ["Fewer than seven audit entries"],
        }
    return result
