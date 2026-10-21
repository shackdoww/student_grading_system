-- Read-only checks for the final fresh-database rubric scenario.
-- IDs may differ; foreign-key joins must identify the same parent records.
SELECT 'STUDENT' AS table_name,count(*) AS rows FROM student
UNION ALL SELECT 'TEACHER',count(*) FROM teacher
UNION ALL SELECT 'SUBJECT',count(*) FROM subject
UNION ALL SELECT 'CLASS',count(*) FROM class
UNION ALL SELECT 'ENROLLMENT',count(*) FROM enrollment
UNION ALL SELECT 'GRADING_PERIOD',count(*) FROM grading_period
UNION ALL SELECT 'GRADE_COMPONENT',count(*) FROM grade_component
UNION ALL SELECT 'GRADE_PERCENTAGE',count(*) FROM grade_percentage
UNION ALL SELECT 'GRADE_COMPONENT_SCORE',count(*) FROM grade_component_score
UNION ALL SELECT 'GRADE',count(*) FROM grade
UNION ALL SELECT 'AUDIT_LOG',count(*) FROM audit_log;

SELECT student_id,first_name,last_name,email,program,year_level,status,set_by AS "Set by",created_by,updated_by
FROM student ORDER BY student_id;

SELECT w.percentage_id,c.class_code,g.name AS component,w.percentage,w.set_by AS "Set by"
FROM grade_percentage w JOIN class c USING(class_id) JOIN grade_component g USING(component_id)
JOIN grading_period p USING(period_id)
ORDER BY c.class_code,p.period_order,g.component_id;

SELECT s.last_name,s.first_name,c.class_code,g.grade_id,g.enrollment_id,
       g.midterm_grade,g.finals_grade,g.overall_grade,g.midterm_equiv,g.finals_equiv,
       g.final_equiv,g.remarks,g.date_encoded
FROM grade g JOIN enrollment e USING(enrollment_id) JOIN student s USING(student_id)
JOIN class c USING(class_id) ORDER BY c.class_code,s.last_name,s.first_name;

SELECT log_id,table_name,record_id,action,old_value,new_value,changed_by,changed_at,source_reference
FROM audit_log ORDER BY log_id;

-- Review any legacy class lacking explicit timetable selections.
SELECT c.class_id,c.class_code,c.schedule FROM class c
WHERE NOT EXISTS(SELECT 1 FROM class_meeting m WHERE m.class_id=c.class_id);
