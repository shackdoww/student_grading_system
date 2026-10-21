# Rubric Database Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native execution, or superpowers:subagent-driven-development if the owner selects delegation. Track work using the checkboxes below.

**Goal:** Make normal application workflows produce the rubric's actual PostgreSQL tables and final records, including requested provenance, and remove superseded grading functions.

**Architecture:** Replace class-owned categories/components with shared period components and class/component weights. Save consolidated results in one grade table, preserve accounts and the existing desktop/service/repository structure, and convert existing records through a transactional versioned migration with a legacy archive.

**Tech Stack:** Python 3.12+, PySide6 6.10.3, Psycopg 3.3.6, PostgreSQL, pytest 8.4.2.

**Spec:** [Approved design](../specs/2026-10-21-rubric-database-alignment-design.md).

## Global Constraints

- Canonical physical tables use the singular names and column names in the approved design; no rubric-shaped views disguising the old model.
- Fresh acceptance counts: student 5; teacher 2; subject 2; class 2; enrollment 4; grading_period 2; grade_component 6; grade_percentage 12; grade_component_score 24; grade 4; audit_log at least 7.
- Preserve Python, PySide6, PostgreSQL, account restrictions, background loading, imports, exports, printing and protected batch deletion.
- `set_by` stores ordered source references; signed-in actors populate separate actor fields and audit entries. Do not manufacture past actors or source references.
- Convert grade points before rounding percentages; missing scores block calculation; one saved grade per enrollment; FG means Overall equivalent.
- Preserve existing records and archived evidence. Do not migrate an external school database, reset records, seed demonstration data or push GitHub changes without further instructions.
- Commit coherent tested milestones locally. Do not claim manual printing or instructor-awarded compliance from automated checks.

## Review Focus

- Simultaneous duplicate enrollment/student creation must fail clearly without overwriting a record; test in Task 3 with two database connections.
- A shared component edit must not invalidate another class's scores or permit a Teacher to alter another class; test in Tasks 1 and 4.
- A policy transaction temporarily passing through a non-100 total must succeed only when its committed total is 100; test deferred checks and failed-transaction audit rollback in Tasks 1 and 3.
- Migration of multiple components in one old category must preserve exact weighting or stop without modifications; test finite and nonrepresentable splits in Task 2.
- Changing a score very close to a grade-point threshold must invalidate saved report results even if rounded percentages match; test grade equivalents and partial results in Tasks 3 and 4.

---

### Task 1: Canonical PostgreSQL schema, constraints and provenance

**Files:** Replace `app/database/schema.sql`; extend `app/database/connection.py`; create `app/database/provenance.py`, `tests/test_rubric_schema.py`, `tests/database_helpers.py` and `tests/test_provenance.py`; retain old schema/migrations as migration fixtures under `tests/fixtures/legacy_database/`.

**Interfaces:**
- `write_source(reference: str | None)` is a context manager carrying validated source text; `audit_actor(username)` remains the trusted actor context.
- `get_connection()` sets actor/source session settings without leaving an open transaction before caller isolation configuration.
- `tests.database_helpers.isolated_database(dsn)` creates/drops only a generated test schema, applies the canonical schema and yields a connection factory. Respect `CHECKLIST_TEST_DSN` and skip when absent.
- Domain IDs stay VARCHAR(50), with UUID-based database defaults for new internal IDs; supplied legacy IDs are preserved. Student numbers and teacher IDs remain explicit.
- `grade` includes nullable partial result fields, `finals_equiv`, `date_encoded` and provenance. `grading_policy` stores class_id, selected periods and overall weights. `schema_version` identifies the installed canonical version.

- [x] Add failing PostgreSQL tests asserting all required columns/relationships; six components assigned independently to two classes; uniqueness of class/component, enrollment/component and enrollment/grade.
- [x] Add failing tests for null optional emails, blank identifiers/names, invalid dates/year/units, NaN/Infinity, score ranges, wrong class/period assignments and restrictive parent deletions.
- [x] Add deferred-total tests: save 30/30/40 atomically; reject 20/30/40 at commit; keep previous weights and audit rows unchanged after rollback. Reject a policy referencing incompatible terms and reject component definition changes invalidating existing data.
- [x] Run `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_rubric_schema.py tests/test_provenance.py -q` against an isolated PostgreSQL instance and record the expected baseline failures.
- [x] Implement canonical DDL, indexes and database validation/audit/provenance triggers. Use explicit inserts, stable primary keys, ordered unique Set by references, no-op update detection and timestamps from PostgreSQL. Deletion audit records survive parent deletion.
- [x] Run the same tests to PASS, including forged actor fields being replaced by the trusted connection context on application writes and identical-value updates not emitting false changes. Commit the milestone.

