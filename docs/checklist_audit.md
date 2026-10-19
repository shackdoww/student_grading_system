# Student Grade Management System checklist audit

Reviewed 19 October 2026 against the supplied CSPC 103 finals checklist
(52 cases, 100 possible points). The original repository at
`34c167e8654220617b38bf4996226a739d330b43` did not fully meet that checklist.
The update fixes the functional gaps described below and refreshes the GUI.
This report is an engineering assessment, not an instructor-awarded score.

## What changed

- Student creation is separate from editing, rejects duplicate numbers even
  during concurrent inserts, and cannot change the number in the edit form.
  Year level is stored; student and teacher emails can be omitted.
- Students can be edited and unused students deleted with confirmation.
  Enrollment status can be updated without changing scores. New enrollments
  use the required Enrolled status. Protected deletion remains Admin-only.
- Score entry reloads saved values, corrects the existing score, and allows an
  Admin to delete a score after confirmation. Nonfinite scores are rejected.
- A central grade-point scale converts unrounded percentages. Period results
  persist Midterm, Finals and Overall percentages, their equivalents, and
  Passed/Failed remarks. The supplied original and recalculated values match.
- Grade changes are audited with old/new data, actor and timestamp. Audit
  history is restricted to Admin snapshots and has an on-screen viewer.
- The Class List, Grade Sheet and Student Grade report use the specified
  columns, last-name order and saved values. Student reports select one term,
  include units and teachers, and calculate the weighted grade-point average.
  Juan's result is **2.05** for 5 units across 2 subjects.
- Reports label missing scores Incomplete and refuse to present unsaved or
  outdated calculations as saved grades. Print output includes report headers
  and totals. CSV export remains a plain table of the displayed rows.
- The GUI uses neutral backgrounds, rounded cards, pill-shaped actions and a
  restrained green accent. Existing reduced-motion support is retained.
- The PySide6 dependency moves from 6.10.0 to 6.10.3 so the requirements can
  install with Python 3.14. The first baseline run used Python 3.12 because
  6.10.0 explicitly excluded 3.14.

## Evidence and limits

Final verification: **89 tests passed** on Python 3.14 with PySide6 6.10.3,
including the real PostgreSQL acceptance scenario. The existing
`python -m tests.verify_period_grading` integration checks also passed,
including account roles, ownership protection and deletion rollback. The
original unmodified suite passed 59 tests using Python 3.12/PySide6 6.10.0.
Python compilation, patch whitespace, and the 52-case/100-point audit totals
were checked. An independent code review found no remaining material blockers
within the approved scope after the audit-isolation and dependency-message
fixes.

`tests/test_checklist_regressions.py` covers the supplied grades, recalculation,
unrounded conversion boundaries, duplicate student protection, the corrected
email-import validation and nonfinite-number rejection.
`tests/test_checklist_ui.py` checks student identity/year editing and loading a
saved score for correction. Existing tests cover roles, confirmation/cancel,
atomic batch deletion, exports, animations and background loading.

`tests/test_checklist_database.py` uses real PostgreSQL in a uniquely named
disposable schema. It applies every migration twice; creates the supplied
master records and scores; checks invalid data, dependent deletions, score
correction/deletion, missing and outdated reports, recalculation, row counts,
signed-in audit attribution, term filtering, report values and SQL-safe names.
It opens the real PySide6 pages and searches for Reyes and the injection-shaped
search string. After closing the window, it launches a new GUI process that
loads the same committed records and checks the grade sheet and 2.05 report.

The test schema is removed after verification. No existing school database was
modified. Screenshots use the checklist's test records and a disposable Admin
account. The final live demonstration, printer selection and the instructor's
database-client inspection still need to be performed by the student/tester.

## Case-by-case assessment

**Ready** means the relevant path is implemented and has code/automated
evidence; it is not a claim that every click was manually demonstrated.
**Model difference** means behavior is supported but the appendix's exact
table/relationship requirement differs, as explained below. **Demo** marks a
remaining live interaction check rather than a known functional failure.
The Before column is based on source review and the original test baseline;
no numerical baseline grade is inferred from it.

