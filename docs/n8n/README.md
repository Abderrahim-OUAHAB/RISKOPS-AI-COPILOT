# AI RiskOps GitHub Maintainer

This folder contains the validated n8n workflow export for the AI RiskOps Copilot portfolio.

## What The Workflow Does

`AI RiskOps GitHub Maintainer` runs a weekly RiskOps automation:

- checks the RiskOps API health,
- retrieves priority customers,
- checks the Action Board,
- syncs recommended actions when the board is empty,
- builds an anonymized RiskOps briefing payload,
- uses an AI Agent to generate a RiskOps report,
- normalizes the report,
- generates an OpenAI RiskOps visual snapshot,
- uploads the image to GitHub,
- injects the image into the Markdown report and GitHub issue body,
- creates a GitHub issue,
- creates a Markdown report in `docs/reports`,
- returns a final automation summary.

## Required Services

- n8n: `http://localhost:5678`
- FastAPI: `http://localhost:8000`
- FastAPI docs: `http://localhost:8000/docs`
- GitHub repository access
- OpenAI API access

## Required Credentials

Use n8n credentials or environment variables. Never store real secrets in the workflow JSON.

```env
OPENAI_API_KEY=
GITHUB_TOKEN=
RISKOPS_API_BASE_URL=http://host.docker.internal:8000
GITHUB_OWNER=Abderrahim-OUAHAB
GITHUB_REPO=RISKOPS-AI-COPILOT
```

## Required RiskOps API Endpoints

- `GET /health`
- `GET /risk/priority-customers`
- `GET /actions/board`
- `POST /actions/sync`

## Import Into n8n

1. Open n8n at `http://localhost:5678`.
2. Go to **Workflows**.
3. Click **Import from File**.
4. Select `docs/n8n/ai-riskops-github-maintainer.json`.
5. Keep the Schedule Trigger disabled until credentials are configured.
6. Save the workflow.

## Configure OpenAI

1. Create or select an OpenAI credential in n8n.
2. Use the `OPENAI_API_KEY` value from your local secret store.
3. Confirm the AI Agent and image generation nodes use that credential.
4. Do not paste real keys into exported workflow JSON.

## Configure GitHub

1. Create or select a GitHub credential in n8n.
2. Use a token with the minimum permissions needed to create issues and upload report/image files.
3. Use the `GITHUB_TOKEN` value from your local secret store.
4. Confirm owner and repository values:

```env
GITHUB_OWNER=Abderrahim-OUAHAB
GITHUB_REPO=RISKOPS-AI-COPILOT
```

## Run Manually

1. Ensure the RiskOps backend is running at `http://localhost:8000`.
2. Open the workflow in n8n.
3. Click **Execute workflow**.
4. Review the final automation summary.
5. Verify the generated GitHub issue, Markdown report and image.

## Activate The Schedule Later

The exported workflow keeps the Schedule Trigger disabled for safety.

Activate it only after:

- OpenAI credentials are configured,
- GitHub credentials are configured,
- the RiskOps backend URL is correct,
- manual execution succeeds,
- generated issues have been reviewed.

## Generated Outputs

- GitHub issue
- Markdown report in `docs/reports`
- OpenAI generated RiskOps visual image
- Final automation summary

## Security And Privacy Rules

- Never commit real API keys.
- Never commit GitHub tokens.
- Rotate any token accidentally exposed.
- Keep Schedule Trigger disabled until credentials are configured.
- Review generated GitHub issues before using this in production.
- Use anonymized customer aliases only.
- Do not expose raw customer IDs in reports, images or issue bodies.

## Manual Validation Checklist

- Backend health check returns ok.
- Priority customers are retrieved.
- Action Board is retrieved.
- AI report is generated.
- Image is generated.
- Image is uploaded to GitHub.
- GitHub issue is created.
- Markdown report is created.
- Final Automation Summary returns success.
- No CUST-* identifiers are exposed.
