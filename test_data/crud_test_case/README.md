# CSPC 103 CRUD test-case dataset

This folder contains the **final saved state** in the CRUD document's appendix,
after all updates/recalculation, PATHFIT report setup, and PS-02. Use this folder
with the application's existing **Data Import** page.

## Import

1. Pull the latest project and run its current database installer/migrations.
2. Use a fresh test database to obtain the appendix's exact final row counts.
3. Sign in as Admin and open **Data Import**.
4. Select **this `test_data/crud_test_case` folder**, not its parent `test_data`.
5. Choose **Validate Data**, then confirm **Import**.
6. Open Class Grades and Student Reports to inspect the saved results.

The importer uses one transaction and updates matching IDs. It does not clear
unrelated records in a database that already has school data. The parent folder
still contains the older, larger example dataset.

## Included tables

| CSV | Rows |
| --- | ---: |
| school_students.csv | 5 |
| school_teachers.csv | 2 |
| school_subjects.csv | 2 |
| school_class_offerings.csv | 2 |
| school_enrollments.csv | 4 |
| school_grading_periods.csv | 2 |
| school_grade_components.csv | 6 |
| school_grade_percentages.csv | 12 |
| school_grade_component_scores.csv | 24 |
| school_grades.csv | 4 |
| school_grading_policies.csv | 2 |
| school_class_meetings.csv | 4 |

The document's example IDs and deletion gaps are preserved: subject 2,
enrollment 4 and score 16 are absent. Lea is absent; Carlo remains a student
without an enrollment. Kevin O'Brien is included. Ana is BSCS. Maria's department
and CSPC 103's schedule/room are the updated values. Six components are reused
by both classes.

CSPC 103 Midterm weights are **30/30/40** after GR-03; Finals are **20/30/50**.
PATHFIT uses **20/30/50** in both periods. Overall weights are **40/60**.
Juan's corrected Midterm Exam is **75**; Ana's Final Quiz is **48** in re-entered
score row 19.

| Student / class | Midterm % | Finals % | Overall % | MG | FG |
| --- | ---: | ---: | ---: | ---: | ---: |
| Juan / CSPC 103 | 81.00 | 83.50 | 82.50 | 2.50 | 2.25 |
| Pedro / CSPC 103 | 52.00 | 65.50 | 60.10 | 5.00 | 5.00 |
| Ana / CSPC 103 | 100.00 | 93.70 | 96.22 | 1.00 | 1.25 |
| Juan / PATHFIT 3 | 90.00 | 90.00 | 90.00 | 1.75 | 1.75 |

Juan's Student Grade report should show **5 units, 2 subjects, GWA 2.05**.

## Dates, times, provenance and audit

- Blank optional cells import as SQL NULL.
- The document labels enrollment/score/grade dates only as "test date". Those
  CSV columns are intentionally omitted so PostgreSQL fills the actual import
  date, instead of storing a fixed or invented historical test date.
- Period dates are "as entered" in the document. This dataset uses Midterm
  2026-01-01 through 2026-05-31 and Finals 2026-06-01 through 2026-10-31.
  Adjust these if your demonstration requires different period dates.
- Structured meetings interpret the displayed TTh 1:00–2:30 and TTh 3:00–5:00 as
  afternoon times: Tuesday/Thursday **13:00–14:30** and **15:00–17:00**.
- `set_by` preserves the appendix's explanatory source text. Grade and policy
  source references are supplied for these additional current-app fields;
  `finals_equiv` is included so reports have all three grade-point equivalents.
- Actual actors and audit timestamps come from the Admin performing the import.
  The CSVs do not impersonate "tester" or insert fabricated audit history.

This imports a snapshot. It does not perform the earlier delete/re-entry,
correction and recomputation actions, or recreate their seven historical audit
transitions. Demonstrate those actions manually or run the project's full
52-case acceptance test to obtain that evidence. Importing the snapshot itself
creates genuine audit entries for its writes.