| Case | Pts | Before | Updated assessment and evidence |
| --- | ---: | --- | --- |
| ST-01 | 2 | Required email; no year level | Ready — three students stored with omitted emails and year 2; list reloads. |
| ST-02 | 2 | Add could overwrite an existing student | Ready — create-only service and INSERT reject duplicate numbers without updating the original. |
| ST-03 | 1 | Required-field validation existed | Ready — blank student number/name rejected; no insert. |
| ST-04 | 2 | Search existed | Ready — Reyes UI search finds Pedro; editor loads saved fields. |
| ST-05 | 2 | No active student-edit action | Ready — Edit student saves Ana's program; number is read-only and year persists. |
| ST-06 | 1 | Admin Data Records deletion existed | Ready / Demo — Lea's deletion is verified in PostgreSQL; confirm the dashboard Yes/No interaction live. |
| ST-07 | 2 | Admin deletion protected dependencies | Ready — Juan's deletion is blocked while enrolled. |
| TE-01 | 2 | Email was mandatory | Ready — Maria is saved and listed with no email. |
| TE-02 | 1 | GUI duplicate-ID check existed | Ready / Demo — blank name is rejected; Add's existing-ID message is retained for live duplicate-ID demonstration. |
| TE-03 | 1 | Teacher list existed | Ready — saved teacher details are available in Academic and reports. |
| TE-04 | 2 | Teacher editing existed | Ready — department is changed and appears in the Class List header. |
| TE-05 | 2 | Generic dependency message | Ready — deletion is blocked and the message names CSPC103-A. |
| SU-01 | 2 | Supported | Ready — subject is persisted with 3 units. |
| SU-02 | 2 | Supported | Ready — duplicate code, zero and negative units are rejected. |
| SU-03 | 1 | Supported | Ready — subject catalog shows stored details. |
| SU-04 | 1 | Supported | Ready — description changes independently of the subject title and units. |
| SU-05 | 2 | Supported | Ready — unused subject removed; referenced CSPC 103 protected. |
| CL-01 | 3 | Supported | Ready — class references teacher and subject; term/schedule/room persist. |
| CL-02 | 2 | Supported | Ready — missing teacher, subject, school year or semester rejected. |
| CL-03 | 1 | No teacher filter | Ready — Class / Section filters offerings by teacher. |
| CL-04 | 2 | Supported | Ready — changed schedule and room appear in report metadata. |
| CL-05 | 2 | Supported | Ready — deletion of an enrolled class is blocked. |
| EN-01 | 3 | Used Active instead of Enrolled | Ready — generated internal keys, today's date and Enrolled status persist. |
| EN-02 | 2 | Supported | Ready — duplicate student/class membership rejected. |
| EN-03 | 1 | Supported | Ready — nonexistent student rejected; no orphan row. |
| EN-04 | 2 | Roster existed with different status vocabulary | Ready — class roster reflects saved membership/status. |
| EN-05 | 2 | No status-edit UI | Ready — status changes Dropped → Enrolled without changing scores. |
| EN-06 | 2 | Admin deletion supported | Ready — Carlo's empty enrollment removed; Juan's scored enrollment protected. |
| GP-01 | 2 | No explicit period order | Ready — order 1/2 is stored and shown; date and term fields retained. |
| GC-01 | 2 | Class-owned components | Model difference — six components for CSPC 103; another class needs its own six. |
| GW-01 | 2 | Split category/policy storage | Model difference — six per-period weights are stored with class/period/category references; not the appendix's exact GRADE_PERCENTAGE layout. |
| GW-02 | 3 | Period Setup validated totals | Ready — invalid 90% policy rejected atomically; previous saved weights remain. |
| GW-03 | 1 | Blank values could produce a Decimal error | Ready — negative/blank/nonfinite weights rejected with validation errors. |
| GC-02 | 1 | Supported by Academic and Period Setup | Ready — saved components, maximums and per-period weights can be inspected. |
| GC-03 | 2 | Protected deletion existed | Ready — a scored component cannot be deleted. |
| SC-01 | 3 | Supported | Ready — 18 linked scores and dates persist before the report setup. |
| SC-02 | 2 | Supported | Ready — 55/50 rejected. |
| SC-03 | 1 | Supported | Ready — negative score rejected. |
| SC-04 | 2 | Supported | Ready — removed enrollment cannot receive a score. |
| SC-05 | 1 | Dialog did not reload saved score values | Ready — selecting a component reloads its saved value and remarks. |
| SC-06 | 2 | Pair-based score upsert existed | Ready — 57 corrected to 75 without adding another score row; Midterm is 80.50. |
| SC-07 | 2 | Old reports could still show legacy values | Ready — missing Final Quiz shows Incomplete; re-entry restores calculability. |
| GR-01 | 3 | Percentages only | Model difference — expected Midterm values and grade points persist in period_grade_results, not GRADE. |
| GR-02 | 3 | No equivalents or Passed/Failed results | Model difference — expected Finals/Overall percentages, equivalents and remarks persist in period_grade_results. |
| GR-03 | 3 | Period recalculation existed | Model difference — expected recalculated values update the existing result rows; raw scores unchanged. |
| GR-04 | 1 | Security events lacked grade before/after data | Ready — grade_audit_log captures updates/deletes/inserts, actor and time. |
| RP-01 | 3 | Wrong columns/header/name order | Ready — required Class List headings, teacher/department, term, schedule/room and last-name order. |
| RP-02 | 3 | Calculated percentages rather than saved grade points | Ready — required No./Student/Course/MG/FG values read from current saved results. |
| RP-03 | 2 | Missing units, teacher, year and term scope | Ready — two saved subjects, title, teacher, units, F Grade and year appear for the selected term. |
| RP-04 | 2 | Simple percentage average | Ready — 5 units, 2 subjects and weighted grade-point average 2.05. |
| PS-01 | 2 | PostgreSQL persistence existed | Ready — a new application process opens saved grade-point reports after the first window closes. |
| PS-02 | 2 | Bound writes and in-memory search existed | Ready — O'Brien stored correctly; injection-shaped UI search returns no rows and cannot alter SQL. |

