---
name: reel-minimal-change
description: Reduce unnecessary implementation complexity while preserving required behavior, tests, security and compatibility. Use for requested simplification, debloating reviews or choices between new abstractions and existing code.
---

# Choose the smallest sufficient change

Identify the required behavior and contracts first. For each proposed addition, consider in order:
1. Is the behavior already implemented and suitable for reuse?
2. Can a standard library or platform feature satisfy the contract?
3. Can an existing dependency do it without a disproportionate cost?
4. Can the design be made smaller without obscuring behavior?
5. If none fits, add the smallest new code or dependency that does.

Stop at the first suitable option, not merely the first option that exists. Reuse must fit semantics, maintenance, supported versions and security. Removing duplication can increase complexity if it forces unrelated behavior into a shared abstraction.

Do not add speculative extension points, generic frameworks or future-facing configuration without an actual requirement. Do not optimize for line count: preserve validation, authorization, error handling, readability and compatibility.

For a review-only request, give concrete simplifications and their tradeoffs without editing. When edits are authorized, change one coherent concern and verify the affected behavior with existing meaningful checks. Avoid tests that simply mirror implementation details.

Report what became simpler and what behavior was checked. The decision ladder is our adaptation of an idea described in Muse's report, not the Ponytail plugin, its hooks or its gated instructions. Do not install that plugin or copy its marketing claims into results.

## Sources and validation

Our instruction-only synthesis, based on the user-supplied Muse Job collection report; not recovered creator skill files. Muse reported full viewing but disclosed approximate timing, sampled frames and unreadable material. We did not independently inspect the original videos.

- [@philofsurprises — One AGENTS.md snippet worth stealing: YAGNI](https://www.instagram.com/reel/De5zE3RKjLs/) — Muse report entry 6.
- [@youraveragetechbro — The skills that keep agent code from bloating (10x AI-Native Developer, Ep. 5 of 7)](https://www.instagram.com/reel/DePGBFXtswr/) — Muse report entry 13.
- [@codenameposhan — Ponytail: the Claude Code plugin that makes AI write less code](https://www.instagram.com/reel/DdDRVU1hlqp/) — Muse report entry 21.

Checked 2026-10-31. Workflow advice/opinion adapted to this environment. Skill structure validated separately; no project workflow or performance claim has been runtime-verified by creating this file.
