# Finals rubric alignment

The implementation remains Python, PySide6, and PostgreSQL by the project
owner's explicit decision. The rubric's Java deliverable is therefore an
intentional exception, not a claim of exact language compliance.

## Current coverage

The ten core PostgreSQL tables, parameter-bound repository queries, application
services, normalized configurable category calculation, raw score storage,
transactional CSV import, and CSV/print outputs already exist. Academic master
and configuration records now have Add, Edit, and protected Delete actions in
the active PySide6 Academic page. Foreign-key selections use existing records;
record IDs cannot change during editing. Writes run through existing services
on background workers and reload the cached presentation snapshot afterward.

Referenced academic records cannot be removed by the new deletion workflow.
It locks the parent row and checks direct dependents in the same transaction,
preventing the database's cascade rules from silently erasing score evidence.

## Refactoring evidence

Before this update the Academic page displayed records without maintenance
actions; the legacy Tkinter implementation retained the maintenance workflow.
The active UI now uses one reusable `RecordDialog` and editor action layer
instead of duplicating six forms. Input collection belongs to the GUI, existing
business validation remains in `AcademicService`, and protected SQL deletion
belongs to the persistence layer. No Tkinter workflow was reintroduced.
Git history records the exact before/after implementation.

## Outstanding requirements

- Independent Midterm and Final computation and configurable period-to-overall
  weights. The current calculator computes one category-weighted consolidated
  grade across submitted scores. It must not be relabeled as a period result.
- Persisted Midterm/Final/Overall results and configuration. The current schema
  has one `grades.final_grade` field and no overall period-weight configuration.
  This requires an approved additive migration, not destructive recreation.
- Grade sheets with every raw component score and all period/overall results.
- Student and enrollment edit/delete controls with the same evidence safeguards.
- Explicit domain values/interfaces, complete CRC/UML/ERD documentation, and
  repository write tests in an isolated test database.
- A complete automated create-class-to-print-grade-sheet end-to-end scenario.

Audit logs and user accounts are recommended extensions in the rubric, not
minimum core requirements. No accounts or schema changes were added here.

## Verification

Run `.venv\Scripts\python.exe -m pytest -q` for calculator, exports, animations,
background jobs, window controls, cached loading, editor validation, detached
editor values, and evidence-protecting deletion tests. The deletion tests mock
database calls and do not claim database-backed transaction verification.
Run `.venv\Scripts\python.exe -m tests.gui_smoke` with the local PostgreSQL
database to exercise real data loading, navigation, dialogs, and outputs.
This smoke test does not mutate school records.
