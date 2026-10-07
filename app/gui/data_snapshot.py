"""Indexed, read-only presentation data; writes still use the existing services."""

from collections import defaultdict

from psycopg.rows import dict_row

from app.calculator.grade_calculator import GradeCalculator
from app.database.connection import get_connection


TABLES = ('students', 'teachers', 'subjects', 'grading_periods', 'class_offerings',
          'enrollments', 'grade_percentages', 'grade_components', 'grade_component_scores', 'grades',
          'grading_policies', 'period_category_weights', 'period_grade_results')


def load_snapshot():
    # All pages see the same committed state, obtained with one connection.
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            cursor.execute("SET LOCAL statement_timeout = '15s'")
            records = {}
            for table in TABLES:
                cursor.execute(f'SELECT * FROM {table}')  # Fixed internal allowlist.
                records[table] = cursor.fetchall()
    return DataSnapshot(records)


def values(row, fields):
    return tuple(row[field] for field in fields.split())


class DataSnapshot:
    def period_result_status(self, enrollment_id, result):
        saved = next((r for r in self._records['period_grade_results'] if r['enrollment_id'] == enrollment_id), None)
        if not saved:
            return 'Current calculation · not saved'
        if all(float(saved[key + '_grade']) == result[key] for key in ['midterm', 'final', 'overall']):
            return 'Saved results match current calculation'
        return 'Saved results outdated · save period grades again'

    def period_result(self, enrollment_id):
        from app.calculator.period_calculator import PeriodCalculator
        records = self._records
        enrollment = next(r for r in records['enrollments'] if r['enrollment_id'] == enrollment_id)
        oid = enrollment['offering_id']
        policy = next((r for r in records['grading_policies'] if r['offering_id'] == oid), None)
        weights = [r for r in records['period_category_weights'] if r['offering_id'] == oid]
        ids = {r['percentage_id'] for r in records['grade_percentages'] if r['offering_id'] == oid}
        components = [r for r in records['grade_components'] if r['percentage_id'] in ids]
        scores = [r for r in records['grade_component_scores'] if r['enrollment_id'] == enrollment_id]
        return PeriodCalculator().calculate(policy, weights, components, scores)

    def records(self):
        """Detached values for editors; callers cannot mutate the cached snapshot."""
        return {name: [dict(row) for row in rows] for name, rows in self._records.items()}

    def __init__(self, records=None):
        records = records or {name: [] for name in TABLES}
        self._records = records
        self._students = sorted([values(r, 'student_id first_name last_name email program status')
                                 for r in records['students']], key=lambda r: (r[2], r[1]))
        self._student = {r[0]: r for r in self._students}
        self._teachers = sorted([values(r, 'teacher_id first_name last_name email department status')
                                 for r in records['teachers']], key=lambda r: (r[2], r[1]))
        teachers = {r['teacher_id']: r for r in records['teachers']}
        subjects = {r['subject_id']: r for r in records['subjects']}
        periods = {r['period_id']: r for r in records['grading_periods']}
        self._subjects = sorted([values(r, 'subject_id subject_code subject_name description units')
                                 for r in subjects.values()], key=lambda r: r[1])
        self._periods = sorted([values(r, 'period_id name start_date end_date school_year semester')
                                for r in periods.values()], key=lambda r: r[2])
        self._offerings = []
        offerings = {r['offering_id']: r for r in records['class_offerings']}
        for r in offerings.values():
            teacher, subject = teachers[r['teacher_id']], subjects[r['subject_id']]
            self._offerings.append(values(r, 'offering_id class_code schedule section school_year semester room teacher_id')
                                   + values(teacher, 'first_name last_name')
                                   + values(subject, 'subject_id subject_code subject_name'))
        self._offerings.sort(key=lambda r: (r[4], r[5], r[11], r[3]))
        self._enrollments_by_student = defaultdict(list)
        self._enrollments_by_offering = defaultdict(list)
        for r in records['enrollments']:
            offering = offerings[r['offering_id']]
            subject = subjects[offering['subject_id']]
            teacher = teachers[offering['teacher_id']]
            student = self._student[r['student_id']]
            self._enrollments_by_student[r['student_id']].append(
                values(r, 'enrollment_id enroll_date status')
                + values(offering, 'offering_id class_code schedule section school_year semester room')
                + values(subject, 'subject_id subject_code subject_name')
                + values(teacher, 'teacher_id first_name last_name'))
            self._enrollments_by_offering[r['offering_id']].append(
                (r['enrollment_id'], student[0], student[1], student[2], student[4], r['status']))
        for rows in self._enrollments_by_student.values():
            rows.sort(key=lambda r: r[11])
        for rows in self._enrollments_by_offering.values():
            rows.sort(key=lambda r: (r[3], r[2]))
        percentages = {r['percentage_id']: r for r in records['grade_percentages']}
        components = {r['component_id']: r for r in records['grade_components']}
        self._components_by_offering = defaultdict(list)
        for r in sorted(components.values(), key=lambda r: (periods[r['period_id']]['start_date'], r['component_id'])):
            percentage = percentages[r['percentage_id']]
            self._components_by_offering[percentage['offering_id']].append(
                values(r, 'component_id name type max_score description period_id')
                + (periods[r['period_id']]['name'], r['percentage_id'], percentage['percentage']))
        self._scores = defaultdict(list)
        for r in records['grade_component_scores']:
            component = components[r['component_id']]
            percentage = percentages[component['percentage_id']]
            period = periods[component['period_id']]
            self._scores[r['enrollment_id']].append(
                values(r, 'score_id score remarks date_recorded')
                + values(component, 'component_id name type max_score description')
                + values(percentage, 'percentage_id percentage offering_id')
                + values(period, 'name start_date end_date'))
        for rows in self._scores.values():
            rows.sort(key=lambda r: (r[13], r[4]))
        self._grades = {r['enrollment_id']: values(r, 'grade_id final_grade remarks date_encoded enrollment_id')
                        for r in records['grades']}
        self.enrollment_count = len(records['enrollments'])

    def students(self):
        return self._students

    def student(self, sid):
        return self._student.get(sid)

    def teachers(self):
        return self._teachers

    def subjects(self):
        return self._subjects

    def periods(self):
        return self._periods

    def offerings(self):
        return self._offerings

    def enrollments_for_student(self, sid):
        return self._enrollments_by_student.get(sid, [])

    def enrollments_for_offering(self, oid):
        return self._enrollments_by_offering.get(oid, [])

    def components_for_offering(self, oid):
        return self._components_by_offering.get(oid, [])

    def saved_grade(self, eid):
        return self._grades.get(eid)

    def calculate_grade(self, eid):
        return GradeCalculator().calculate(self._scores.get(eid, []))
