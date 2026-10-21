# Rubric alignment

The current implementation follows the appendix's actual domain relationships:
six shared period components for the acceptance scenario, twelve class/component
weights, and four consolidated saved grades. There is one current grade store.
The earlier category/result-store differences are resolved for new workflows.

See [checklist evidence](checklist_audit.md), [installation/migration](../README.md)
and the [approved design](superpowers/specs/2026-10-21-rubric-database-alignment-design.md).
Original schema/migrations live only in `tests/fixtures/legacy_database` to prove
conversion compatibility. Their SQL is not part of the new installation path.

Python/PySide6/PostgreSQL remain the chosen architecture. The subject's required
Java description is saved exactly as text; this does not claim the application
itself is implemented in Java. A separate language/submission requirement would
need separate assessment. No instructor-awarded score is claimed.
