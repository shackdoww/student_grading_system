# Rubric database alignment design

Date: 2026-10-21
Status: Approved by the owner on 2026-10-21; implementation planning in progress.
Baseline: GitHub main, 6242e258c8725c4eb2706a68d158d36ced129d6e.
Source: CSPC 103 Finals Project — CRUD Test Case Scenarios (100 pts), including its final-table appendix.

## Goal and agreed scope

Make the existing application implement the rubric's database relationships, final records, validation, reports, persistence and audit evidence. Preserve Python, PySide6, PostgreSQL, the GUI/service/repository separation, accounts, role restrictions, background work, exports, printing and protected batch deletion. No application rewrite and no automatic insertion of demonstration records into a user's school database.

The owner explicitly requests both test-case provenance (Set by) and attribution to the signed-in actor. These are separate: ST-01 is a source reference, not a username. Real actor names and timestamps must never be invented to resemble the appendix.

## Approach and alternatives

Recommended: migrate to physical rubric-shaped domain tables and update their consumers. Shared components and per-class component weights become the actual persistence model, and consolidated grades are saved in GRADE. This addresses the relationship and row-count differences directly.

Rejected: expose rubric-shaped views over the old category model. Views can make inspection easier but do not satisfy the requested underlying table contents or remove the conflicting ownership relationships.

Rejected: create a separate rubric demonstration application/database path. That risks keeping two incompatible implementations and makes the live demonstration unrepresentative of normal workflows.

## Canonical schema

Use unquoted lowercase singular PostgreSQL table names corresponding to the document's uppercase labels. CLASS is `class`; case is PostgreSQL identifier normalization. Foreign keys use `class_id`, not `offering_id`, and grade percentages reference components directly. Additional account, policy and migration metadata tables are permitted; the rubric's row counts apply to its listed domain tables.

| Table | Required domain columns | Fresh acceptance count |
| --- | --- | ---: |
| student | student_id, first_name, last_name, email, program, year_level, status | 5 |
| teacher | teacher_id, first_name, last_name, email, department, status | 2 |
| subject | subject_id, subject_code, subject_name, description, units | 2 |
| class | class_id, class_code, subject_id, teacher_id, section, school_year, semester, schedule, room | 2 |
| enrollment | enrollment_id, student_id, class_id, enroll_date, status | 4 |
| grading_period | period_id, name, period_order, start_date, end_date, school_year, semester | 2 |
| grade_component | component_id, period_id, name, type, max_score, description | 6 |
| grade_percentage | percentage_id, class_id, component_id, percentage | 12 |
| grade_component_score | score_id, enrollment_id, component_id, score, remarks, date_recorded | 24 |
| grade | grade_id, enrollment_id, midterm_grade, finals_grade, overall_grade, midterm_equiv, final_equiv, remarks, date_encoded | 4 |
| audit_log | log_id, table_name, record_id, action, old_value, new_value, changed_by, changed_at | >=7 |

Retain `finals_equiv` on grade as an additional field because the scenarios require conversion of Finals as well as Midterm and Overall. `final_equiv` remains the Overall equivalent used for FG/F Grade. Persist overall period weights and selected periods in a grading_policy linked to class; there is no second result store or category weight store.

The document explicitly permits different surrogate ID values. Existing IDs remain valid; new internal IDs are generated, with unique constraints enforced by PostgreSQL. Student numbers and teacher IDs remain user-facing identifiers. No requirement to recreate deleted numeric ID gaps artificially.

## Provenance and actors

Add `set_by`, `created_by`, `updated_by`, `created_at` and `updated_at` to domain records. Set by stores source references supplied for actual operations; actor columns derive from the authenticated session. A source/reference input is available in relevant create/edit, score, enrollment and policy workflows, and imports accept provenance. It is optional for ordinary usage, validated when supplied, and never interpreted as executable text.

For rubric demonstrations use the relevant ST/TE/SU/CL/EN/GP/GC/GW/SC/GR/PS reference or Report setup. Set by retains ordered unique references across updates, so Ana's row can expose ST-01; ST-05. No production behavior hard-codes those records or assumes a particular test case from a person's name. Acceptance tests pass references explicitly, using the same service contracts as the GUI.