### Task 2: Safe fresh install and legacy migration

**Files:** Modify `app/database/apply_migration.py`; create `app/database/migrate_legacy.py`, `app/database/migration_preflight.py`, `tests/test_rubric_migration.py`.

**Interfaces:**
- `inspect_legacy(connection) -> dict` returns table inventories, proposed component/weight/result mappings and blocking record IDs without writing.
- `migrate(connection, *, preflight_only: bool = False) -> dict` installs fresh canonical schema or converts the recognized existing schema inside one transaction. Hold an advisory migration lock; reject unknown/partially incompatible layouts.
- CLI retains `--all`, adds `--preflight` and routes canonical reruns to a no-op; deprecated flags explain that the unified installer is now used rather than executing old migrations against new tables.
- Archive name derives from the target schema and version, and old-to-new mappings are retained. Account/session/security tables remain usable with teacher references rewired transactionally.

- [x] Add failing tests for fresh install, repeat install, migration-004 empty/populated schemas and unknown schema rejection. Verify IDs, timestamps, accounts, raw scores and original archived rows.
- [x] Add conversion tests for one component per category, exact finite division for multiple components and rejected nonrepresentable division. Compare computed percentages and grade points before/after every convertible complete legacy enrollment.
- [x] Add rollback tests for an injected failure and for incompatible period/category data. Assert no partially migrated canonical schema, changed academic records or fabricated historical provenance.
- [x] Run `... pytest tests/test_rubric_migration.py -q` and observe failures before implementation.
- [x] Implement version dispatch, preflight, locked transactional archive/conversion and sequence/default initialization. Use archive schema qualification in all legacy reads. Preserve old audit entries; legacy grades lacking period data remain archived and active reports require recomputation.
- [x] Run migration tests to PASS and repeat `--all` successfully. Commit the milestone.

### Task 3: Canonical repositories, grading and authorization

**Files:** Modify `app/repositories/*_repository.py`, `app/repositories/protected_delete.py`, `app/services/academic_service.py`, `app/services/period_grading_service.py`, `app/services/score_service.py`, `app/services/enrollment_service.py`, `app/services/student_service.py`, `app/services/access_control.py`, `app/services/record_deletion_service.py`, `app/calculator/period_calculator.py`; create `tests/test_rubric_services.py`; update existing account, enrollment, deletion and calculator tests.

**Interfaces:**
- `AcademicService.save_component(component_id, name, component_type, max_score, description, period_id)` manages a shared definition; `get_components(class_id)` returns only the class's assigned definitions.
- `PeriodGradingService.save_policy(policy, weights)` consumes policy keys class_id, midterm_period_id, final_period_id, midterm_weight, final_weight, and weight dictionaries component_id/percentage. It inserts/updates class/component rows in place, retaining percentage IDs and meaningful audit changes.
- `PeriodGradingService.calculate_and_save(enrollment_id, period=None)` supports full calculation or Midterm-only calculation and upserts the canonical grade. It returns calculated fields; unavailable periods are null on partial saves.
- `PeriodCalculator.calculate(policy, weights, components, scores, include_equivalents=False, period=None)` uses per-component weights. `GradeCalculator.grade_point` remains the single scale.
- `SecuredService` accepts optional `source_reference` on exposed writes, establishes `write_source` and trusted actor contexts, and does not pass actor identity supplied by the user. Service calls within these contexts inherit provenance.
- Keep master-record tuple presentation adapters stable where harmless; use explicit named mappings for component/weight/result relationships. Domain field names are class_id/finals_grade throughout persistence.

