---
name: reel-spec-first
description: Turn substantial feature or architecture requests into a small implementation spec with explicit acceptance criteria and handoffs. Use for ambiguous or multi-component changes, not trivial edits.
---

# Spec before a substantial change

Read the target repository's instructions, existing behavior and relevant interfaces. Find the unresolved decision that could make a build go wrong; do not create a planning ceremony for a small edit.

Write a short spec at a project-appropriate path. `.pipeline/specs.md` is an optional convention, not a product requirement. Include:
- The user outcome, in scope and out of scope.
- The current behavior and constraints with verified file paths.
- The proposed approach, data/API contracts, failure behavior and compatibility or migration requirements.
- Observable acceptance criteria, including meaningful negative cases.
- A small ordered implementation plan and the checks that would demonstrate success.

Mark assumptions and decisions needing the user. Do not invent function names or claim paths exist without checking. Prefer the existing architecture unless the requirement justifies replacing it.

When implementation is already authorized, resolve routine choices and proceed; ask only for a material missing decision or an action outside authorization. A spec does not authorize sending messages, deployments or merges. Respect requests for planning only.

When handing off work, include the scope, relevant paths, spec version, acceptance criteria and unresolved risks. A file handoff carries evidence; it does not confer permissions. Delegate only when the user or applicable instructions authorize it, using available tools rather than imitating a Claude slash command.

Return the spec path and the important decision it resolves. If no edits were made, say so.

## Sources and validation

Our instruction-only synthesis, based on the user-supplied Muse Job collection report; not recovered creator skill files. Muse reported full viewing but disclosed approximate timing, sampled frames and unreadable material. We did not independently inspect the original videos.

- [@raycfu — Build a dev team with 4 AI agents in Claude](https://www.instagram.com/reel/DZqXF-1vPzg/) — Muse report entry 28.
- [@aidendjohnston — Overnight agent workflows 101](https://www.instagram.com/reel/De0zboJzAlO/) — Muse report entry 9.

Checked 2026-10-31. Workflow advice/opinion adapted to this environment. Skill structure validated separately; no project workflow or performance claim has been runtime-verified by creating this file.
