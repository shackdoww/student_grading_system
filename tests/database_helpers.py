"""Disposable, explicitly selected PostgreSQL schemas; never the school's schema."""
import os
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def isolated_database(dsn=None, install=True):
    dsn = dsn or os.getenv('CHECKLIST_TEST_DSN')
    if not dsn:
        pytest.skip('Set CHECKLIST_TEST_DSN to run isolated PostgreSQL checks.')
    schema = 'test_rubric_' + uuid4().hex
    with psycopg.connect(dsn) as connection:
        connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))

    def connect():
        connection = psycopg.connect(dsn)
        connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
        from app.database.connection import _actor
        try:
            from app.database.provenance import source_reference
            source = source_reference()
        except ImportError:
            source = ''
        connection.execute("SELECT set_config('app.actor', %s, false), set_config('app.source', %s, false)",
                           (_actor.get(), source or ''))
        connection.commit()
        return connection

    connect.schema_name = schema
    connect.dsn = dsn
    try:
        if install:
            with connect() as connection:
                connection.execute((ROOT / 'app/database/schema.sql').read_text())
        yield connect
    finally:
        with psycopg.connect(dsn) as connection:
            connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def master_records(connect):
    with connect() as c:
        c.execute("INSERT INTO student(student_id,first_name,last_name,program,year_level,status) VALUES ('S','Juan','Dela Cruz','BSCS',2,'Active')")
        c.execute("INSERT INTO teacher(teacher_id,first_name,last_name,department,status) VALUES ('T','Maria','Santos','IT','Active')")
        c.execute("INSERT INTO subject(subject_id,subject_code,subject_name,units) VALUES ('U','CSPC 103','OOP',3)")
        c.execute("INSERT INTO class(class_id,class_code,subject_id,teacher_id,section,school_year,semester,schedule) VALUES ('C','CSPC103-A','U','T','A','2026-2027','1st','MWF')")
        c.execute("INSERT INTO grading_period(period_id,name,period_order,start_date,end_date,school_year,semester) VALUES ('M','Midterm',1,'2026-01-01','2026-05-01','2026-2027','1st'),('F','Finals',2,'2026-05-02','2026-10-01','2026-2027','1st')")
        c.execute("INSERT INTO enrollment(enrollment_id,student_id,class_id,enroll_date,status) VALUES ('E','S','C',CURRENT_DATE,'Enrolled')")
        c.execute("INSERT INTO grade_component(component_id,period_id,name,type,max_score) VALUES ('MQ','M','Mid Quiz','Quiz',50),('ML','M','Mid Lab','Laboratory',100),('ME','M','Mid Exam','Exam',100),('FQ','F','Final Quiz','Quiz',50),('FL','F','Final Lab','Laboratory',100),('FE','F','Final Exam','Exam',100)")


def configure(connect, class_id='C'):
    with connect() as c:
        c.execute("INSERT INTO grading_policy(class_id,midterm_period_id,final_period_id,midterm_weight,final_weight) VALUES (%s,'M','F',40,60)", (class_id,))
        for component, weight in [('MQ',20),('ML',30),('ME',50),('FQ',20),('FL',30),('FE',50)]:
            c.execute('INSERT INTO grade_percentage(class_id,component_id,percentage) VALUES (%s,%s,%s)', (class_id,component,weight))
