# Interview Q&A

## Architecture

1. What is AI RiskOps Copilot?
AI RiskOps Copilot is a local AI product that combines documents, customer data, churn prediction, RAG, a controlled agent, data pipelines and monitoring to prioritize business risk.

2. Why is this not just a chatbot?
Because it uses persisted data, vector search, ML scoring, source retrieval, orchestration, monitoring and health checks.

3. Why separate frontend and backend?
Streamlit focuses on demo UX, while FastAPI owns business logic, validation, persistence and API contracts.

## FastAPI

4. Why use FastAPI?
FastAPI gives typed endpoints, Pydantic validation, dependency injection and automatic Swagger docs.

5. How do you handle errors?
Endpoints raise HTTP exceptions with clear status codes, and database errors are rolled back where needed.

6. What are `/health` and `/ready` for?
`/health` checks whether the API and dependencies respond. `/ready` checks whether the app is ready for real traffic or demo use.

## PostgreSQL

7. Why PostgreSQL?
It is realistic for business data, supports SQL analytics and can also host pgvector embeddings.

8. What data is stored?
Customers, documents, document chunks, embeddings and risk predictions.

## pgvector

9. Why pgvector?
It avoids adding another vector database while keeping semantic search inside PostgreSQL.

10. What is stored in pgvector?
Document chunk embeddings used for similarity search in RAG.

## RAG

11. What is the RAG flow?
Upload a document, extract text, chunk it, embed chunks, retrieve similar chunks and answer with sources.

12. Why return sources?
Sources make the answer auditable and reduce blind trust in generated text.

## Embeddings

13. What are embeddings?
Embeddings are numeric vectors that represent semantic meaning and allow similarity search.

14. What happens without an OpenAI key?
RAG embedding and generated answers are unavailable, but customer risk, reports, monitoring and the controlled agent demo still work.

## LlamaIndex

15. Why mention LlamaIndex?
The project is structured for RAG-style indexing and retrieval patterns; the current services keep the implementation simple and inspectable.

## OpenAI API

16. Where is OpenAI used?
OpenAI is used for embeddings and RAG answer generation when an API key is configured.

17. Is the key committed?
No. `.env` is ignored, and `.env.example` only documents variable names.

## XGBoost

18. Why XGBoost?
It is a strong baseline for tabular data and works well for churn-style structured features.

19. What features are used?
Tenure, charges, contract type, support tickets and late payments.

## MLflow

20. Why MLflow?
MLflow tracks experiments, parameters, metrics and artifacts so model training is reproducible.

21. Where is MLflow stored?
In the local `mlruns` directory.

## Airflow

22. Why Airflow?
Airflow shows how the app could run scheduled operational workflows.

23. What does the DAG do?
It checks the API, imports sample customers, runs dbt, trains the model and generates reports.

## dbt

24. Why dbt?
dbt makes SQL transformations testable and organized.

25. What models exist?
Staging, intermediate customer risk features and a mart summary.

## LangGraph

26. Why LangGraph?
LangGraph provides an explicit workflow for routing user questions to known tools.

27. Why keep the agent controlled?
Controlled routing is easier to test, explain and defend than a fully autonomous agent.

## Monitoring

28. What is monitored?
API health, readiness, ML data quality and RAG/agent traces.

29. What is in an LLM trace?
Timestamp, question, selected tool, latency, status, error, source count and document id.

30. What does the ML report check?
Missing values and simple drift on key customer features.

## Docker

31. Why Docker Compose?
It starts PostgreSQL, backend, frontend and Airflow services consistently for demos.

32. What slowed Docker before?
Full uncached builds can be slow because Airflow, dbt, ML and RAG dependencies are heavy.

## GitHub Actions

33. What does CI validate?
Dependency installation, Python compilation, Docker Compose config and key project files.

34. Does CI need OpenAI or Langfuse?
No. CI is designed to run without external secrets.

## Project Limits

35. What are the main limits?
No cloud deployment, no auth, small sample dataset, lightweight monitoring and optional OpenAI for RAG.

36. How would you improve it next?
Deploy on AWS, add auth, add better tests, add RAG evaluation and add alerting.

## Future Improvements

37. How would you make it production-ready?
Use managed Postgres, secret management, observability dashboards, CI integration tests, auth, backups and deployment automation.

38. How would you scale RAG?
Use async processing, stronger indexing, evaluation sets, caching and better document metadata filters.

39. How would you improve the model?
Use more real customer history, feature stores, calibration, backtesting and monitoring alerts.

40. What is the business value?
It helps teams prioritize retention work with explanations and recommended actions.
