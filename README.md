# Antigravity Email Agent

An autonomous, stateless email triage agent powered by Groq (LLaMA 3) and the Google APIs.
The agent reads unread emails, compares them against a synchronized Knowledge Base folder on Google Drive, and drafts completely grounded replies as native Gmail drafts. It will skip non-queries and flag queries it cannot safely answer with `Needs-Human`.

## Setup Instructions

### 1. Google Cloud Console
1. Create a Google Cloud Project.
2. Enable the **Gmail API** and **Google Drive API**.
3. Configure the OAuth Consent Screen.
4. Create **OAuth 2.0 Client IDs** (Desktop application). 
5. Download the credentials and extract the `client_id` and `client_secret`.
6. Use a local script (like Google's OAuth playground or standard oauthlib flow) to authenticate your Google Account and obtain a `refresh_token`.

### 2. Groq API
1. Create an account on [Groq Cloud](https://console.groq.com).
2. Generate an API Key.

### 3. GitHub Repository Secrets
To run the automated GitHub Actions workflow, add the following secrets to your repository settings (`Settings > Secrets and variables > Actions`):

- `GOOGLE_OAUTH_CLIENT_ID`: The Client ID from Google Cloud.
- `GOOGLE_OAUTH_CLIENT_SECRET`: The Client Secret from Google Cloud.
- `GOOGLE_OAUTH_REFRESH_TOKEN`: The generated offline refresh token.
- `GROQ_API_KEY`: The API key from Groq.
- `KNOWLEDGE_DRIVE_FOLDER_ID`: The ID of the Google Drive folder containing your knowledge base `.txt`, `.pdf`, or `.docx` files (found in the URL when viewing the folder).
- `DIGEST_RECIPIENT_EMAIL`: (Optional) The email address to receive daily stats digests.

### 4. Gmail Labels
The agent automatically creates and assigns the following labels:
- `Agent-Processed`: Applied to every email the agent touches so it isn't processed twice.
- `Needs-Human`: Applied when the LLM determines the Knowledge Base does not contain enough information to draft a response safely.

### 5. Running the Agent
The agent is completely stateless and runs autonomously every hour via GitHub Actions (`.github/workflows/triage-agent.yml`). It persists its execution stats and synced knowledge base documents to the `knowledge/` directory of the `main` branch.
