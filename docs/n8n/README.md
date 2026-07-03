# AI RiskOps GitHub Maintainer

This folder contains the validated n8n workflow export for the AI RiskOps Copilot portfolio.

## Workflows

- Main workflow: `AI RiskOps GitHub Maintainer`
- Error workflow: `AI RiskOps Error Handler`

The main export is stored in `docs/n8n/ai-riskops-github-maintainer.json`. The Error Handler workflow is documented here; no separate safe export is included unless a dedicated JSON file is provided.

Operations runbook: [OPERATIONS.md](OPERATIONS.md)

Local validation script: [`scripts/validate_n8n_workflows.py`](../../scripts/validate_n8n_workflows.py)

## Main Workflow Capabilities

`AI RiskOps GitHub Maintainer` runs a weekly RiskOps automation:

- API health check,
- priority customer retrieval,
- Action Board retrieval,
- recommended action sync when the board is empty,
- anonymized briefing payload creation,
- AI report generation,
- RiskOps Quality Gate validation,
- OpenAI visual snapshot generation,
- GitHub image upload,
- GitHub issue creation,
- Markdown report creation in `docs/reports`,
- final automation summary.

## Enterprise Hardening

The hardened workflow adds:

- retry on external API nodes,
- RiskOps Quality Gate validation before publishing,
- GitHub issue labels for generated issues,
- `AI RiskOps Error Handler` workflow for execution failures,
- GitHub incident issue creation on failure,
- weekly duplicate issue guard,
- safe skip behavior when a weekly issue already exists.

## Weekly Duplicate Guard

Before calling the AI Agent, the workflow searches GitHub for an existing weekly issue with the same report date.

If an issue already exists, the workflow stops safely and returns:

```json
{
  "automation_status": "skipped",
  "reason": "weekly_issue_already_exists"
}
```

In this skipped path:

- no new AI report is generated,
- no new OpenAI image is generated,
- no duplicate GitHub issue is created,
- no unnecessary OpenAI image cost is incurred.

## Error Handling

`AI RiskOps Error Handler` is designed to run from an n8n Error Trigger during real executions.

When the main workflow fails, the Error Handler creates a GitHub incident issue with labels such as:

- `riskops`
- `automation`
- `incident`
- `workflow-failure`

Review incident issues before using this automation in production.

## Required Services

- n8n: `http://localhost:5678`
- FastAPI backend: `http://localhost:8000`
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

## Local Validation

Run the local validation script before committing workflow changes:

```bash
python scripts/validate_n8n_workflows.py
```

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
2. Use a token with the minimum permissions needed to search issues, create issues and upload report/image files.
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
6. If the workflow returns `automation_status: skipped`, confirm a weekly issue already exists for that report date.

## Activate The Schedule Later

The exported workflow keeps the Schedule Trigger disabled for safety.

Activate it only after:

- OpenAI credentials are configured,
- GitHub credentials are configured,
- the RiskOps backend URL is correct,
- manual execution succeeds,
- duplicate guard behavior is reviewed,
- generated issues have been reviewed.

## Generated Outputs

- GitHub issue
- Markdown report in `docs/reports`
- OpenAI generated RiskOps visual image
- GitHub incident issue on failure
- Skip summary when a weekly issue already exists
- Final automation summary

## Security And Privacy Rules

- Never commit real API keys.
- Never commit GitHub tokens.
- Rotate any token accidentally exposed.
- Keep Schedule Trigger disabled until credentials are configured.
- Review generated GitHub issues before using this in production.
- Use anonymized customer aliases only.
- Do not expose raw customer identifiers in reports, images or issue bodies.

## Manual Validation Checklist

- Backend health check returns ok.
- Priority customers are retrieved.
- Action Board is retrieved.
- Weekly duplicate guard is evaluated before AI generation.
- AI report is generated when no duplicate weekly issue exists.
- Quality Gate passes before publishing.
- Image is generated.
- Image is uploaded to GitHub.
- GitHub issue is created with labels.
- Markdown report is created.
- Final Automation Summary returns success.
- Duplicate weekly runs return skipped status.
- No raw customer identifiers are exposed.
