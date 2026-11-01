---
name: reel-parallel-work-boundaries
description: Plan code and environment isolation for explicitly authorized parallel development. Use when tasks may share worktrees, databases, ports, migrations or mutable test state.
---

# Separate code changes from shared runtime state

First determine whether work can be divided into independent tasks. If parallel execution has not been authorized, give the proposed split and shared-state risks without spawning workers or starting services.

For each authorized task, define ownership of files/contracts, its base revision, allowed operations, acceptance checks and integration order. Reuse a suitable existing checkout or app-managed worktree when appropriate; do not discard user changes.

A Git worktree provides a separate working tree while sharing repository metadata. It is not an execution sandbox. Inventory the other collision points: database/schema, services and ports, queues, caches, storage, migration history and account credentials.

Where tasks mutate shared state, provide separate disposable resources or serialize that work. A VM or container helps only if the relevant state is actually separated and its network, mounts and credentials are appropriate; cloud branding alone does not prove isolation. Do not start paid resources or duplicate production data merely because a reel recommends cloud agents.

Use short evidence handoffs: changed paths, tests, contract changes and unresolved dependencies. Integrate in an order that checks shared contracts, not just whether patches apply. Respect resource and usage budgets; no claim of unlimited parallelism.

Return the boundary map, conflicts, chosen isolation or serialization, and integration checks. Preserve work until its result is safely retained; use the app's managed worktree lifecycle when available.

## Sources and validation

Our instruction-only synthesis, based on the user-supplied Muse Job collection report; not recovered creator skill files. Muse reported full viewing but disclosed approximate timing, sampled frames and unreadable material. We did not independently inspect the original videos.

- [@aidendjohnston — Overnight agent workflows 101](https://www.instagram.com/reel/De0zboJzAlO/) — Muse report entry 9.
- [@youraveragetechbro — Cloud coding agents beat git worktrees for parallel work (10x AI-Native Developer, Ep. 3 of 7)](https://www.instagram.com/reel/Dd4EU7ORjOK/) — Muse report entry 17.
- [@nuhushaik — 3 levels of Claude Code](https://www.instagram.com/reel/DZl3mvzxSfL/) — Muse report entry 29.
- [Git worktree manual](https://git-scm.com/docs/git-worktree) — primary documentation checked for the relevant mechanism.

Checked 2026-10-31. Documentation-supported mechanism; workflow defaults are our design choices. Skill structure validated separately; no project workflow or performance claim has been runtime-verified by creating this file.