- [x] Add failing service tests for exact initial and recalculated CSPC results, PATHFIT reuse without extra components, score correction preserving row ID, deletion/re-entry, full/partial grade uniqueness and missing-score failures.
- [x] Add tests for concurrent duplicate student/enrollment attempts and clear validation errors. Add provenance accumulation and signed-in audit attribution for scores, policy edits, grade saves, imports and batch deletion.
- [x] Add role tests: Admin/Dean maintain shared definitions; Teacher can assign existing components and edit weights/scores/results only for assigned classes; Registrar cannot change grades. Reassignment and guessed foreign IDs cannot bypass scope.
- [x] Run targeted service/calculator/account/enrollment/deletion tests to confirm the old contracts fail the new requirements.
- [x] Implement new repository SQL, services, Decimal calculation, partial results, protected dependencies and authorization. Reject shared-definition edits that invalidate any assignment or score. Serialize policy/result changes and retain existing error/rollback guarantees.
- [x] Run targeted tests to PASS plus schema/migration tests. Commit the milestone.

### Task 4: Desktop editors, snapshots, reports and provenance inspection

**Files:** Modify `app/gui/academic_editor.py`, `app/gui/period_grading_dialog.py`, `app/gui/pyside_app.py`, `app/gui/data_snapshot.py`, `app/gui/checklist_reports.py`, `app/gui/accounts.py`, `tests/ui_helpers.py`, `tests/test_academic_editor.py`, `tests/test_checklist_ui.py`, `tests/test_ui_loading.py`, `tests/test_checklist_regressions.py`; create `tests/test_rubric_ui.py`.

**Interfaces:**
- `DataSnapshot` consumes canonical table dictionaries, indexes class/component assignments, exposes canonical saved grades and calculates current results from the same period calculator used by services.
- Policy dialog selects shared components for each period and class, saves all weights atomically and returns the Task 3 contracts. Shared component editing has no class-owned percentage selector.
- Dialogs and write actions supply source_reference; Data Records/record inspection displays stored Set by and actor/timestamp fields without altering the required report column layouts.
- Grade actions expose Compute/Save Midterm and Save Grades against one service/store; missing Finals does not prevent Midterm-only saving. Changed or partial results cannot appear as completed FG values.

- [x] Add failing GUI tests for shared component selection, per-class independent weights, source entry, read-only actor inspection and role-disabled shared-definition edits.
- [x] Add report tests for exact headers/column order, Juan/Ana/Pedro name order, updated department/schedule/room, final grade points and Juan's 5-unit/2-subject/2.05 GWA.
- [x] Add threshold tests where rounded percentages match but grade points differ, stale policy changes, incomplete scores, null partial results and empty reports.
- [x] Run `QT_QPA_PLATFORM=offscreen ... pytest tests/test_rubric_ui.py tests/test_checklist_ui.py tests/test_ui_loading.py -q` and observe failures before edits.
- [x] Update snapshots, scoped data, editors, actions, permission labels and record inspection. Preserve async writes/reloads, selection, reduced motion, export and print behavior.
- [x] Run GUI/report/loading/output tests to PASS and commit the milestone.

### Task 5: CSV compatibility and removal of superseded functions

**Files:** Modify `app/services/school_data_import_service.py`, `app/services/student_service.py`, `test_data/*.csv`, `test_data/README.md`, `app/gui/pyside_app.py`, `app/gui/data_snapshot.py`, `app/calculator/grade_calculator.py`; remove `app/services/grading_service.py` and `app/repositories/grade_repository.py` once unused; adapt `tests/test_grade_calculator.py`, `tests/verify_database.py`, `tests/verify_snapshot.py`, `tests/verify_period_grading.py`, `tests/verify_accounts.py`; create `tests/test_rubric_import.py` and extend `tests/test_app_cleanup.py`.

**Interfaces:**
- `SchoolDataImportService.read_folder(folder)`, `validate(datasets)` and `import_all(datasets)` remain the entrypoints. Canonical files carry shared components, class/component weights, policies, consolidated grades and optional source references/year level.
- Detect legacy-format headers, normalize through the same conversion rules as migration, and reject incompatible conversions before writes. Optional blank text/email fields become null where appropriate. One transaction includes all writes/audit/provenance.
- Remove `GradingService`, old GradeRepository, `calculate_and_save_grade`, legacy calculator `calculate`/`calculate_breakdown`, snapshot legacy grade branches, Save Legacy Grade/save_grade, and active period_category_weights/period_grade_results paths. Keep only the grade-point scale in GradeCalculator.

