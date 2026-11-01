---
name: reel-auth-boundary-review
description: Review an application login, session, password-reset or authorization flow against its actual threat model. Use for an explicitly requested auth review or a material auth change; report evidence before proposing fixes.
---

# Review the actual authentication boundaries

Trace login, session issuance/storage, logout, reset and server authorization through the selected code. Identify the auth provider and deployed assumptions. Use current provider documentation and OWASP guidance rather than a universal copy-paste fix prompt.

Check where tokens are exposed and how the chosen architecture mitigates XSS, CSRF, session theft and expiry. JavaScript-readable session secrets deserve scrutiny; cookie-based designs also need appropriate flags and CSRF defenses. Do not claim that one storage choice eliminates XSS or universally fits native, SPA and server-rendered applications.

Verify that protected actions enforce authorization on the server. A hidden admin button is not access control. Check recovery/token expiry and reuse, abuse limits on login/reset, and error behavior that may disclose accounts.

Distinguish MFA, email ownership verification and identity proofing: they address different risks. For password-based systems, prefer current length and breached-password guidance over arbitrary uppercase/number/symbol composition rules. Assess the provider's policy rather than weakening it without evidence.

Return observed issues with the triggering scenario, impact, code location and a scoped remediation proposal. Mark missing evidence; do not certify an app as secure from this checklist. Use synthetic test data; do not attack production endpoints, read real credentials or change permissions as part of a review.

This skill is our corrected review workflow, not the creator's gated fix prompts. Implement changes only when the user requested fixes or approves the concrete proposals.

## Sources and validation

Our instruction-only synthesis, based on the user-supplied Muse Job collection report; not recovered creator skill files. Muse reported full viewing but disclosed approximate timing, sampled frames and unreadable material. We did not independently inspect the original videos.

- [@haydenschmitty — 5 ways your vibecoded login endpoint isn't secure](https://www.instagram.com/reel/DZsXW-HonCi/) — Muse report entry 27.
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html) — primary documentation checked for the relevant mechanism.

Checked 2026-10-31. Documentation-supported mechanism; workflow defaults are our design choices. Skill structure validated separately; no project workflow or performance claim has been runtime-verified by creating this file.
