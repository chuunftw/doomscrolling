---
name: reel-capped-browser-eval
description: Validate an authorized web UI change through user-visible scenarios and a bounded fix-and-retest loop. Use for browser-based regression checks, not unrelated backend changes or unsupervised production actions.
---

# A bounded UI evaluation loop

Read the repository's existing test setup and acceptance criteria. Use its current harness when suitable; choose Playwright for a new suite only when it fits and setup is authorized. Do not install several competing harnesses from a reel's tool list.

Before running, identify the target environment, test account/data, allowed interactions, cleanup and a time or iteration budget. Our default proposal is at most three fix-and-retest cycles for a small local change; use a user-specified budget instead. No scheduled or overnight run is implied.

Exercise the user-visible outcome, meaningful error paths and relevant boundary cases. Prefer resilient role/text locators, observable assertions and isolated test data. Use the harness's waiting/assertion facilities rather than arbitrary delays. Capture a trace or screenshot when it helps explain a failure; do not collect credentials or unrelated personal content.

For each failure, distinguish application bug, invalid expectation, fixture/environment issue and flaky timing. Fix only the authorized cause. Never weaken an acceptance criterion, delete a failing test or increase retries simply to obtain green results.

After a fix, rerun the failing scenario and the relevant regression checks. Stop when criteria pass, the agreed budget is exhausted, progress repeats without a new hypothesis, or an access boundary blocks testing. Preserve the failure and report the next decision; do not silently restart the budget.

Return observed scenarios, results, environment, fixes, artifacts and gaps. A screenshot is not proof of behavior outside the captured state, and passing tests do not authorize deployment or merge.

## Sources and validation

Our instruction-only synthesis, based on the user-supplied Muse Job collection report; not recovered creator skill files. Muse reported full viewing but disclosed approximate timing, sampled frames and unreadable material. We did not independently inspect the original videos.

- [@youraveragetechbro — Verification skills: merge code without reading it (10x AI-Native Developer, Ep. 1 of 7)](https://www.instagram.com/reel/Ddjc3znxnqj/) — Muse report entry 19.
- [@raycfu — Build a dev team with 4 AI agents in Claude](https://www.instagram.com/reel/DZqXF-1vPzg/) — Muse report entry 28.
- [@leo.taps — Loops: how Claude Code's creator works now](https://www.instagram.com/reel/DZV6tWfvYa9/) — Muse report entry 31.
- [@aidendjohnston — My solo-founder AI stack (engineering, design, testing, content)](https://www.instagram.com/reel/DeLhVyuT8G9/) — Muse report entry 14.
- [Playwright best practices](https://playwright.dev/docs/best-practices) — primary documentation checked for the relevant mechanism.

Checked 2026-10-31. Documentation-supported mechanism; workflow defaults are our design choices. Skill structure validated separately; no project workflow or performance claim has been runtime-verified by creating this file.