- [x] Add failing canonical round-trip import tests, blank optional email/year handling, NaN/Infinity rejection, uniqueness and foreign-key checks, invalid policy rollback and source attribution.
- [x] Add legacy-format conversion success/rejection tests and an integration check that the documented bundled dataset imports into an isolated schema without changing computed results.
- [x] Add cleanup tests that production imports/call sites do not reference removed services, handlers, legacy result tables or old calculator methods; explicitly exclude migration fixtures/archive conversion from that ban.
- [x] Run import and cleanup tests, implement canonical import normalization/validation, update sample files/documentation and remove obsolete code only after replacement tests pass.
- [x] Run affected tests and `rg` reference checks to confirm no dangling production references. Commit the milestone.

### Task 6: Full appendix acceptance, restart evidence and documentation

**Files:** Replace old-model assertions in `tests/test_checklist_database.py`, update `tests/checklist_restart_probe.py`, create `tests/fixtures/rubric_expected.json` and `tests/rubric_comparison.py`; update `README.md`, `docs/checklist_audit.md`, `docs/rubric_alignment.md`, `docs/accounts_and_roles.md`, `.env.example` if needed, and this plan's checkboxes.

**Interfaces:**
- `rubric_expected.json` records every final appendix row by natural keys, counts, permitted nulls, expected missing rows and seven minimum audit transitions. Surrogate IDs are resolved by relationships; do not hard-code generated values.
- `tests.rubric_comparison.compare(connection) -> dict` returns per-table expected/actual counts and field discrepancies; the acceptance run writes a JSON report to an explicit artifact path outside tracked school data.
- Restart probe uses the same committed isolated schema and the real GUI/snapshot/report code in a second process.

- [x] Implement fixture expectations and execute all 52 cases via production services/secured boundaries with actual source references. Assert every intermediate rejection/update/deletion and unchanged raw scores after recalculation. GUI tests cover the dialogs and confirmation/cancel boundaries.
- [x] Compare all final tables, provenance, null fields, forbidden records, grade values and audit transitions. Verify accounts/security/policy metadata is separate from rubric row counts. Confirm actor values come from real disposable authenticated accounts.
- [x] Launch a second GUI process, reload records and assert the saved Grade Sheet and Student Grade outputs. Persist the machine-readable comparison artifact.
- [x] Run the full suite with PostgreSQL enabled: `QT_QPA_PLATFORM=offscreen CHECKLIST_TEST_DSN=<isolated-test-dsn> .venv/bin/python -m pytest -q`. All tests must pass; opt-in DB tests must run rather than skip.
- [x] Run the retained standalone integration probes against a disposable test database, `python -m compileall -q app tests`, `git diff --check`, and scan for active old-model references. Resolve regressions before completion.
- [x] Update installation/migration/preflight commands, schema descriptions, provenance behavior, class assignment/grade actions, CSV compatibility, deletion ordering and rubric evidence. Distinguish automated evidence from remaining live keyboard/mouse and physical-printer checks.
- [x] Review the final diff against every approved spec section, record limitations/evidence, commit the tested work and report the local branch/commit and comparison artifact. Do not push automatically.

## Execution handoff

Recommended execution: Native, implementing this plan in the current session. The schema, migration, services and GUI contracts are tightly coupled; a single implementer keeps those changes coordinated. Use the approved design plus this plan, and the worktree/TDD/execution/review skills at the appropriate gates. The owner approved native execution with “Go.”

## Execution amendment and evidence

The owner additionally requested selectable schedule days/times and prevention of
conflicts. Added `app/services/scheduling.py`, `app/gui/schedule_editor.py`,
normalized `class_meeting`, deferred database conflict checks, and scheduling/import
regressions. Existing text schedules require explicit time review.

Old standalone verification scripts were removed once their behavior was covered
by the PostgreSQL acceptance/role/migration/UI tests. The bundled CSVs remain an
explicitly documented legacy compatibility fixture; the canonical importer and
original-data archive preserve their values.

Verification before final review: 120 tests passed with PostgreSQL 17 enabled,
including all 52 rubric cases and a fresh GUI-process restart. Final review and
any resulting fixes are recorded in the branch history and completion report.
