# doomscrolling

A restricted Muse companion for turning Instagram ideas into an evidence-backed plan with GPT/Codex. This is our own local derivative of [nikships/muse-cli](https://github.com/nikships/muse-cli), not an official Meta client. Upstream attribution and exact reviewed source blob IDs are in [LICENSE](LICENSE) and [UPSTREAM.json](UPSTREAM.json).

**Current milestone:** offline-tested request preparation, a restricted CLI/MCP adapter, and Windows encrypted session storage. Nothing here has been connected to a real Muse account or used to view Instagram. Live dependency installation, session use, or dispatch needs separate authorization.

## What changed

- The default CLI and MCP modes prepare or inspect a single source-review request without network or credentials.
- The only gateway routes are Muse identity, session metadata, bounded history of one chosen session, and the fixed single-source review prompt when separately enabled.
- No raw API escape hatch, permission/approval endpoints, credential-management routes, chat/file deletion, generic free-form send, browser control, cookie export, self-update, installer script, or automatic file downloads.
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
| Default | `--run-dir` | `prepare_reel_request`, `inspect_reel_request` |
| Explicit account reads | add `--vault`, `--allow-network`, `--allow-session-use` | above plus `muse_status`, `muse_sessions`, `muse_history` |
| Explicit remote task | additionally `--allow-muse-task` | above plus `dispatch_reel_request`, requiring the reviewed digest |

There is no credential-entry MCP tool. Account-read mode does not expose dispatch. Flags and a digest do not constitute human permission themselves; the operator/agent must first obtain the user's actual approval for that exact account operation. Approval of code review or repository edits is not account authorization.

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

## Remaining limits

- Live Muse authentication, gateway compatibility, task acceptance, account identity, Instagram access and actual audio/frame understanding have not been tested. The private upstream protocol can change without notice.
- No video capture, Whisper transcription, image download or arbitrary file writing from Muse responses is implemented here. Keep the previous local capture pipeline available where needed; don't silently fall back to it or claim a caption summary is a full analysis.
- The HTTP auth requests use fixed Muse endpoints and reject redirects. The WebSocket uses a fixed gateway host and TLS verification. Upstream-derived timeouts and bounded responses do not provide OS resource isolation, an absolute end-to-end deadline, or cancellation of remote work.
- Responses/history may contain private information or malicious instructions. Do not execute text returned by Muse. No automatic transcript/history dump is committed. Local request/receipt folders and encrypted credentials are ignored by Git.
- No website, model, plugin, GitHub automation or account operation is deployed by installing/importing this source. Future actions still require the appropriate user authorization.
