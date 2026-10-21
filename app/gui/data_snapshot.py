"""Indexed, read-only presentation data; writes still use the existing services."""

from collections import defaultdict

from psycopg.rows import dict_row

from app.database.connection import get_connection


TABLES = ('student','teacher','subject','grading_period','class','enrollment',
          'grade_component','grade_percentage','grade_component_score','grade','grading_policy','audit_log','class_meeting')

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
    def period_result(self, enrollment_id, include_equivalents=False):
        from app.calculator.period_calculator import PeriodCalculator
        records=self._records
        enrollment=next(r for r in records['enrollment'] if r['enrollment_id']==enrollment_id)
        cid=enrollment['class_id']
        policy=next((r for r in records['grading_policy'] if r['class_id']==cid),None)
        weights=[r for r in records['grade_percentage'] if r['class_id']==cid]
        ids={r['component_id'] for r in weights}
        components=[r for r in records['grade_component'] if r['component_id'] in ids]
        scores=[r for r in records['grade_component_score'] if r['enrollment_id']==enrollment_id]
        return PeriodCalculator().calculate(policy,weights,components,scores,include_equivalents=include_equivalents)

    def records(self):
        """Detached values for editors; callers cannot mutate the cached snapshot."""
        return {name: [dict(row) for row in rows] for name, rows in self._records.items()}

    def __init__(self, records=None):
        records = records or {name: [] for name in TABLES}
        self._records = {name: records.get(name, []) for name in TABLES}
        records = self._records
        self._students = sorted([values(r, 'student_id first_name last_name email program status') + (r.get('year_level'),)
                                 for r in records['student']], key=lambda r: (r[2], r[1]))
        self._student = {r[0]: r for r in self._students}
        self._teachers = sorted([values(r, 'teacher_id first_name last_name email department status')
                                 for r in records['teacher']], key=lambda r: (r[2], r[1]))
        teachers = {r['teacher_id']: r for r in records['teacher']}
        subjects = {r['subject_id']: r for r in records['subject']}
        periods = {r['period_id']: r for r in records['grading_period']}
        self._subjects = sorted([values(r, 'subject_id subject_code subject_name description units')
                                 for r in subjects.values()], key=lambda r: r[1])
        self._periods = sorted([values(r, 'period_id name start_date end_date school_year semester') + (r.get('period_order',1),)
                                for r in periods.values()], key=lambda r: (r[6],r[2]))
        self._offerings = []
        offerings = {r['class_id']: r for r in records['class']}
        for r in offerings.values():
            teacher, subject = teachers[r['teacher_id']], subjects[r['subject_id']]
            self._offerings.append(values(r, 'class_id class_code schedule section school_year semester room teacher_id')
                                   + values(teacher, 'first_name last_name')
                                   + values(subject, 'subject_id subject_code subject_name'))
        self._offerings.sort(key=lambda r: (r[4], r[5], r[11], r[3]))
        self._enrollments_by_student = defaultdict(list)
        self._enrollments_by_offering = defaultdict(list)
        for r in records['enrollment']:
            offering = offerings[r['class_id']]
            subject = subjects[offering['subject_id']]
            teacher = teachers[offering['teacher_id']]
            student = self._student[r['student_id']]
            self._enrollments_by_student[r['student_id']].append(
                values(r, 'enrollment_id enroll_date status')
                + values(offering, 'class_id class_code schedule section school_year semester room')
                + values(subject, 'subject_id subject_code subject_name')
                + values(teacher, 'teacher_id first_name last_name'))
            self._enrollments_by_offering[r['class_id']].append(
                (r['enrollment_id'], student[0], student[1], student[2], student[4], r['status']))
        for rows in self._enrollments_by_student.values():
            rows.sort(key=lambda r: r[11])
        for rows in self._enrollments_by_offering.values():
            rows.sort(key=lambda r: (r[3], r[2]))
        components={r['component_id']:r for r in records['grade_component']}
        percentages={(r['class_id'],r['component_id']):r for r in records['grade_percentage']}
        self._components_by_offering=defaultdict(list)
        for r in sorted(records['grade_percentage'],key=lambda r:(periods[components[r['component_id']]['period_id']]['period_order'],r['component_id'])):
            component=components[r['component_id']]
            period=periods[component['period_id']]
            self._components_by_offering[r['class_id']].append(
                values(component,'component_id name type max_score description period_id')+
                (period['name'],r['percentage_id'],r['percentage']))
        enrollments={r['enrollment_id']:r for r in records['enrollment']}
        self._scores=defaultdict(list)
        for r in records['grade_component_score']:
            component=components[r['component_id']]
            period=periods[component['period_id']]
            cid=enrollments[r['enrollment_id']]['class_id']
            percentage=percentages[(cid,r['component_id'])]
            self._scores[r['enrollment_id']].append(
                values(r,'score_id score remarks date_recorded')+
                values(component,'component_id name type max_score description')+
                values(percentage,'percentage_id percentage class_id')+
                values(period,'name start_date end_date'))
        self.enrollment_count=len(records['enrollment'])

    def students(self):
        return self._students

    def student(self,sid):
        return self._student.get(sid)

    def teachers(self):
        return self._teachers

    def subjects(self):
        return self._subjects

    def periods(self):
        return self._periods

    def offerings(self):
        return self._offerings

    def enrollments_for_student(self,sid):
        return self._enrollments_by_student.get(sid,[])

    def enrollments_for_offering(self,cid):
        return self._enrollments_by_offering.get(cid,[])

    def components_for_offering(self,cid):
        return self._components_by_offering.get(cid,[])
