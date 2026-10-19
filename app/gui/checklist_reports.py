"""Report layouts built from saved, current database results in a snapshot."""
from decimal import Decimal, ROUND_HALF_UP


def _context(records, offering_id):
    offering = next(r for r in records['class_offerings'] if r['offering_id'] == offering_id)
    subject = next(r for r in records['subjects'] if r['subject_id'] == offering['subject_id'])
    teacher = next(r for r in records['teachers'] if r['teacher_id'] == offering['teacher_id'])
    return offering, subject, teacher


def saved_result(snapshot, enrollment_id):
    saved = next((r for r in snapshot.records()['period_grade_results'] if r['enrollment_id'] == enrollment_id), None)
    try:
        current = snapshot.period_result(enrollment_id, include_equivalents=True)
    except ValueError:
        return None, 'Incomplete'
    fields = ['midterm_equiv','finals_equiv','final_equiv']
    if not saved or any(saved.get(k) is None for k in fields):
        return None, 'Not saved'
    if any(float(saved[k+'_grade']) != current[k] for k in ['midterm','final','overall']) or any(float(saved[k]) != current[k] for k in fields):
        return None, 'Recompute required'
    return saved, saved.get('remarks') or 'Saved'


def class_report(snapshot, offering_id, grade_sheet=False):
    records = snapshot.records()
    offering, subject, teacher = _context(records,offering_id)
    students = {s['student_id']:s for s in records['students']}
    roster = [r for r in records['enrollments'] if r['offering_id']==offering_id and r['status']!='Dropped']
    roster.sort(key=lambda r:(students[r['student_id']]['last_name'].casefold(),students[r['student_id']]['first_name'].casefold()))
    rows=[]
    for number,enrollment in enumerate(roster,1):
        student=students[enrollment['student_id']]
        row=[number,f"{student['last_name']}, {student['first_name']}",student['program']]
        if grade_sheet:
            saved,status=saved_result(snapshot,enrollment['enrollment_id'])
            row += [f"{saved[k]:.2f}" if saved else status for k in ['midterm_equiv','final_equiv']]
        rows.append(row)
    return dict(title='Grade Sheet' if grade_sheet else 'Class List',
        metadata=[f"Subject: {subject['subject_code']} – {subject['subject_name']}     Section: {offering['section']}",
                  f"Teacher: {teacher['first_name']} {teacher['last_name']}, {teacher['department']}",
                  f"Term: {offering['semester']} Semester, SY {offering['school_year']}",
                  f"Schedule / Room: {offering['schedule']}, {offering.get('room') or 'TBA'}"],
        headers=['No.','Student','Course','MG','FG'] if grade_sheet else ['No.','Student Name','Course'],rows=rows,summary=[])


def student_report(snapshot, student_id, school_year, semester):
    records=snapshot.records()
    student=next(r for r in records['students'] if r['student_id']==student_id)
    year=student.get('year_level')
    suffix={1:'st',2:'nd',3:'rd'}.get(year,'th')
    metadata=[f"Student Name: {student['last_name']}, {student['first_name']}     Course: {student['program']}     Year: {str(year)+suffix if year else 'Not entered'}",
              f'Term: {semester} Semester, SY {school_year}']
    enrolled=[]
    for enrollment in records['enrollments']:
        if enrollment['student_id'] != student_id or enrollment['status']=='Dropped':
            continue
        offering,subject,teacher=_context(records,enrollment['offering_id'])
        if (offering['school_year'],offering['semester']) == (school_year,semester):
            enrolled.append((subject['subject_code'],enrollment,subject,teacher))
    rows=[]; units=Decimal(0); weighted=Decimal(0); complete=True
    for number,(_,enrollment,subject,teacher) in enumerate(sorted(enrolled,key=lambda r:r[0]),1):
        saved,status=saved_result(snapshot,enrollment['enrollment_id'])
        grade=Decimal(str(saved['final_equiv'])) if saved else None
        subject_units=Decimal(str(subject['units']))
        units+=subject_units
        if grade is None:
            complete=False
        else:
            weighted+=grade*subject_units
        rows.append([number,subject['subject_code'],subject['subject_name'],f"{teacher['first_name']} {teacher['last_name']}",subject['units'],f'{grade:.2f}' if grade is not None else status])
    average=f'{(weighted/units).quantize(Decimal(".01"), rounding=ROUND_HALF_UP):.2f}' if units and complete else 'Incomplete' if rows else '—'
    return dict(title='Student Grade',metadata=metadata,
        headers=['No.','Subject Code','Description','Teacher','Units','F Grade'],rows=rows,
        summary=[f'Total Units: {units:g}',f'No. of Subjects: {len(rows)}',f'Grade Weighted Average: {average}'])
