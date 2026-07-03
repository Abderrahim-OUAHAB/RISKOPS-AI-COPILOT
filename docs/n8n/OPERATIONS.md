# n8n Operations Runbook

This runbook explains how to operate the n8n automation layer for AI RiskOps Copilot.

## Workflows

- Main workflow: `AI RiskOps GitHub Maintainer`
- Error workflow: `AI RiskOps Error Handler`

The main workflow creates a weekly RiskOps briefing, GitHub issue, Markdown report and visual snapshot. The error workflow is designed to create an incident issue when the main workflow fails during a real execution.

## Local Development Setup

n8n runs separately from the AI RiskOps app. It is an external automation client that calls the FastAPI backend over HTTP.

Required local services:

- AI RiskOps FastAPI backend
- GitHub repository access
- OpenAI API access
- n8n running at `http://localhost:5678`

Useful URLs:

- n8n: `http://localhost:5678`
- FastAPI: `http://localhost:8000`
- FastAPI docs: `http://localhost:8000/docs`

## Backend URL Choice

Use `http://host.docker.internal:8000` when n8n runs inside Docker and the RiskOps backend is exposed on the host machine.

Use `http://backend:8000` only when n8n is attached to the same Docker network as the RiskOps Compose stack and can resolve the `backend` service name.

Use `http://localhost:8000` only when n8n runs directly on the host machine outside Docker.

## Required Credentials

Configure credentials in n8n or through environment variables:

```env
OPENAI_API_KEY=
GITHUB_TOKEN=
RISKOPS_API_BASE_URL=http://host.docker.internal:8000
GITHUB_OWNER=Abderrahim-OUAHAB
GITHUB_REPO=RISKOPS-AI-COPILOT
```

Do not paste real secrets into exported workflow JSON.

## Manual Run Procedure

1. Start the AI RiskOps backend.
2. Open n8n at `http://localhost:5678`.
3. Import `docs/n8n/ai-riskops-github-maintainer.json`.
4. Configure OpenAI and GitHub credentials.
5. Keep the Schedule Trigger disabled.
6. Click **Execute workflow**.
7. Review the final automation summary.
8. Confirm GitHub issue, image and Markdown report outputs.

## Schedule Activation Procedure

Activate the Schedule Trigger only after:

- manual execution succeeds,
- GitHub issue labels are correct,
- the weekly duplicate guard is verified,
- generated issues have been reviewed,
- token scopes are minimal,
- the team agrees the workflow can run unattended.

## Token Rotation Procedure

1. Revoke the old OpenAI key or GitHub token.
2. Create a new token with minimal permissions.
3. Update the n8n credential or environment variable.
4. Run the workflow manually.
5. Review generated outputs.
6. Delete any accidental exports containing real token values.

If a token is exposed, rotate it immediately and treat the old token as compromised.

## Error Handler Behavior

`AI RiskOps Error Handler` is intended to run from an n8n Error Trigger. During a real execution failure, it creates a GitHub incident issue with labels such as `riskops`, `automation`, `incident` and `workflow-failure`.

Review incident issues before adapting this workflow for production use.

## Duplicate Weekly Issue Guard

The main workflow searches for an existing weekly issue for the report date before invoking the AI Agent.

If a weekly issue already exists, the workflow returns a skipped summary:

```json
{
  "automation_status": "skipped",
  "reason": "weekly_issue_already_exists"
}
```

This prevents duplicate GitHub issues, duplicate reports and unnecessary OpenAI image generation cost.

## Rollback Procedure

1. Disable the Schedule Trigger in n8n.
2. Re-import the previous known-good workflow export from Git.
3. Confirm credentials are still linked correctly.
4. Run the workflow manually.
5. Keep the schedule disabled until manual validation passes.

If the workflow created an unwanted GitHub issue or report, close the issue and revert or remove the generated report file in a follow-up commit.

## Troubleshooting Checklist

- FastAPI `/health` returns ok.
- `RISKOPS_API_BASE_URL` points to the reachable backend URL.
- GitHub token can search issues, create issues and upload files.
- OpenAI credential is linked to the AI and image nodes.
- Schedule Trigger is disabled during testing.
- Weekly duplicate guard is not skipping because of an old issue.
- Quality Gate failure message is reviewed.
- No real secrets are present in exported JSON.
- No raw customer identifiers are present in generated outputs.
