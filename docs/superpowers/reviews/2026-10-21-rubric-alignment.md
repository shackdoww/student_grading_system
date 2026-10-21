# Rubric alignment completion and review

The work modifies the existing `shackdoww/student_grading_system` checkout,
starting from main commit `6242e25`, on local branch
`feat/rubric-database-alignment`. No replacement application or GitHub repository
was created. This report records the local verification and review completed before publication.

## Verification

Final suite: **126 passed** on Python 3.12/PySide6 6.10.3/PostgreSQL 17 with
`CHECKLIST_TEST_DSN` enabled. All 52 rubric cases ran, with zero discrepancies in
the saved-row comparison and a second-process GUI persistence check. Actual
counts: 5 students, 2 teachers, 2 subjects, 2 classes, 4 enrollments, 2 periods,
6 components, 12 weights, 24 scores and 4 grades; 87 audit entries (minimum 7).

Compilation, whitespace checks and undefined-name/duplicate-definition checks
passed. The real installer CLI completed fresh preflight, install and repeated
install in another disposable database. The selectable class editor was also
rendered offscreen and visually inspected.

## Independent review and verified fixes

One fresh reviewer examined the full branch and independently ran 34 targeted
checks. It reported four Important issues and no Critical issues. Every finding
was reproduced by a failing regression before correction:

| Finding | Regression coverage | Resolution |
| --- | --- | --- |
| Concurrent assignment removal and score insertion could leave an orphan score | `test_assignment_removal_cannot_race_a_score_insert`; `test_older_serializable_policy_snapshot_cannot_remove_new_score_assignment` | Score writes serialize on the assignment's MVCC version, including an older serializable policy snapshot; no-op audit/provenance stays unchanged |
| Duplicate CSV primary keys silently overwrote earlier input rows | `test_duplicate_csv_primary_keys_are_rejected_without_overwriting` | Reject duplicate input keys before importing |
| Imported displayed schedule omitted retained old meetings | `test_import_replaces_meeting_set_and_display_together`, with and without a class row | Supplied meetings replace that class's complete meeting set atomically, and display is derived from the resulting set |
| Explicit blanks could not clear existing nullable values | `test_import_can_clear_previously_supplied_optional_values` | Supplied blank optional fields become SQL NULL; omitted fields remain unchanged |

Targeted regression checks and the full suite passed after this single fix pass.
No Minor findings were deferred. Physical printing, the live demonstration,
external school databases and production-scale performance were not judged.

## Implementation decisions

- Work in the existing disposable cloud clone on a feature branch: keeps the
  user's main checkout/history unchanged. If a separate worktree is preferred,
  only branch placement needs to change.
- Preserve existing component identities during migration instead of guessing
  equivalence from names. The fresh rubric scenario shares six definitions;
  existing duplicate definitions need an explicit reviewed mapping to merge.
- Check schedule conflicts by teacher, room and active enrolled student within a
  term. Reused section labels do not identify a cohort; cohort-wide planning
  would require an explicit cohort identifier.
- Preserve ambiguous legacy schedule text for explicit time review, and archive
  old percentage-only grades when period data is unavailable. Users must confirm
  those schedules/configurations and recompute rather than accept invented data.
- No external school database was upgraded. GitHub publication is a separate
  repository operation authorized by the owner after local verification.
