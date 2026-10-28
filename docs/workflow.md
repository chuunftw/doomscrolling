# From Saved ideas to an approved plan

The Muse adapter is one possible source reader. GPT/Codex still owns evidence review, verification, relevance decisions and the implementation plan. Work in a separate run folder. Do not copy account/session credentials, payment details, unrelated messages, or secret configuration into reports.

## 1. Collect only the approved sources

Start with the explicit original link. For a later Saved run, agree the collection bound and account first, corroborate creator metadata, and exclude the user's own posts by default. The current Muse adapter only supports one explicit source per request; it does not yet implement bulk Saved collection. Use an authorized export or a separately reviewed collector for that phase. Keep uncertain creators for inspection instead of bypassing own-post exclusion.

Show obvious non-technique/irrelevant items with a short reason. Only mark those as skipped after the user agrees. Preserve source links and metadata so later runs can merge new items rather than losing earlier work.

## 2. Read speech and visual evidence

Record exactly what Muse actually accessed. Read captions/transcripts and inspect every full-size frame/slide with code, prompts, commands, URLs or settings. Short samples and screenshots can miss brief text. Say what could not be heard/read, preserve timestamps, and keep original media where the user chose to retain it. Do not fill missing code from memory or label a caption-only account as a complete reel review.

The fixed Muse task asks for these distinctions; it cannot enforce Muse's perception or remote actions. If Muse cannot access the full content, obtain a separate authorized acquisition method or mark the source incomplete.

## 3. Classify and merge

Write one note per source: URL, creator, accessed modalities, source timestamps/frames, readable code/prompts, named tools and versions, attributed claims, sponsorship evidence and uncertainty. Classify useful actionable techniques as `keep`, essential comment/DM/signup/payment gates as `teaser`, and non-actionable content as `fluff`. Do not send comments/DMs to obtain gated content. Optional gated extras do not automatically invalidate an otherwise usable technique.

Merge duplicates by concrete mechanism and outcome, keep the best supported details, and note disagreements. Popularity does not verify a claim. A reel can contain several distinct techniques.

## 4. Verify without confusing folders and isolation

Consult current official docs or maintainer repositories for every kept technique, including ideas intended for other projects or a future library. Record URLs, checked dates and supported/contradicted claims. Attribute opinions and performance promises.

Before running a technique, inspect actual code, dependencies and side effects. Use only reviewed suitable code under genuinely enforced restrictions: a disposable VM/container or a verified execution boundary with no credentials, limited writes, restricted network, time/resource limits and no unintended host/project access. A working folder, virtual environment, snapshot, browser profile or this adapter's flags do not enforce security isolation. Do not weaken restrictions or elevate just to pass a test. When adequate constraints are unavailable, perform docs/code review and state it was not run.

Use `verified` only with an observed test result, command/output, input, versions, environment and scope. Otherwise use `docs-match`, `outdated`, `wrong`, `opinion`, or `unclear` as supported. Stand-in data verifies only the stated test.

## 5. Fit the actual user projects

Inspect only selected, relevant projects and authorized settings. Read manifests/lockfiles, README, applicable `AGENTS.md`, skills, relevant Codex configuration/hooks, tests/CI and recent commits. Redact secrets. Do not discover unrelated chat histories, home folders or credential stores. Verify Codex feature support before translating a Claude-specific hook or setting.

Assign each technique to current project (`yes`), existing implementation (`already`), a relevant other project (`elsewhere`), future reference (`library`), a user decision (`ask`), or rejected (`no`). Do not discard a sound idea solely because it does not fit today's repository.

## 6. Rank and seek implementation approval

Present normally 3–7 justified priorities, fewer for one source when appropriate. Each includes the actual proposed change, why it fits, effort/impact, evidence/testing limits and original links. Include short sections for other projects/library/already implemented, disputed claims and gated teasers. Do not pad the plan.

Wait for explicit item approval before changing project code, skills, settings or hooks. Read account access, source collection, plan approval and implementation approval are different scopes. Verify approved changes with meaningful tests and a review of the resulting files. Retain useful unapproved ideas as notes; do not install global skills or delete recordings automatically.
