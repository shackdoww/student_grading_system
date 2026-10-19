# Student Information and Grading System

## Checklist and GUI update

The current desktop interface uses neutral surfaces, rounded cards and controls,
and a restrained green accent. Student creation rejects an existing student
number; student editing keeps that number fixed. Year level is stored, student
and teacher email addresses are optional, and enrollment status can be updated
without changing scores. Admins can remove unused records; dependent records
remain protected. Score entry reloads saved scores for corrections and supports
confirmed score deletion for Admins.

Use the Class / Section page for the Class List and the Class Grades page's
Grade Sheet output for MG and FG grade points. The Student Report includes a
term selector, units, teachers, final grade points and the units-weighted GWA.
Reports display saved results only when they match current scores and weights.
Missing scores display **Incomplete**; changed grades display **Recompute
required** until saved again. The grade-point conversion uses the unrounded
percentage. Grade changes record their before/after values, signed-in actor
and time in `grade_audit_log`; Admins can open Audit history in Class Grades.

**Existing databases:** after updating dependencies and configuring `.env`, run
`python -m app.database.apply_migration --all` before launching. Migration 004
adds fields and audit tables without deleting academic records. Existing student
years are left unset for a person to enter accurately. Previously saved period
results need to be recomputed once to populate their grade-point equivalents.

**New databases:** create the database, execute `app/database/schema.sql` once,
then run `python -m app.database.apply_migration --all`. Copy `.env.example` to
`.env` and enter the actual connection settings. Do not rerun `schema.sql` on an
existing database. Launch with `python main.py` and create the first Admin
account when prompted; no default password is shipped.

Use a virtual environment and `python -m pip install -r requirements.txt`.
PySide6 was updated to 6.10.3, which supports Python 3.14 as well as Python 3.12
([official package metadata](https://pypi.org/project/PySide6/6.10.3/)). The old
6.10.0 pin could not install on Python 3.14.

See [the checklist audit](docs/checklist_audit.md) for case-by-case evidence
and the remaining database-model differences. This is not a claim of an awarded
100/100: the existing schema keeps components per class and period results in
`period_grade_results`, whereas the checklist appendix reuses six global
components and stores the consolidated results in `GRADE`.

Verification in an isolated test environment:

```powershell
python -m pytest -q
# Optional database acceptance test; creates and removes only a generated schema:
$env:CHECKLIST_TEST_DSN='host=localhost port=5432 dbname=your_test_database user=your_test_user'
python -m pytest tests/test_checklist_database.py -q
# Requires CREATE SCHEMA privileges. Use a test database, not a production account.
```

The acceptance test uses real PostgreSQL writes, loads the real PySide6 pages,
checks the supplied results and protected deletions, and launches a second GUI
process to verify persistence. It does not replace the instructor's live
mouse-and-keyboard demonstration.

## Architecture

`main.py` is the only application launcher. The GUI uses PySide6, services
validate and authorize workflows, repositories use parameter-bound PostgreSQL
queries, and the database enforces relationships and range checks.

```
app/
  calculator/       Grade normalization and grade-point scale
  database/         Connection, base schema and additive migrations
  gui/              Desktop pages, dialogs, report layouts and print/export
  repositories/     PostgreSQL persistence
  services/         Validated and role-scoped operations
main.py
requirements.txt
tests/
```

Period grading uses configurable policies and category weights. Enter explicit
zero scores when appropriate: missing scores block calculation. A class's
components belong to its category records; create separate components for
another class. Legacy consolidated grades are retained for compatibility,
while current reports use `period_grade_results` and its saved grade points.

The dashboard's student counts and program distribution use loaded records.
Set `STUDENT_HUB_REDUCED_MOTION=1` to reduce animations. Tables support CSV
export and print preview. CSV formula-like text is escaped and printed text is
HTML-escaped.

See [accounts and roles](docs/accounts_and_roles.md) for first-Admin setup,
permissions and deletion controls. Refer to [the checklist audit](docs/checklist_audit.md)
for the supplied cases, validation evidence and demonstration steps.
