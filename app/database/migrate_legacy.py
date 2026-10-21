"""Versioned, transactional fresh installation and evidence-preserving conversion."""
from pathlib import Path
from uuid import uuid4
from psycopg import sql
from psycopg.types.json import Jsonb
from app.database.migration_preflight import TABLE_MAP, inspect_legacy

ROOT=Path(__file__).parent


def _insert(connection,table,rows):
    for row in rows:
        if not row:
            continue
        keys=list(row)
        connection.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(
            sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,keys)),
            sql.SQL(',').join(sql.Placeholder() for _ in keys)),
            [Jsonb(row[k]) if isinstance(row[k],(dict,list)) else row[k] for k in keys])


def migrate(connection, *, preflight_only=False):
    # Must be the first transaction statement; migration serializes with app writers.
    connection.execute("SELECT pg_advisory_xact_lock(hashtext(current_schema() || ':rubric-schema'))")
    if connection.execute("SELECT to_regclass('schema_version')").fetchone()[0]:
        version=connection.execute('SELECT max(version) FROM schema_version').fetchone()[0]
        if version!=5:
            raise ValueError(f'Unsupported schema version {version}; no changes applied.')
        return {'status':'current','version':version,'blockers':[]}
    if not connection.execute("SELECT to_regclass('students')").fetchone()[0]:
        tables=connection.execute("SELECT tablename FROM pg_tables WHERE schemaname=current_schema()").fetchall()
        if tables:
            raise ValueError('Unrecognized database layout; no changes applied.')
        if not preflight_only:
            connection.execute((ROOT/'schema.sql').read_text())
        return {'status':'fresh' if preflight_only else 'installed','version':5,'blockers':[]}
    report=inspect_legacy(connection)
    if preflight_only:
        return {k:v for k,v in report.items() if k not in ('records','weights')}
    if report['blockers']:
        raise ValueError('Migration blocked: '+' '.join(report['blockers']))
    records=report['records']
    archive='legacy_rubric_'+uuid4().hex[:16]
    connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(archive)))
    for table in records:
        connection.execute(sql.SQL('LOCK TABLE {} IN ACCESS EXCLUSIVE MODE').format(sql.Identifier(table)))
    # Re-read under locks; preflight information must not race a school write.
    report=inspect_legacy(connection)
    if report['blockers']:
        raise ValueError('Migration blocked: '+' '.join(report['blockers']))
    records=report['records']
    for table in records:
        connection.execute(sql.SQL('ALTER TABLE {} SET SCHEMA {}').format(sql.Identifier(table),sql.Identifier(archive)))
    connection.execute((ROOT/'schema.sql').read_text())
    for table in ('student','teacher','subject','class','enrollment','grading_period','grade_component',
                  'grade_percentage','grade_component_score','grade','grading_policy'):
        connection.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER provenance').format(sql.Identifier(table)))
        connection.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER audit').format(sql.Identifier(table)))
    for old in ('students','teachers','subjects','class_offerings','enrollments','grading_periods','grade_components'):
        rows=[]
        for record in records.get(old,[]):
            row=dict(record)
            if 'offering_id' in row: row['class_id']=row.pop('offering_id')
            if old=='grade_components': row.pop('percentage_id')
            if old in ('students','teachers') and not row.get('email'): row['email']=None
            rows.append(row)
        _insert(connection,TABLE_MAP[old],rows)
    _insert(connection,'grade_percentage',report['weights'])
    _insert(connection,'grade_component_score',records.get('grade_component_scores',[]))
    _insert(connection,'grading_policy',[dict((('class_id' if k=='offering_id' else k),v) for k,v in r.items()) for r in records.get('grading_policies',[])])
    for result in records.get('period_grade_results',[]):
        row={k:v for k,v in result.items() if k!='calculated_at'}
        row['grade_id']='G-'+row['enrollment_id']
        if len(row['grade_id'])>50: row['grade_id']=str(uuid4())
        row['finals_grade']=row.pop('final_grade')
        when=result.get('calculated_at')
        if when:
            row.update(date_encoded=when.date(),created_at=when,updated_at=when)
        # Old migration-002 results can lack equivalents. Preserve those in archive,
        # and require recomputation rather than inventing unrounded equivalents.
        if any(row.get(k) is None for k in ('midterm_equiv','finals_equiv','final_equiv','remarks')):
            continue
        _insert(connection,'grade',[row])
    for table in ('user_accounts','account_sessions','security_events'):
        _insert(connection,table,records.get(table,[]))
    for row in records.get('grade_audit_log',[]):
        row=dict(row)
        row.pop('log_id',None)
        _insert(connection,'audit_log',[row])
    # Reset the copied security event sequence without assuming its schema/name.
    connection.execute("SELECT setval(pg_get_serial_sequence('security_events','event_id'),GREATEST(COALESCE((SELECT max(event_id) FROM security_events),0),1),(SELECT count(*)>0 FROM security_events))")
    connection.execute('SET CONSTRAINTS ALL IMMEDIATE')
    for table in ('student','teacher','subject','class','enrollment','grading_period','grade_component',
                  'grade_percentage','grade_component_score','grade','grading_policy'):
        connection.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER provenance').format(sql.Identifier(table)))
        connection.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER audit').format(sql.Identifier(table)))
    connection.execute('SET CONSTRAINTS ALL IMMEDIATE')
    return {'status':'migrated','version':5,'archive_schema':archive,'counts':report['counts'],'blockers':[]}
