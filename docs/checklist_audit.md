# CSPC 103 rubric verification

The actual domain model now follows the supplied appendix: shared period
components, per-class component weights and one consolidated grade per enrollment.
The previous class-owned category model, separate period weight/result stores,
legacy grade-save path and redundant student-only import path have been removed
from the active application. Legacy schema fixtures remain for migration tests.

## Automated scenario

`tests/test_checklist_database.py` runs all 52 cases through the real services and
secured account boundary, deferring cases explicitly dependent on later records.
It checks required/duplicate inputs, CRUD persistence, protected deletes, raw score
correction/deletion/re-entry, invalid policy rollback, Midterm-only saves, full
calculation/recalculation, audit before/after values and actual actor attribution.
The real GUI performs student searches, and a second GUI process reads saved
Grade Sheet and Student Grade outputs after the first data session.

`tests/fixtures/rubric_expected.json` describes every final appendix row by its
natural keys. `tests/rubric_comparison.py` compares saved PostgreSQL records,
foreign-key joins, NULL fields, source references, percentages and equivalents.
The acceptance test emits `/tmp/student-rubric-comparison.json` (or the location
selected by `RUBRIC_COMPARISON_PATH`). No school database is preloaded by this test.

| Table | Expected final rows |
| --- | ---: |
| STUDENT | 5 |
| TEACHER | 2 |
| SUBJECT | 2 |
| CLASS | 2 |
| ENROLLMENT | 4 |
| GRADING_PERIOD | 2 |
| GRADE_COMPONENT | 6 |
| GRADE_PERCENTAGE | 12 |
| GRADE_COMPONENT_SCORE | 24 |
| GRADE | 4 |
| AUDIT_LOG | at least 7 |

Grade Sheet checks Juan 2.50/2.25, Ana 1.00/1.25 and Pedro 5.00/5.00, in
last-name order. Juan's two-subject report checks five units and weighted GWA
2.05. The grade-point scale uses unrounded percentages. Actual generated IDs,
actor names and test timestamps are used; instructor example IDs are not faked.

## Additional regression evidence

PostgreSQL tests cover fresh/repeat installation; populated legacy conversion,
archived evidence, account/session preservation and timestamps; exact grouped
weight conversion and blocked incompatible conversions; concurrent student and
enrollment creation; shared component permissions; transactional import;
provenance/actor separation and no-op auditing.

The owner's additional schedule requirement is implemented with selectable days
and AM/PM time controls. Structured meetings reject teacher, room and active
student conflicts within a term, allow back-to-back meetings, and recheck a
Dropped → Enrolled status change. Canonical CSV imports cannot bypass this by
supplying only ambiguous schedule text. Existing ambiguous legacy schedules are
preserved for explicit review rather than guessed.

## Manual demonstration and limits

Run the complete suite with a disposable `CHECKLIST_TEST_DSN` as documented in
README. Without it, PostgreSQL tests intentionally skip; that is not acceptance
evidence. Inspect actual tables with [read-only SQL](rubric_database_checks.sql).

Live mouse/keyboard demonstration, printer selection, physical print output and
instructor database-client inspection still require a human demonstration. These
checks do not claim an instructor-awarded 100/100 or Java-language compliance.
Python, PySide6 and PostgreSQL are retained by the owner's requested architecture.

Set by is implemented as the owner's requested source provenance. The document's
original column explains which cases produced each row; it is not a username.
Signed-in users are recorded separately. Existing archives are outside the
canonical domain counts, and authentication/policy/timetable metadata is not
extra rubric domain data.

Final verification and independent review: [completion evidence](superpowers/reviews/2026-10-21-rubric-alignment.md).
