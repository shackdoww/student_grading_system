def context(cursor, offering_id):
    cursor.execute('SELECT * FROM grading_policies WHERE offering_id = %s', (offering_id,))
    policy = cursor.fetchone()
    cursor.execute('SELECT * FROM period_category_weights WHERE offering_id = %s', (offering_id,))
    weights = cursor.fetchall()
    cursor.execute('''SELECT c.* FROM grade_components c JOIN grade_percentages p
                      ON c.percentage_id = p.percentage_id WHERE p.offering_id = %s''', (offering_id,))
    return policy, weights, cursor.fetchall()


def save_policy(cursor, policy, weights):
    cursor.execute('''INSERT INTO grading_policies VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT(offering_id) DO UPDATE SET midterm_period_id=EXCLUDED.midterm_period_id,
        final_period_id=EXCLUDED.final_period_id, midterm_weight=EXCLUDED.midterm_weight,
        final_weight=EXCLUDED.final_weight''', tuple(policy[k] for k in
        ['offering_id', 'midterm_period_id', 'final_period_id', 'midterm_weight', 'final_weight']))
    cursor.execute('DELETE FROM period_category_weights WHERE offering_id=%s', (policy['offering_id'],))
    for row in weights:
        cursor.execute('INSERT INTO period_category_weights VALUES (%s,%s,%s,%s)',
                       (policy['offering_id'], row['period_id'], row['percentage_id'], row['weight']))


def save_result(cursor, enrollment_id, result):
    cursor.execute('''INSERT INTO period_grade_results
        (enrollment_id,midterm_grade,final_grade,overall_grade,midterm_equiv,finals_equiv,final_equiv,remarks)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT(enrollment_id) DO UPDATE SET midterm_grade=EXCLUDED.midterm_grade,
        final_grade=EXCLUDED.final_grade,overall_grade=EXCLUDED.overall_grade,
        midterm_equiv=EXCLUDED.midterm_equiv,finals_equiv=EXCLUDED.finals_equiv,
        final_equiv=EXCLUDED.final_equiv,remarks=EXCLUDED.remarks,
        calculated_at=CURRENT_TIMESTAMP''', (enrollment_id, result['midterm'], result['final'], result['overall'],
        result['midterm_equiv'],result['finals_equiv'],result['final_equiv'],result['remarks']))
