# Accounts and roles

Install or migrate with `python -m app.database.apply_migration --all`. Existing accounts, sessions and security events are preserved during conversion. Use `--preflight` first on existing databases.

Start the application with `python main.py`. If no accounts exist, the local
setup screen creates the first Admin. Choose your own username, name and a
15–128 character passphrase. There are no default passwords, seeded production
accounts, or passwords in source control. Do not send passwords through chat.
After setup, every application launch requires sign-in.

| Role | Access |
| --- | --- |
| Admin | All school workflows, account management, import and permanent deletion |
| College Dean | School-wide reports and shared academic/grading configuration; no score entry, account management or deletion |
| Teacher | Reports, scores, component assignments and weights for assigned classes; shared component definitions are Admin/Dean only |
| Registrar | School-wide reports, student records and enrollment; no grading changes or deletion |

Teacher accounts require an existing teacher record. Admins create accounts,
enable/disable access, and change roles from Accounts. Role changes and disabling
revoke existing sessions. The last active Admin cannot be disabled/demoted,
and Admins cannot disable themselves or change their own role. Another Admin
must change that role. Disabled accounts and audit events are retained.

## Security behavior and limits

Passwords are salted and hashed with scrypt using N=16384, r=8, p=5. Passwords
are not stored as plaintext. Sessions expire after eight hours. Five failed
attempts lock an account for 15 minutes. Credential errors do not distinguish
unknown usernames from incorrect passwords. Account listings exclude hashes.

Application-boundary service proxies validate the session and role before
writes. Teacher writes check both the current owner and proposed destination
when updating configuration. Teacher read snapshots are filtered before reaching
the interface. The UI also disables unavailable actions. Session invalidation
is enforced immediately for writes and on the next data refresh for visible
records. The permission policy denies actions not explicitly listed.

This is local desktop access control, not a security boundary against someone
who controls the computer or knows the shared PostgreSQL credentials. Protect
`.env` and database privileges. For untrusted multi-user deployment, put these
workflows behind an authenticated server/API and use least-privilege database
roles. MFA, account recovery/password reset, and centralized session monitoring
are not implemented in this version.

Sources: [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
and [OWASP authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).

## Manual deletion through the app

Only Admins see Data Records. Select a record type and check the rows to remove.
Select all checks every record in the current dataset (including off-screen
rows); Clear selection unchecks them. The counter shows the selected total.
Selections survive refreshes, but never carry over to a different dataset.
Choose Delete selected records permanently to review the count, record IDs,
and full list under Show Details. Confirmation defaults to No.
No backup is made and there is no undo. Each deletion is audited in the same
transaction. A batch is all-or-nothing: a missing record, dependency or database
error rolls back the whole batch, including its audit entries. Dependencies
block deletion; the app never automatically cascades away raw academic evidence.

To clear school records, delete saved grades, then raw scores and enrollments.
Remove class policies (which remove their component weight assignments), then
unused components, classes, periods, subjects and teachers/students. Teacher
records linked to accounts remain protected. Accounts, sessions and security
events are intentionally excluded from school-record cleanup.

Set by stores optional source references, separate from actual actor identities.
Ordinary writes and batch deletions consistently attribute audit events to the
signed-in username. Unknown historic actors are not invented during migration.

## Verification

Run `python -m pytest -q`; set `QT_QPA_PLATFORM=offscreen` for headless Qt. Set
`CHECKLIST_TEST_DSN` to a disposable PostgreSQL database to include actual account
bootstrap/login, Teacher permissions, provenance, protected deletion and rollback
checks. These tests never use the configured school's schema. UI helpers provide
explicit fake authentication only inside `tests/`; startup uses real accounts.
