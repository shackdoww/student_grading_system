# Legacy school CSV example

These ten files describe the older class-owned category model (30 students,
8 teachers, 12 subjects/classes, 60 enrollments and 360 scores). They are not the
rubric's final demonstration dataset and must not be presented as such.

Select this folder in Data Import, validate, then confirm the transactional import.
The importer recognizes `percentage_id` on legacy components, converts exact
category averages to class/component weights, and preserves the original CSV
values in `import_archive`. It does not merge component identities or fabricate
period results from the old final-percentage column. Old schedules lack explicit
AM/PM values: confirm them in the class day/time editor. Configure the class
period policy and recompute grades afterward.

Canonical format uses the same filenames for master records, components, scores
and grades, plus `school_class_meetings.csv` and `school_grading_policies.csv`.
The column lists are declared in `app/services/school_data_import_service.py`.
Key changes: `class_id` replaces `offering_id`; components have no percentage
parent; weights have `class_id,component_id,percentage`; grades contain Midterm,
Finals, Overall and their equivalents. Meetings use weekday 1=Monday through
7=Sunday and 24-hour `start_time,end_time`. Optional `source_reference` is stored
as provenance; actor fields are always supplied by the signed-in application.

Use the same semester vocabulary across classes and periods. Optional emails,
descriptions and remarks may be blank. Nonfinite numbers, broken references,
invalid totals and timetable conflicts are rejected without saved changes.
