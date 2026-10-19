"""Opt-in real PostgreSQL acceptance checks; never use the application's schema."""
import importlib
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from app.services.academic_service import AcademicService
from app.services.enrollment_service import EnrollmentService
from app.services.period_grading_service import PeriodGradingService
from app.services.score_service import ScoreService
from app.services.student_service import StudentService
from app.gui.data_snapshot import load_snapshot
from app.gui.checklist_reports import class_report, student_report


@pytest.fixture
def school(monkeypatch):
    dsn = os.getenv('CHECKLIST_TEST_DSN')
    if not dsn:
        pytest.skip('Set CHECKLIST_TEST_DSN to run isolated PostgreSQL acceptance checks.')
    schema = 'test_checklist_' + uuid4().hex
    with psycopg.connect(dsn) as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    def connect():
        conn = psycopg.connect(dsn)
        conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
        from app.database.connection import _actor
        actor=_actor.get()
        conn.execute("SELECT set_config('app.actor', %s, false)", ('checklist-tester' if actor=='system' else actor,))
        conn.commit()
        return conn
    connect.schema_name=schema
    root = Path(__file__).resolve().parents[1]
    try:
        with connect() as conn:
            conn.execute((root/'app/database/schema.sql').read_text())
            for migration in sorted((root/'app/database').glob('migration_*.sql')):
                conn.execute(migration.read_text())
            for migration in sorted((root/'app/database').glob('migration_*.sql')):
                conn.execute(migration.read_text())
        for path in (root/'app/repositories').glob('*.py'):
            module = importlib.import_module('app.repositories.'+path.stem)
            if hasattr(module, 'get_connection'):
                monkeypatch.setattr(module, 'get_connection', connect)
        monkeypatch.setattr('app.gui.data_snapshot.get_connection', connect)
        yield connect
    finally:
        with psycopg.connect(dsn) as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def test_checklist_create_validate_recompute_report_and_persist(school):
    connect = school
    students, academic = StudentService(), AcademicService()
    enrollment, scores = EnrollmentService(), ScoreService()
    periods = PeriodGradingService(connection_factory=connect)
    from app.services.account_service import AccountService
    from app.services.access_control import AccessGuard, SecuredService
    from app.services.record_deletion_service import RecordDeletionService
    auth=AccountService(connect)
    password='A disposable checklist passphrase'
    auth.create_account('checklistadmin','Checklist Tester',password,'admin',first_admin=True)
    token=auth.authenticate('checklistadmin',password)
    guard=AccessGuard(auth,token)
    deletion=RecordDeletionService(guard)
    for sid, first, last, program in [('2026-0001','Juan','Dela Cruz','BSCS'),
                                     ('2026-0002','Pedro','Reyes','BSCS'),
                                     ('2026-0003','Ana','Garcia','BSIT')]:
        students.create(sid,first,last,'',program,'Active',2)
    with pytest.raises(ValueError, match='already exists'):
        students.create('2026-0001','Other','Name','','BSIT','Active',1)
    with pytest.raises(ValueError):
        students.create('','Missing','Number','','BSCS','Active',2)
    students.save('2026-0003','Ana','Garcia','','BSCS','Active',2)
    students.create('2026-0099','Lea','Ramos','','BSIT','Active',1)
    deletion.delete('students','2026-0099')
    assert students.repository.find_by_id('2026-0099') is None
    with pytest.raises(ValueError):
        academic.save_teacher('BAD','','Name','','Department','Active')
    academic.save_teacher('T-1001','Maria','Santos','','Computer Studies Department','Active')
    academic.save_teacher('T-1001','Maria','Santos','','Information Technology Department','Active')
    academic.save_subject('SUB','CSPC 103','Object Oriented Programming','',3)
    academic.save_subject('SUB','CSPC 103','Object Oriented Programming','Object-oriented analysis, design and programming in Java',3)
    academic.save_subject('TEMP','TEMP','Temporary','',1)
    academic.delete_unreferenced('subjects','TEMP')
    with pytest.raises(psycopg.errors.UniqueViolation):
        academic.save_subject('DUP','CSPC 103','Duplicate','',3)
    with pytest.raises(ValueError):
        academic.save_subject('BAD','BAD','Bad','',0)
    academic.save_offering('O','CSPC103-A','MWF 9:00–10:00','A','2026-2027','1st','CS-201','T-1001','SUB')
    academic.save_offering('O','CSPC103-A','TTh 1:00–2:30','A','2026-2027','1st','CS-202','T-1001','SUB')
    with pytest.raises(ValueError,match='CSPC103-A'):
        academic.delete_unreferenced('teachers','T-1001')
    with pytest.raises(ValueError):
        academic.delete_unreferenced('subjects','SUB')
    for teacher,subject,year,semester in [('', 'SUB','2026-2027','1st'),('T-1001','','2026-2027','1st'),('T-1001','SUB','','1st'),('T-1001','SUB','2026-2027','')]:
        with pytest.raises(ValueError):
            academic.save_offering('BAD','BAD','Monday','A',year,semester,'',teacher,subject)
    ids = [enrollment.enroll(sid,'O','Enrolled') for sid in ['2026-0001','2026-0002','2026-0003']]
    with pytest.raises(ValueError, match='already enrolled'):
        enrollment.enroll('2026-0001','O','Enrolled')
    with pytest.raises(ValueError):
        enrollment.enroll('2026-9999','O','Enrolled')
    enrollment.update_status(ids[1], 'Dropped')
    enrollment.update_status(ids[1], 'Enrolled')
    with pytest.raises(ValueError):
        deletion.delete('students','2026-0001')
    with pytest.raises(ValueError):
        academic.delete_unreferenced('class_offerings','O')
    students.create('2026-0098','Carlo','Mendoza','','BSIT','Active',1)
    temporary=enrollment.enroll('2026-0098','O','Enrolled')
    deletion.delete('enrollments',temporary)
    for pid, order in [('M',1),('F',2)]:
        academic.save_period(pid,'Midterm' if pid=='M' else 'Finals',date(2026,1,1),date(2026,12,31),'2026-2027','1st',order)
    policy = dict(offering_id='O',midterm_period_id='M',final_period_id='F',midterm_weight=40,final_weight=60)
    def configure(oid, prefix):
        for category, weight in [('Q',20),('L',30),('E',50)]:
            academic.save_percentage(prefix+category,weight,oid)
            for pid in ['M','F']:
                academic.save_component(prefix+pid+category,pid+category,category,50 if category=='Q' else 100,'',pid,prefix+category)
        weights = [dict(period_id=p,percentage_id=prefix+c,weight=w) for p in ['M','F'] for c,w in [('Q',20),('L',30),('E',50)]]
        periods.save_policy(dict(policy,offering_id=oid), weights)
        return weights
    weights = configure('O','')
    invalid = [dict(w) for w in weights]
    invalid[2]['weight'] = 40
    with pytest.raises(ValueError):
        periods.save_policy(policy, invalid)
    for bad in [-5,'']:
        invalid=[dict(w) for w in weights]
        invalid[0]['weight']=bad
        with pytest.raises(ValueError):
            periods.save_policy(policy,invalid)
    with connect() as conn:
        assert conn.execute("SELECT weight FROM period_category_weights WHERE period_id='M' ORDER BY percentage_id").fetchall() == [(50,),(30,),(20,)]
    data = [[40,90,57,45,85,80],[20,60,55,30,70,65],[50,100,100,48,95,92]]
    components = ['MQ','ML','ME','FQ','FL','FE']
    for eid, values in zip(ids,data):
        for cid, value in zip(components,values):
            scores.record_score('SC-'+uuid4().hex,eid,cid,value)
    for value in [-5,55,float('nan')]:
        with pytest.raises(ValueError):
            scores.record_score('SC-'+uuid4().hex,ids[0],'MQ',value)
    with pytest.raises(ValueError):
        scores.record_score('removed-enrollment',temporary,'MQ',20)
    with pytest.raises(ValueError):
        deletion.delete('enrollments',ids[0])
    with pytest.raises(ValueError):
        academic.delete_unreferenced('grade_components','MQ')
    SecuredService(scores,guard).record_score('correction',ids[0],'ME',75)
    for eid, want in zip(ids,[82.3,60.7,96.22]):
        assert periods.calculate_and_save(eid)['overall'] == want
    with connect() as conn:
        assert conn.execute('SELECT count(*) FROM grade_component_scores').fetchone()[0] == 18
        ana_score = conn.execute("SELECT score_id FROM grade_component_scores WHERE enrollment_id=%s AND component_id='FQ'",(ids[2],)).fetchone()[0]
    scores.delete_score(ana_score)
    missing=class_report(load_snapshot(),'O',grade_sheet=True)
    assert missing['rows'][1][-1] == 'Incomplete'
    with pytest.raises(ValueError, match='Missing score'):
        periods.calculate_and_save(ids[2])
    scores.record_score('ana-quiz-reentry',ids[2],'FQ',48)
    for row,value in zip(weights[:3],[30,30,40]):
        row['weight'] = value
    periods.save_policy(policy,weights)
    outdated=class_report(load_snapshot(),'O',grade_sheet=True)
    assert outdated['rows'][0][-1] == 'Recompute required'
    for eid,want in zip(ids,[82.5,60.1,96.22]):
        assert periods.calculate_and_save(eid)['overall'] == want
    academic.save_teacher('T-1002','Jose','Ramos','','Physical Education Department','Active')
    academic.save_subject('PATH','PATHFIT 3','Physical Activity Towards Health and Fitness 3','',2)
    academic.save_offering('O2','PATHFIT3-A','TTh 3:00–5:00','A','2026-2027','1st','Gym','T-1002','PATH')
    configure('O2','P')
    pe = enrollment.enroll('2026-0001','O2','Enrolled')
    for cid,value in zip(components,[45,90,90,45,90,90]):
        scores.record_score('P'+cid,pe,'P'+cid,value)
    periods.calculate_and_save(pe)
    snapshot = load_snapshot()
    grade_sheet = class_report(snapshot,'O',grade_sheet=True)
    assert grade_sheet['headers'] == ['No.','Student','Course','MG','FG']
    assert grade_sheet['rows'] == [[1,'Dela Cruz, Juan','BSCS','2.50','2.25'],[2,'Garcia, Ana','BSCS','1.00','1.25'],[3,'Reyes, Pedro','BSCS','5.00','5.00']]
    report = student_report(snapshot,'2026-0001','2026-2027','1st')
    assert report['summary'] == ['Total Units: 5','No. of Subjects: 2','Grade Weighted Average: 2.05']
    assert [row[-1] for row in report['rows']] == ['2.25','1.75']
    assert 'Information Technology Department' in ' '.join(class_report(snapshot,'O')['metadata'])
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFontDatabase
    from PySide6.QtTest import QTest
    from app.gui import pyside_app as gui
    from app.gui.table_output import table_data
    app = QApplication.instance() or QApplication([])
    # Qt's offscreen Windows backend does not enumerate installed fonts.
    for font in ['segoeui.ttf','segoeuib.ttf']:
        path=Path('C:/Windows/Fonts')/font
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))
    app.setStyle('Fusion')
    app.setStyleSheet(gui.STYLE)
    monkey_loader = pytest.MonkeyPatch()
    monkey_loader.setattr(gui,'load_snapshot',lambda:snapshot)
    window=gui.StudentHub(token,auth)
    errors=[]
    window.error=errors.append
    try:
        window.show()
        for _ in range(300):
            if window._data_version:
                break
            QTest.qWait(10)
        assert window._data_version and not errors
        window.show_page('grades')
        assert table_data(window.grades.grade_sheet)[0] == ['No.','Student','Course','MG','FG']
        window.show_page('reports')
        window.reports.student.setCurrentIndex(window.reports.student.findData('2026-0001'))
        assert window.reports.list.item(0,5).text() == '2.25'
        assert '2.05' in window.reports.summary.text()
        window.show_page('roster')
        window.roster.teacher.setCurrentIndex(window.roster.teacher.findData('T-1002'))
        assert window.roster.offering.count()==1
        assert window.roster.offering.currentData()=='O2'
        window.roster.teacher.setCurrentIndex(0)
        window.roster.offering.setCurrentIndex(window.roster.offering.findData('O'))
        window.show_page('dashboard')
        window.dashboard.search.setText('Reyes')
        assert window.dashboard.student_table.rowCount() == 1
        window.dashboard.search.setText("' OR '1'='1")
        assert window.dashboard.student_table.rowCount() == 0
        window.dashboard.search.clear()
        directory=os.getenv('CHECKLIST_SCREENSHOT_DIR')
        if directory:
            folder=Path(directory)
            folder.mkdir(parents=True,exist_ok=True)
            window.resize(1440,960)
            for page in ['dashboard','grades','reports','roster']:
                window.show_page(page)
                QTest.qWait(300)
                assert window.grab().save(str(folder/(page+'.png')))
    finally:
        window.close()
        monkey_loader.undo()
    students.create('2026-0004','Kevin',"O'Brien",'','BSIT','Active',1)
    academic.save_offering('OTHER-TERM','CS-NEXT','Monday','B','2027-2028','2nd','Room','T-1001','SUB')
    future=enrollment.enroll('2026-0001','OTHER-TERM','Enrolled')
    scoped=student_report(load_snapshot(),'2026-0001','2026-2027','1st')
    assert len(scoped['rows'])==2 and scoped['summary'][-1].endswith('2.05')
    deletion.delete('enrollments',future)
    academic.delete_unreferenced('class_offerings','OTHER-TERM')
    with connect() as conn:
        assert conn.execute('SELECT count(*) FROM period_grade_results').fetchone()[0] == 4
        assert conn.execute("SELECT count(*) FROM grade_audit_log WHERE changed_by='checklist-tester'").fetchone()[0] >= 7
        assert conn.execute("SELECT changed_by FROM grade_audit_log WHERE table_name='grade_component_scores' AND action='UPDATE'").fetchone()[0] == 'checklistadmin'
        assert conn.execute("SELECT old_value->>'score',new_value->>'score' FROM grade_audit_log WHERE table_name='grade_component_scores' AND action='UPDATE'").fetchone() == ('57.00','75.00')
        assert conn.execute('SELECT year_level FROM students WHERE student_id=%s',('2026-0003',)).fetchone()[0] == 2
        assert conn.execute('SELECT count(*) FROM students').fetchone()[0] == 5
        assert conn.execute('SELECT count(*) FROM enrollments').fetchone()[0] == 4
    # A new connection and snapshot are the durable-state check, independent of the UI cache.
    assert student_report(load_snapshot(),'2026-0001','2026-2027','1st')['summary'][-1].endswith('2.05')
    child=subprocess.run([sys.executable,'-m','tests.checklist_restart_probe'],
        env=os.environ | {'CHECKLIST_SCHEMA':connect.schema_name,'CHECKLIST_TEST_TOKEN':token},
        capture_output=True,text=True,timeout=30)
    assert child.returncode==0,child.stdout+'\n'+child.stderr