## Remaining differences that affect a strict 100-point claim

The original architecture links a component to a class-owned category. The
checklist appendix reuses six global components across CSPC 103 and PATHFIT 3.
Preserving this application's existing relationships requires **12 components**
for those two classes. The database stores base categories in
`grade_percentages`, the 12 per-period settings in `period_category_weights`,
and four consolidated period results in `period_grade_results`. The legacy
`grades` table is retained; it is not silently repurposed or populated with
ambiguous percentages. Reports use the new saved period results.

The students, teachers, subjects, classes, enrollments, periods and raw score
counts in the acceptance scenario match the appendix's corresponding records.
The component/weight/result table mapping does not match its literal schema
and final row counts. If the instructor requires that exact data model, this
version must not be presented as fully compliant. It needs a separately
planned data-model migration, including a safe conversion of existing
class-owned components and scores. Table-name casing or surrogate ID values
alone are not the issue; the component ownership relationship is different.

The supplied 52-case document does not by itself establish an implementation
language requirement. The application remains Python/PySide6/PostgreSQL as
approved. Any separate course requirement for Java, UML/CRC diagrams or other
submission artifacts needs to be checked against that separate specification.

## Installation and demonstration

1. Install the pinned dependencies in a virtual environment.
2. Configure `.env` from `.env.example` for the intended database.
3. On a new database only, execute `app/database/schema.sql` once.
4. Run `python -m app.database.apply_migration --all` on either a new or
   existing database. It applies additive migrations in order. Existing
   student years remain unset until entered; old period results need one
   recomputation to add their equivalents.
5. Run `python main.py`, create/sign in as an Admin for the full demonstration,
   and start from an empty school dataset as requested in the checklist.
6. Create records in the checklist order. Use Period Setup to select Midterm
   and Finals and save the 40/60 overall and 20/30/50 category settings. Enter
   scores through Record Score, then select each student and Save Period Grades.
7. After changing a score or policy, save the affected period grades again.
   Print the Class List, Grade Sheet and Student Grade outputs from their
   respective pages. Keep the database client open for the instructor's checks.

The original sample CSV files remain examples of the older class-owned model;
they are not a pre-filled database claiming to be the final checklist state.
They do not supply the newly added year levels or grade-point result fields.
