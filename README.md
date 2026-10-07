# Student Information and Grading System

A Python and PostgreSQL student information and grading system based on the project's UML design.

`main.py` is the only application launch entry point. The desktop interface
uses PySide6; unused compatibility launchers and Tkinter windows have been removed.
Academic records and grading
configuration can be maintained from the Academic page; referenced records
are protected from deletion. Tables support CSV export and print preview.
See [rubric alignment](docs/rubric_alignment.md) for verified coverage and
outstanding finals-project requirements.

The app now requires a school account. See [accounts and roles](docs/accounts_and_roles.md)
for first-Admin setup, permissions and manual deletion controls.

## Technologies

- Python 3
- PostgreSQL
- psycopg
- python-dotenv
- IntelliJ IDEA
- Git and GitHub

## Project Structure

```
app/
├── calculator/
│   ├── grade_calculator.py
│   └── period_calculator.py
├── database/
│   ├── connection.py
│   ├── schema.sql
│   └── migration_*.sql
├── gui/
│   ├── pyside_app.py
│   ├── academic_editor.py
│   ├── period_grading_dialog.py
│   ├── program_distribution.py
│   └── assets/icons/
├── repositories/
│   └── PostgreSQL repositories
└── services/
    └── validated application workflows

main.py
requirements.txt
tests/
```

## Backend Architecture

The system uses Python as the application backend and PostgreSQL as the database backend.

```
GUI
 ↓
Python Services
 ↓
Repositories
 ↓
PostgreSQL
```

Python services handle application rules and validation. Repositories handle SQL access. PostgreSQL stores the data and enforces database constraints.
The dashboard program-distribution chart uses the loaded student records,
not sample statistics. Its animation respects `STUDENT_HUB_REDUCED_MOTION=1`.

## Applying the Existing-Database Migration

If the database already exists, do not rerun `schema.sql` because it recreates the tables. Instead, run `app/database/migration_001_backend_validation.sql` once in PostgreSQL. It adds the grading validation triggers without dropping existing data.

## Setup

1. Create the PostgreSQL database named `student_grading_system`.
2. Run `app/database/schema.sql`.
   Then apply `app/database/migration_002_period_grading.sql` to add period
   grading tables. On an existing database, apply only the migration; do not
   recreate the schema. The migration can safely be run more than once.
   Also apply `app/database/migration_003_accounts.sql` (or run
   `python -m app.database.apply_migration --accounts`) before launching.
3. Create a local `.env` file:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=student_grading_system
DB_USER=postgres
DB_PASSWORD=your_actual_password
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run:

```bash
python main.py
```

## Grading Flow

```
Student
   ↓
Enrollment
   ↓
Grade Component Scores
   ↓
GradeCalculator
   ↓
GradingService
   ↓
GradeRepository
   ↓
grades table
```

The calculator converts each component score to a percentage, averages components that belong to the same grading percentage, applies the category weight, and adds the weighted results to produce the final grade.

## Midterm Final and Overall grades

Enrollment IDs are internal: the Enrollments page generates a unique ID when
creating each student/class link. Select a student, class offering and status;
there is no ID to type. Existing enrollment IDs are preserved. Ordinary rosters,
reports and exports show student numbers instead. Grade actions use a hidden
enrollment key, and score IDs are also generated automatically. CSV import
retains explicit identifiers for linking imported datasets.

The legacy calculation and saved grades remain unchanged. For the separate
period workflow, create components for two grading periods matching the class
school year and semester. In Class Grades, choose **Period Setup**, select the
Midterm and Final periods, and enter the overall weights and each period's
category weights. Each set must total 100%; the percentages are configurable,
not hard-coded. Category IDs refer to the existing Academic weights records.

Enter all required component scores, including explicit zero scores. Missing
scores block period calculation. **Save Period Grades** persists separate
Midterm, Final, and Overall values for the selected roster student. The grade
sheet includes raw scores and current calculations; the Readiness column shows
whether persisted results match. Configuration or score changes require saving
again to update stored results. Student reports include all three period values.
Select the period grade sheet in the output selector to export CSV or print.

Apply the additive migration from Python with:

```powershell
python -m app.database.apply_migration --period-grading
```

Verification:

```powershell
python -m pytest -q
python -m tests.verify_period_grading
python -m tests.gui_smoke
```

The period integration test creates a uniquely named isolated PostgreSQL schema,
checks durable results and recalculation, exercises the PySide6 reports, and
removes only that test schema afterward. It needs CREATE SCHEMA privileges.
