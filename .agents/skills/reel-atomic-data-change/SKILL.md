---
name: reel-atomic-data-change
description: Diagnose lost updates, duplicate effects or violated invariants in database read-modify-write flows. Use when concurrent requests can mutate the same records; inspect engine-specific isolation before changing transactions.
---

# Protect data invariants under concurrency

State the invariant first: for example, preserving all increments, preventing a negative balance or consuming a token once. Trace the reads, writes, transaction boundaries, retries and external effects under two interleaving requests.

Separate three issues: lost updates on one record, invariants spanning several records, and duplicate external side effects. A transaction is not automatically serializable, and single-statement atomicity does not prove every business invariant.

For a simple database-side increment/decrement, consider a parameterized in-place update rather than reading a value into application code and overwriting it. Add predicates and check affected rows when required by the invariant. For multiple records or more complex decisions, inspect the actual database's locking/isolation semantics and choose suitable constraints, locks, optimistic versions or stronger isolation.

Treat serialization/deadlock retry and request idempotency separately. Bound retries and retry the correct transaction unit only when external side effects are safe. Never blindly repeat payments or messages after an uncertain result.

When code changes are authorized, use disposable data and a meaningful concurrent test that asserts the final invariant and rollback behavior. A sequential happy-path test is insufficient evidence for a race fix. Do not run stress tests or destructive migrations against production.

Return the failing interleaving, chosen mechanism, database/version assumptions, checks and remaining limits. The reel's SQL sketch is evidence of an idea, not a complete transfer/accounting implementation.

## Sources and validation

Our instruction-only synthesis, based on the user-supplied Muse Job collection report; not recovered creator skill files. Muse reported full viewing but disclosed approximate timing, sampled frames and unreadable material. We did not independently inspect the original videos.

- [@jordan_kodes — Race conditions: the read-modify-write bug](https://www.instagram.com/reel/DYfqiZExKh1/) — Muse report entry 35.
- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html) — primary documentation checked for the relevant mechanism.

Checked 2026-10-31. Documentation-supported mechanism; workflow defaults are our design choices. Skill structure validated separately; no project workflow or performance claim has been runtime-verified by creating this file.
