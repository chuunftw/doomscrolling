---
name: reel-independent-review
description: Review a proposed implementation against its specification and project rules without modifying the code. Use when the user requests an independent review or a pre-merge quality check.
---

# Independent implementation review

Start from the user outcome, spec, repository instructions and current diff. Trace the changed behavior and affected callers before accepting the author's explanation. Separate observed facts from guesses.

Remain read-only during this review: do not patch code, rewrite tests, stage changes, merge or approve a pull request. Run only appropriate authorized checks; if a check mutates fixtures, starts external services or uses accounts, establish its scope first.

Build the rubric from the project: correctness, boundary/error cases, data ownership, compatibility, access control where relevant, test quality and unnecessary complexity. Look for a concrete trigger, its consequence and the code location. Do not manufacture findings to fill a quota.

For each material finding, provide severity, path/line, a reproducible scenario and the smallest corrective direction. Distinguish confirmed bugs, untested concerns and design preferences. A green test suite does not establish that omitted scenarios work.

A separate context is useful when actually available: give the reviewer the spec, diff and project rubric, not the implementer's desired verdict. Do not claim a fresh or independent context if reviewing in the same chat. Spawn no agent unless delegation is authorized.

Return findings first, then checks performed and remaining limits. Say when no actionable findings were found. A review verdict is advice, not authorization to merge, and cannot replace required human approvals.

## Sources and validation

Our instruction-only synthesis, based on the user-supplied Muse Job collection report; not recovered creator skill files. Muse reported full viewing but disclosed approximate timing, sampled frames and unreadable material. We did not independently inspect the original videos.

- [@raycfu — Build a dev team with 4 AI agents in Claude](https://www.instagram.com/reel/DZqXF-1vPzg/) — Muse report entry 28.
- [@zazencodes — An AI software factory in Claude Code (SPONSORED)](https://www.instagram.com/reel/Derra61CUhb/) — Muse report entry 12.

Checked 2026-10-31. Workflow advice/opinion adapted to this environment. Skill structure validated separately; no project workflow or performance claim has been runtime-verified by creating this file.
