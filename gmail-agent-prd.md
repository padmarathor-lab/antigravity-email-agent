# PRD: Gmail Customer Query Triage & Draft Agent

## 1. Overview

An automated agent that monitors a business Gmail inbox, identifies genuine customer queries (as opposed to newsletters, receipts, internal mail, automated notifications, etc.), and drafts replies based strictly on a curated set of knowledge documents stored in Google Drive. The agent never sends email — it only creates Gmail drafts for human review. If no answer exists in the knowledge base, the agent flags the email for manual handling instead of guessing.

## 2. Goals

- Reduce time spent by the team triaging and drafting replies to repetitive customer queries.
- Ensure all customer-facing replies are grounded only in approved knowledge documents — no hallucinated answers.
- Keep the existing Gmail workflow unchanged for the team (drafts appear normally in threads).
- Keep infrastructure and cost minimal (no new apps, databases, or dashboards).

## 3. Non-Goals

- No automatic sending of emails.
- No new UI, dashboard, or database.
- No support for non-English emails (out of scope for v1).
- No handling of attachments in incoming emails (out of scope for v1).

## 4. Architecture Summary

- **Runtime**: GitHub Actions scheduled workflow, running hourly (cron).
- **Auth**: OAuth 2.0 with stored refresh token (GitHub Secrets) for both Gmail and Google Drive — consumer @gmail.com account, so no service account.
- **State tracking**: Gmail labels only. No external database.
- **LLM provider**: Groq free tier, two-stage (cheap triage model, then a stronger drafting model).
- **Knowledge base**: Up to 10 PDF/DOCX files in a single Google Drive folder, all text-based (no OCR needed).

## 5. Detailed Workflow

### 5.1 Trigger
- GitHub Actions cron job runs every hour.
- Each run is stateless; all state is derived from Gmail labels at run start.

### 5.2 Fetch candidate messages
1. Query Gmail for messages in the inbox that:
   - Do **not** have the `Agent-Processed` label (applied at the **message** level, not thread level).
   - Are **incoming** (not sent by the account owner).
2. For each candidate message, check the thread:
   - If any message in the thread sent **after** this message is from the account owner (i.e., a human has already replied), apply `Agent-Processed` to this message and skip — no further action.
   - If a draft already exists on the thread, apply `Agent-Processed` to this message and skip.

### 5.3 Stage 1 — Cheap Triage (Groq, cheap/fast model)
- Input: email subject + body text (full body, not just headers/sender).
- Task: classify as `CUSTOMER_QUERY` or `NOT_QUERY` (newsletters, receipts, automated notifications, internal mail, spam, out-of-office, etc.).
- If `NOT_QUERY`:
  - Apply `Agent-Processed` to the message.
  - Stop processing this message.
- If `CUSTOMER_QUERY`:
  - Proceed to Stage 2.

### 5.4 Knowledge Base Loading
- On each run, list files in the configured Google Drive folder.
- For each file, compare `modifiedTime` against a cached manifest (`knowledge/manifest.json`, committed to repo).
- If a file is new or `modifiedTime` changed: download and extract text (PDF and DOCX), update cached extracted text (`knowledge/extracted/<file_id>.txt`) and manifest.
- If unchanged: reuse cached extracted text.
- Commit updated cache files back to the repo as part of the workflow run if changes occurred.

### 5.5 Stage 2 — Drafting (Groq, stronger model)
- Input: full email thread context (customer's message + any prior thread history) + concatenated knowledge base text (or relevant excerpts if context size requires trimming).
- Task: Determine whether the knowledge base contains sufficient information to answer the query.
  - **If yes**: Generate a reply draft, grounded only in the knowledge documents. Append the placeholder signature block (see Section 6).
  - **If no** (answer not found, or only partially found): Do **not** generate a draft. Return a "no answer found" result.
- Binary outcome only — no partial drafts for partially-covered questions in v1.

### 5.6 Actions Based on Stage 2 Result

**If draft generated:**
1. Create a Gmail draft as a reply within the original thread (proper `In-Reply-To` / `References` headers so it threads correctly).
2. Apply `Agent-Processed` label to the message.

**If no answer found:**
1. Apply `Agent-Processed` label to the message (so it's not reprocessed).
2. Apply `Needs-Human` label to the message.
3. No draft is created.

### 5.7 Daily Digest
- Once per day (e.g., the first run after midnight, or a separate daily cron schedule), send a summary email to the account owner containing:
  - Count of messages processed in the last 24 hours.
  - Count of drafts created.
  - Count of messages flagged `Needs-Human`.
  - Count of messages skipped as `NOT_QUERY`.
  - Any errors encountered during runs (e.g., Groq rate limit hits, parsing failures).

## 6. Draft Format

- Drafts are created as Gmail draft replies within the existing thread.
- Each draft ends with a placeholder signature block:
  ```
  [SIGNATURE_PLACEHOLDER — to be replaced with team's standard sign-off]
  ```
- The drafting model should match a professional, helpful tone consistent with customer support correspondence.

## 7. Labels Used

| Label | Applied to | Meaning |
|---|---|---|
| `Agent-Processed` | Individual messages | This message has been evaluated; do not reprocess. |
| `Needs-Human` | Individual messages | Customer query identified, but no answer found in knowledge base — requires manual handling. |

## 8. Error Handling & Resilience

- Groq API failures (rate limits, timeouts): retry with exponential backoff (e.g., 3 attempts). If all attempts fail for a given message, leave it unlabeled so it's retried on the next hourly run; log the failure for the daily digest.
- `Agent-Processed` is applied **immediately** after the determining action (skip, draft creation, or flag) completes successfully — never before — to avoid double-processing on crash/partial-run.
- Knowledge base extraction failures for a given file: log and skip that file for this run, continue with remaining files; do not block message processing entirely.

## 9. Configuration

Stored as GitHub Secrets / repo config:
- `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_REFRESH_TOKEN`
- `GROQ_API_KEY`
- `KNOWLEDGE_DRIVE_FOLDER_ID`
- `DIGEST_RECIPIENT_EMAIL` (defaults to account owner)
- Label names (`Agent-Processed`, `Needs-Human`) — configurable constants.

## 10. Operational Risks & Notes

- **OAuth app verification status**: If the Google Cloud OAuth consent screen is in "Testing" mode, refresh tokens expire after 7 days. The app must be moved to "Production" (or use an internal/unverified-but-published configuration appropriate for personal use) to ensure the refresh token remains valid long-term.
- **Groq free tier limits**: Rate limits (requests/minute, tokens/day) are subject to change by Groq. At ~10-20 emails/day with 2 LLM calls each, expected usage is low, but retry/backoff logic mitigates transient failures.
- **Knowledge base size**: Up to 10 documents — full-text concatenation into the drafting prompt is assumed feasible at this scale, given typical context window sizes. If documents grow significantly, a retrieval step (chunking + relevance filtering) would become necessary — out of scope for v1.
- **Message-level labeling**: Gmail API supports applying labels to individual messages within a thread, enabling the message-level tracking required here.

## 11. Future Considerations (Out of Scope for v1)

- Multi-language support.
- Handling of email attachments as part of query context.
- Partial-answer drafts with explicit caveats.
- Retrieval-augmented knowledge base for larger document sets.
- Pre-filtering via headers to reduce LLM triage calls (deferred — triage handles all classification for now).
