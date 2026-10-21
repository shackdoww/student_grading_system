"""Read-only, exact conversion of legacy category averages to component weights."""
from collections import defaultdict
from decimal import Decimal
from psycopg.rows import dict_row

TABLE_MAP = {
    'students':'student', 'teachers':'teacher', 'subjects':'subject',
    'class_offerings':'class', 'enrollments':'enrollment', 'grading_periods':'grading_period',
    'grade_components':'grade_component', 'grade_percentages':'grade_percentage',
    'grade_component_scores':'grade_component_score', 'grades':'grade',
    'grading_policies':'grading_policy', 'period_category_weights':None,
    'period_grade_results':None, 'grade_audit_log':'audit_log',
    'user_accounts':'user_accounts', 'account_sessions':'account_sessions', 'security_events':'security_events',
}


def component_weights(records):
    groups=defaultdict(list)
    for component in records.get('grade_components',[]):
        groups[(component['percentage_id'],component['period_id'])].append(component)
    explicit={(r['percentage_id'],r['period_id']):Decimal(str(r['weight'])) for r in records.get('period_category_weights',[])}
    categories={r['percentage_id']:r for r in records.get('grade_percentages',[])}
    output=[]; blockers=[]
    for (category_id,period_id),components in groups.items():
        category=categories[category_id]
        weight=explicit.get((category_id,period_id),Decimal(str(category['percentage'])))
        divided=weight/len(components)
        if divided.quantize(Decimal('.01'))*len(components)!=weight:
            blockers.append(f'Category {category_id}, period {period_id}: {weight}% cannot split exactly between {len(components)} components at two decimals.')
            continue
        for component in components:
            output.append({'percentage_id':f"W-{component['component_id']}", 'class_id':category['offering_id'],
                           'component_id':component['component_id'],'percentage':divided})
    return output,blockers


def inspect_legacy(connection):
    records={}
    with connection.cursor(row_factory=dict_row) as cursor:
        for table in TABLE_MAP:
            cursor.execute('SELECT to_regclass(%s)',(table,))
            if cursor.fetchone()['to_regclass'] is not None:
                from psycopg import sql
                cursor.execute(sql.SQL('SELECT * FROM {}').format(sql.Identifier(table)))
                records[table]=cursor.fetchall()
    weights,blockers=component_weights(records)
    for row in weights:
        if len(row['percentage_id'])>50:
            from uuid import uuid5,NAMESPACE_OID
            row['percentage_id']=str(uuid5(NAMESPACE_OID,row['percentage_id']))
    return {'status':'legacy','counts':{t:len(r) for t,r in records.items()},'blockers':blockers,
            'records':records,'weights':weights}
