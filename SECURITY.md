# Security Policy

## Supported Version

The supported portfolio version is the latest tagged demo release.

## Security Model for Demo

AI RiskOps Copilot is a portfolio and local demo system. It is not production
enterprise-ready without additional controls such as authentication,
authorization, managed secrets, network controls, audit logging, malware
scanning, and formal compliance review.

## Secrets Handling

Secrets must be stored in `.env` or in the runtime environment. `.env` is
ignored by Git and must never be committed. The repository only includes
`.env.example` with placeholder values.

## File Upload Limitations

The demo API accepts document uploads for supported file types only and applies
a configurable upload size limit. This is a basic demo safeguard, not a full
content security system. Production usage should add MIME validation, malware
scanning, quarantine storage, tenant isolation, and object storage policies.

## RAG and LLM Risks

RAG answers can be incomplete or incorrect if the retrieved sources are weak,
outdated, or irrelevant. Uploaded documents can also contain prompt-injection
content. Do not treat generated answers as authoritative without human review.

## Data Privacy Warning

Do not upload real customer data, confidential contracts, payment data, personal
data, or regulated information into the demo environment. Local traces and
reports may contain user questions or extracted document content.

## Known Limitations

- No user authentication or role-based access control.
- No enterprise audit log.
- No malware scanning for uploaded files.
- No PII redaction.
- No production-grade rate limiting backend.
- No cloud secrets manager.
- No formal RAG or ML safety evaluation.

## Responsible Use

Use this project with synthetic data or demo-safe samples only. Review all AI
outputs before using them in any business decision.

## Contact

For security questions, replace this placeholder with the project maintainer
contact before public enterprise use.