Audit triggers capture before/after values, operation, source reference, signed-in username and timestamp. Deletion logs survive record deletion. Unchanged writes do not produce false grade changes. Actor representation is consistent across ordinary writes, batch deletion and imports. Historical provenance and actor values stay unknown unless evidence exists; a migration actor identifies the conversion itself, not past school activity.

## Shared components, weights and authorization

Components belong to a grading period and can be reused across classes. A grade_percentage is a unique class/component assignment. Both classes reuse the same six components. A score is valid only if its enrollment's class has the component assigned, and the component's period matches the class term.

Policy editing saves all assignments and weights for a period/class atomically. Each configured period totals exactly 100, and overall weights total exactly 100. Reject blank, nonfinite, nonpositive and out-of-range weights. Database constraints/triggers also enforce valid persisted configurations at transaction completion, while allowing complete configuration creation in one transaction. Empty unconfigured classes may exist; partial policies cannot be used for grading.

Admin and Dean manage the shared component definitions. Teachers retain score entry, grade saving and policy changes for assigned classes. Teachers can assign existing shared components and change their own class weights, but cannot edit a shared definition affecting another teacher. This is necessary to preserve the existing ownership protections after components become shared.

Component changes that would invalidate existing scores, period assignments or term alignment are rejected. Parent deletions use restrictive foreign keys and existing confirmation/audit workflows. Score-bearing components, enrolled students/classes, used subjects/teachers and scored enrollments remain protected.

## Grade calculation and persistence

For each selected period, sum `(score / max_score * 100) * (component weight / 100)`. Overall uses configured Midterm/Finals weights, 40/60 for this fixture. Use Decimal calculations and the central existing grade-point scale. Convert the unrounded percentage, then round percentages for persistence/display. Missing scores mean Incomplete, never implicit zero.

Use one unique grade row per enrollment, updated on recomputation. The normal Save Grades action writes this canonical row. Remove duplicate legacy-save behavior from the active UI after migration; preserve old evidence in the archive. Midterm-only computation may save a partial grade record with unavailable Finals/Overall fields null; reports cannot treat it as a complete result. Completed results match the appendix.

Reports read canonical saved grades, compare them with current score/configuration calculations, and continue showing Not saved, Incomplete or Recompute required as appropriate. Preserve last-name sorting, exact headings, term scope and units-weighted GWA. Grade-point thresholds remain centralized.

## Migration and existing data

Introduce a versioned, transactional migration path that supports both a fresh schema and an existing migration-004 database. Prior migrations must not rerun old SQL against the new schema. Reapplying the installer/migrator must be safe.

Before conversion, produce a preflight inventory and copy original domain tables and mapping evidence to an explicitly named legacy archive schema in the same database. Keep existing audit and account records. A failed conversion rolls back canonical changes and reports the record IDs requiring attention. No resets, destructive cascades or automatic replacement with rubric sample rows.

Map existing classes/enrollments directly. Convert category/period configuration to class/component weights only where the old equal-category-average formula can be represented exactly and existing grades/grade-point boundaries remain equivalent. Ambiguous or nonrepresentable grouped-category conversions stop with an actionable preflight report rather than silently changing results. Do not merge components merely because names match; preserve identities unless an explicit mapping proves period, definition, assignments and score evidence compatible.

Existing consolidated period results map into grade, preserving enrollment links and timestamps. Historic legacy percentage grades remain in the archive when they cannot provide rubric-required period data; mark their active enrollments as needing recomputation instead of inventing missing values. Ordinary fresh rubric workflows require no archive or special mode.

Retain import support through an updated canonical format, with documented validation/conversion of the older bundled format. Optional emails become null, nonfinite numbers return validation messages, and imports preserve provenance, atomicity and parameter binding. Update the bundled data documentation so it no longer claims old-model outputs are rubric-equivalent.

## UI and repository changes

Update academic editors, class component assignment/policy setup, score component selection, snapshots, report lookups, permission scopes, deletion dependencies and CSV import together. Components no longer ask for a class-owned percentage parent. Weight editors identify class and component, with period inferred and displayed. Expose provenance and actor information read-only in record inspection/data tables, and source reference on writes. Keep reports' required column layouts unchanged.

