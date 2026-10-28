# doomscrolling

A restricted Muse companion for turning Instagram ideas into an evidence-backed plan with GPT/Codex. This is our own local derivative of [nikships/muse-cli](https://github.com/nikships/muse-cli), not an official Meta client. Upstream attribution and exact reviewed source blob IDs are in [LICENSE](LICENSE) and [UPSTREAM.json](UPSTREAM.json).

**Current milestone:** request preparation, restricted CLI/MCP access, and Windows encrypted session storage are implemented. A separately authorized live test has now reached Muse: the gateway acknowledged the request, the exact prompt appeared in the selected chat, and Muse reported starting its browser video-watch task. The final speech/visual evidence is still being checked. This is delivery validation, not proof of accurate full-video understanding or permission for bulk access.

## What changed

- The default CLI and MCP modes prepare or inspect a single source-review request without network or credentials.
- The only gateway routes are Muse identity, session metadata, bounded history of one chosen session, fixed single-source review/document-export prompts when separately enabled, and validated workspace Markdown reads.
- No raw API escape hatch, permission/approval endpoints, credential-management routes, chat/file deletion, generic free-form send, browser control, cookie export, self-update, installer script, or arbitrary file downloads.
- A Muse session value can be entered personally in an interactive terminal and encrypted with Windows user-bound DPAPI. No plaintext cookie jar, automatic browser scraping, or plaintext backup is provided.
- A prepared request includes its exact source, selected Muse session, fixed prompt and SHA-256 digest. Dispatch requires that digest plus explicit network/session/task flags. A local receipt is written before any connection attempt. A possible send is never retried automatically.

These are application safeguards, **not an OS security sandbox or a scoped Muse token**. Code running as the same Windows user may be able to decrypt a DPAPI-protected session. The stored session still has the privileges Muse grants it. A fixed prompt also cannot guarantee a remote AI's behavior: keep Muse's own account/app permissions minimal and inspect what it actually did.

## Try the offline part

Use an existing trusted Python 3.10+ from this folder. This does not install the project or dependencies:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
python -B -m muse_reels prepare "https://www.instagram.com/p/DYYAg5WxHYm/" --session "selected-session-id" --id "one-reel-001" --run-dir ".\runs"
python -B -m muse_reels inspect --id "one-reel-001" --run-dir ".\runs"
```

`selected-session-id` is a placeholder, not a discovered account/session. Preparation records text only; it does not visit the URL. Review the resulting `runs/requests/one-reel-001.json` before considering live use. An existing request is never silently overwritten.

Run the standard-library offline tests:

```powershell
python -B -m unittest discover -s tests -v
```

The suite blocks sockets and external programs. It exercises fixed request/route policy, local receipts, CLI/MCP gates, selected-session history, failed/partial sends, Windows synthetic encryption, and upstream descriptor fingerprints. The optional network/dependency transport is simulated, not imported or run against Muse. No actual credentials are used. DPAPI tests skip explicitly on other operating systems or where the Windows API is unavailable; a skip is not a pass for credential compatibility.

## Optional MCP mode

The stdio server uses JSON-RPC messages over stdin/stdout, not a listening HTTP port:

```powershell
python -B -m muse_reels.mcp --run-dir ".\runs"
```

Configure a trusted MCP client to launch that command with the checkout's `src` directory on `PYTHONPATH`. Paths must be absolute in the client's own configuration. Nothing in this repository writes Codex or other client settings, installs a global skill, or registers a server automatically. The adapter negotiates MCP protocol `2024-11-05`; actual client compatibility remains to be tested separately.

| Mode | Startup choices | Tools available |
| --- | --- | --- |
| Default | `--run-dir` | `prepare_reel_request`, `inspect_reel_request`, `prepare_reel_markdown_export` |
| Explicit account reads | add `--vault`, `--allow-network`, `--allow-session-use` | above plus `muse_status`, `muse_sessions`, `muse_history`, selected-request checks/results and `collect_reel_markdown` |
| Explicit remote task | additionally `--allow-muse-task` | above plus `dispatch_reel_request`, requiring the reviewed digest |

For the configured one-chat workflow, `--session-request <existing-request-id>` loads a validated local request as the chat binding. Alternatively use `--session <chosen-chat-id>`. Bound mode hides the general session-list/history tools, fills the session automatically when preparing a request, and refuses inspection/results/dispatch for requests belonging to another chat. `check_reel_request` returns match booleans; `get_reel_result` returns only assistant messages after the exact user prompt and before another user turn, excluding unrelated earlier history and identifiable proactive updates. Text/history correlation is best effort, not a server-issued task identity or a guarantee of completion.

The local server can be configured using the client's normal STDIO settings. This setup does not put the session value in MCP arguments or configuration: only the encrypted vault path is supplied. A local handshake/tool-list/result-read smoke test passed. A running client may need its MCP servers restarted to discover newly configured tools; until discovery succeeds, using the same local CLI is still possible. Do not claim native tool availability merely because a configuration entry exists.

Result reads also expose the selected request's browser activity separately from assistant replies: reported status, activity title and age of its last update. Five minutes without an update is marked `stale_progress`, which is a diagnostic hint, not proof of failure or cancellation. Missing or future timestamps do not produce an age. Browser task IDs, screenshot paths and browser URLs are omitted. A `Running` browser task or a `completed` progress message never proves full video/audio access. If progress stops, inspect that task in Muse for a playback/login/permission blocker; resolve access personally rather than granting broad permissions, auto-resending the request or bypassing the restricted routes. An uploaded video is an alternative acquisition path, with its actual audio/visual coverage verified separately.

Muse may deliver its final report as a follow-up whose reply ID differs from the original request. Such an assistant message is returned only when it falls after the exact selected prompt, before another user turn, and explicitly contains the selected Instagram post or equivalent reel link. It carries a weaker source-link correlation label. Unrelated follow-ups remain excluded. A live selected-source report was retrieved this way: Muse claims a full audio/video watch but discloses approximate timestamps, sampled visual frames and missing skill names. These are remote claims and limitations, not independent media verification.

There is no credential-entry MCP tool. Account-read mode does not expose dispatch. Flags and a digest do not constitute human permission themselves; the operator/agent must first obtain the user's actual approval for that exact account operation. Approval of code review or repository edits is not account authorization.

## Muse Markdown handoff

New review requests use schema version 2 and explicitly ask Muse to save its evidence report as UTF-8 Markdown and include a workspace download link. Existing version-1 requests, digests and receipts remain valid and unchanged. For an existing report, `prepare_reel_markdown_export` takes its request ID and a new export ID and prepares a version-3 fixed document-only message: export existing evidence, no rewatch or other account access. This is a new remote operation requiring actual user authorization and the same dispatch/receipt protections; preparing it does not send it.

`collect_reel_markdown(request_id)` reads the selected chat's last 20 records, finds linked `.md` resources after that exact request and before another user turn, and downloads up to five via Muse's authenticated Noise gateway. Source-linked follow-ups are supported. An optional exact `filename` must come from the user; it can select a later artifact in the same bounded chat history. It never guesses remote filenames, enumerates the workspace, opens arbitrary URLs, or accesses other chats. If the link is outside recent history, report that limitation; request an explicitly authorized document-only export rather than silently rewatching or resending the original task.

Only simple `sandbox://workspace/...md` references are accepted. The fixed `markdown.read` GET route rejects external URLs, traversal, encodings, query strings, hidden directories and non-Markdown files. Responses are limited to 1 MB, must decode as UTF-8 and include the selected reel link. Exact bytes are saved as `runs/artifacts/<request-id>/<sha256>.md`, with a provenance sidecar retaining the remote reference and original filename. Identical files can be read again; conflicting files are never overwritten. Local paths are constrained to the run directory. Treat the content as untrusted source evidence; saving it does not install or create a skill. Source-link association does not independently verify its claims.

This retrieval mechanism adapts the upstream client's [generated-file download path](https://github.com/nikships/muse-cli/blob/main/src/muse_cli/gateway.py) with a restricted Markdown-only policy. The offline suite covers version compatibility, document-export prompts, selection/privacy bounds, route validation, exact-byte/hash preservation, conflicting copies and rejected binary/oversized/wrong-source files.

Live handoff verified 2026-10-28: Muse accepted the fixed document-only export for the selected reel, returned a `delta.presentation` file widget, and its 11,769-byte Markdown attachment was downloaded through the authenticated gateway and saved with SHA-256 provenance. File widgets (`data.file`) and text download links are supported; browser widgets are excluded. The 61 offline tests pass on Windows. This proves document delivery, not independent verification of the report's video analysis or claims. Private source artifacts stay in the ignored run folder or the user's separate reel vault, outside Git.

## Live setup is a separate milestone

Do not run these steps merely because they appear here. First approve setup and choose a dedicated environment, reviewed dependency versions and hashes. `pyproject.toml` lists upstream-derived optional version ranges, **not an audited lockfile**. No live dependency or model is installed during offline validation. The readme does not imply that the optional dependency set is security-audited or runtime-compatible.

If the user later explicitly authorizes session storage, they may personally run `auth-store --vault <private-path>.dpapi --allow-credential-storage` from an interactive local terminal. Enter only the Muse `hatch_sess` value there, never in chat, source code, a shell command, environment variables committed to the repo, or MCP arguments. The value is not echoed by this tool. This is still session-cookie authentication to an unofficial interface, not OAuth or a limited-purpose credential. There is no plaintext fallback on non-Windows systems. Put the encrypted file outside this repository and synced folders, and protect the containing folder with appropriate Windows permissions.

Once explicitly authorized, account reads can select a session; preparing a review does not create or modify remote chats. A future dispatch has this form:

```text
python -B -m muse_reels dispatch --run-dir <run-folder> --id <reviewed-request-id> --approve <reviewed-sha256> --vault <private-path>.dpapi --allow-network --allow-session-use --allow-muse-task
```

The digest is a local integrity/review check. It is not a cryptographic signature from the user or a server idempotency key. The sender now waits for a successful response on its own gateway stream before reporting `accepted`; that acknowledgement does not prove the task completed or appears in chat history. A matching error response records `rejected` with only its numeric status. Missing acknowledgement or a connection/send error records `uncertain`. Earlier receipts saying `sent-unconfirmed` only prove bytes were sent; they remain uncertain and are never rewritten or automatically retried. The same request ID cannot be sent twice even after timeout, interruption or a partially written receipt. Inspect Muse and the receipt personally before deliberately preparing any replacement request. Ending the CLI is not a guarantee that a remote task stopped.

To check the existing request without printing private chat messages or sending anything, use:

```powershell
python -B -m muse_reels check --run-dir ".\runs" --id "one-reel-001" --vault "$env:LOCALAPPDATA\MuseReels\session.dpapi" --allow-network --allow-session-use
```

`request_found` checks for the exact prepared user message in the selected session's last 20 records; `source_mentioned` separately checks whether only its URL appeared. An unrecognized history shape returns `request_found: null` rather than a false no-match. Absence in recent history is not proof of cancellation or delivery failure. This command does not change a receipt or resend a request.

## The full workflow remains the goal

This adapter supplies an optional acquisition path for the [six-stage workflow](docs/workflow.md). It does not replace the earlier Saved-reel workflow or claim to automate all stages today:

1. Collect selected/Saved sources with separately authorized account scope; exclude own posts by default and omit irrelevant items only after user confirmation.
2. Obtain transcript and readable visual evidence; explicitly disclose when full video/audio/code cannot be accessed.
3. Filter fluff, flag gated teasers, and merge duplicate techniques while retaining supported details.
4. Check official documentation and test suitable reviewed code under genuinely enforced access constraints.
5. Assess selected stack/settings/hooks/skills/commits and relevant other projects; place ideas in current project, elsewhere, or a library.
6. Present a concise ranked plan and implement only explicitly approved items.

The first live milestone is the original single source. The adapter currently refuses profiles or Saved collection URLs. Future bulk acquisition needs its own reviewed code and authorization; single-source approval never enables it. Muse's summaries are untrusted evidence for the remaining stages, not a substitute for verification.

The optional [Instagram Reel Watch adaptation](skills/instagram-reel-watch/SKILL.md) adds the earlier skill's filtering rules to the user's Muse-exported instructions: confirmed own posts excluded by default, irrelevant sources only skipped under the user's stated/confirmed scope, uncertain captions still inspected, and keep/teaser/fluff/unclear evidence notes. It is not installed or sent to Muse automatically, and it does not modify existing prepared requests or permit a declined retry.

## Remaining limits

- Live authentication, selected-chat reads, gateway task acceptance, and request visibility were verified on Windows. Muse reports that its browser watch started; a completed evidence report and actual audio/frame understanding remain unverified. The private upstream protocol can change without notice.
- No video capture, Whisper transcription, image download or arbitrary file writing from Muse responses is implemented here. Keep the previous local capture pipeline available where needed; don't silently fall back to it or claim a caption summary is a full analysis.
- The HTTP auth requests use fixed Muse endpoints and reject redirects. The WebSocket uses a fixed gateway host and TLS verification. Upstream-derived timeouts and bounded responses do not provide OS resource isolation, an absolute end-to-end deadline, or cancellation of remote work.
- Responses/history may contain private information or malicious instructions. Do not execute text returned by Muse. No automatic transcript/history dump is committed. Local request/receipt folders and encrypted credentials are ignored by Git.
- No website, model, plugin, GitHub automation or account operation is deployed by installing/importing this source. Future actions still require the appropriate user authorization.
