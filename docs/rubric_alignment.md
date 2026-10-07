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

## Period grading update

Migration 002 adds three tables without altering the ten existing core tables:
`grading_policies`, `period_category_weights`, and `period_grade_results`.
The separate PeriodCalculator strategy normalizes raw scores, averages scores
within a category, applies per-period category weights, and computes the overall
result with configurable period weights. Full precision is retained until the
final two-decimal rounding. Missing scores are rejected, not silently zeroed.
The legacy calculator and existing saved consolidated grades are unchanged.

PeriodGradingService validates term alignment and saves each policy and its
category weights atomically. Calculation reads policy, components and scores
and persists results in a serializable transaction. Class Grades provides setup,
saving, and an exportable/printable sheet containing raw component scores and
Midterm/Final/Overall results. Student reports include those results and indicate
when saved grades are outdated relative to current calculations.

`tests.verify_period_grading` verifies migration repeatability, durable saves,
configuration-based recalculation, invalid-policy rollback, preserved legacy
data, and PySide6 grade-sheet/student-report values in an isolated schema.
This is integration/UI evidence, not a complete mouse-driven end-to-end test.

## Outstanding requirements

The application now has one launcher, `main.py`. Unreferenced compatibility
launchers and legacy Tkinter windows were removed after checking their imports.
Existing application services and PostgreSQL mappings were retained; historic
GUI code is recoverable from Git. Tests enforce the absence of Tkinter imports.

- Student and enrollment edit/delete controls with the same evidence safeguards.
- Explicit domain values/interfaces, complete CRC/UML/ERD documentation, and
  repository write tests in an isolated test database.
- A complete automated create-class-to-print-grade-sheet end-to-end scenario.

User accounts and role-scoped application access are now implemented through
additive migration 003. Security events cover account management and explicit
record deletion. Comprehensive raw score/grade change auditing remains a future
extension; these security events do not claim to be that full grade-change log.
See `accounts_and_roles.md` for scope and local desktop security limitations.

## Verification

Run `.venv\Scripts\python.exe -m pytest -q` for calculator, exports, animations,
background jobs, window controls, cached loading, editor validation, detached
editor values, and evidence-protecting deletion tests. The deletion tests mock
database calls and do not claim database-backed transaction verification.
Run `.venv\Scripts\python.exe -m tests.gui_smoke` with the local PostgreSQL
database to exercise real data loading, navigation, dialogs, and outputs.
This smoke test does not mutate school records.