Repository SQL uses explicit column lists and bound parameters. Replace tuple-offset assumptions affected by new relationships with named results or stable adapters where necessary. No parallel old/new persistence implementations in active workflows.

The owner also authorizes removing functions superseded by this model. Remove the old consolidated-percentage calculator methods, GradingService/GradeRepository legacy persistence, Save Legacy Grade handler, redundant category-weight/result snapshot branches and their obsolete verification paths after replacement coverage passes. Keep the central grade-point scale and the current period calculator, updating its inputs. Old migrations remain historical inputs to the conversion tests; they are not active installation steps on the canonical schema. Do not remove unrelated accounts, permissions, imports, exports, printing, animations or protected batch deletion merely because the appendix does not list them.

## Acceptance evidence

Create an isolated PostgreSQL schema/database and execute all 52 cases in their dependency order, deferring the cases that explicitly say Run after a later case. Use the actual services and relevant PySide6 editors. Start with no school records. Do not implement a production seed button that bypasses the workflows.

Assert every appendix record, count, relationship, null, field update and absent record. Verify rejected cases leave database state unchanged, including audit entries where transactions roll back. Verify component sharing, independent weights for both classes, duplicate/concurrent inserts, direct SQL constraint enforcement, protected deletion, teacher isolation and provenance/actor separation.

Final fixture assertions:

- Students: Juan, Pedro, Ana (now BSCS), Carlo (kept without enrollment), Kevin O'Brien; no Lea.
- Teachers: Maria (Information Technology Department), Jose (Physical Education Department).
- CSPC 103: three units and the Java description; PATHFIT 3: two units.
- CSPC class: TTh 1:00–2:30, CS-202; PATHFIT: TTh 3:00–5:00, Gym; section A, 1st Semester, SY 2026-2027.
- Enrollments: Juan/Pedro/Ana in CSPC, Juan in PATHFIT; all Enrolled.
- Six shared components: Mid Quiz 50, Mid Lab 100, Mid Exam 100; Final Quiz 50, Final Lab 100, Final Exam 100.
- CSPC final weights: Midterm 30/30/40; Finals 20/30/50. PATHFIT: 20/30/50 in each period.
- CSPC scores: Juan 40/90/75/45/85/80; Pedro 20/60/55/30/70/65; Ana 50/100/100/48/95/92. PATHFIT Juan: 45/90/90/45/90/90.
- Final percentages (Midterm/Finals/Overall): Juan 81/83.50/82.50; Pedro 52/65.50/60.10; Ana 100/93.70/96.22; PATHFIT Juan 90/90/90.
- Midterm/Finals/Overall equivalents: Juan 2.50/2.25/2.25; Pedro 5/5/5; Ana 1/1.50/1.25; PATHFIT Juan 1.75/1.75/1.75.
- At least the seven documented correction/deletion/reinsertion/weight/recalculation audit events, with the actual actor and time.
- Grade Sheet: Juan 2.50/2.25, Ana 1/1.25, Pedro 5/5; Juan Student Grade: five units, two subjects, GWA 2.05.

Restart a second application process and verify the same saved reports. Verify source references and signed-in actors in PostgreSQL and the record inspection UI. Run the existing suite after adapting assertions intentionally tied to the old model. Add migration tests for empty, populated, repeat-run and blocked ambiguous conversions. Export a machine-readable expected-versus-actual table comparison and document remaining manual printer/live-demonstration checks.

## Boundaries and completion

The rubric is an acceptance scenario, not a requirement that every user's live database always contains exactly these counts. Counts are asserted after that specific fresh-database scenario. Accounts/security/policy metadata and an optional legacy archive do not represent extra rubric domain records.

The appendix's Set by narrative is implemented as requested provenance, not a claim that the instructor explicitly required such a physical column. Exact surrogate ID values are not an acceptance condition because the document expressly permits differences. Manual demonstration and physical printer checks cannot be claimed from automated tests alone.

Implementation is complete only after PostgreSQL-backed acceptance, migration, authorization and GUI regression checks pass and the repository documentation reflects the final schema and commands. No push or modification of an external school database is included without a further instruction.
