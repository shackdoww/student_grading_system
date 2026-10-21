def context(cursor, class_id):
    cursor.execute("SELECT * FROM grading_policy WHERE class_id=%s", (class_id,))
    policy = cursor.fetchone()
    cursor.execute("SELECT * FROM grade_percentage WHERE class_id=%s", (class_id,))
    weights = cursor.fetchall()
    cursor.execute(
        """SELECT c.* FROM grade_component c JOIN grade_percentage w USING(component_id)
                      WHERE w.class_id=%s""",
        (class_id,),
    )
    return policy, weights, cursor.fetchall()


def save_policy(cursor, policy, weights):
    cursor.execute(
        """INSERT INTO grading_policy(class_id,midterm_period_id,final_period_id,midterm_weight,final_weight)
        VALUES (%s,%s,%s,%s,%s) ON CONFLICT(class_id) DO UPDATE SET
        midterm_period_id=EXCLUDED.midterm_period_id,final_period_id=EXCLUDED.final_period_id,
        midterm_weight=EXCLUDED.midterm_weight,final_weight=EXCLUDED.final_weight""",
        tuple(
            policy[k]
            for k in (
                "class_id",
                "midterm_period_id",
                "final_period_id",
                "midterm_weight",
                "final_weight",
            )
        ),
    )
    ids = [r["component_id"] for r in weights]
    cursor.execute(
        "DELETE FROM grade_percentage WHERE class_id=%s AND NOT (component_id=ANY(%s))",
        (policy["class_id"], ids),
    )
    for row in weights:
        cursor.execute(
            """INSERT INTO grade_percentage(class_id,component_id,percentage) VALUES (%s,%s,%s)
            ON CONFLICT(class_id,component_id) DO UPDATE SET percentage=EXCLUDED.percentage""",
            (policy["class_id"], row["component_id"], row["percentage"]),
        )


def save_result(cursor, enrollment_id, result):
    cursor.execute(
        """INSERT INTO grade(enrollment_id,midterm_grade,finals_grade,overall_grade,midterm_equiv,finals_equiv,final_equiv,remarks)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(enrollment_id) DO UPDATE SET
        midterm_grade=EXCLUDED.midterm_grade,finals_grade=EXCLUDED.finals_grade,
        overall_grade=EXCLUDED.overall_grade,midterm_equiv=EXCLUDED.midterm_equiv,
        finals_equiv=EXCLUDED.finals_equiv,final_equiv=EXCLUDED.final_equiv,
        remarks=EXCLUDED.remarks,date_encoded=CURRENT_DATE""",
        (
            enrollment_id,
            *(
                result.get(k)
                for k in (
                    "midterm",
                    "final",
                    "overall",
                    "midterm_equiv",
                    "finals_equiv",
                    "final_equiv",
                    "remarks",
                )
            ),
        ),
    )
