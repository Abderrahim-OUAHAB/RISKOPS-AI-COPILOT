# AI RiskOps Copilot - Code Walkthrough

Ce document sert de guide technique pour comprendre le projet AI RiskOps Copilot V1 portfolio. Il explique quoi lire, dans quel ordre, comment les flux fonctionnent, quelles technologies sont utilisées et comment lancer la demo.

## Vue Globale

AI RiskOps Copilot est une application IA locale qui aide a prioriser les risques clients. Le projet combine une interface Streamlit, une API FastAPI, PostgreSQL, pgvector, un flux RAG, un modele XGBoost, un agent LangGraph controle, Airflow, dbt, MLflow et une couche monitoring.

La phrase mentale a garder :

> Streamlit pose des questions a FastAPI. FastAPI lit PostgreSQL, traite les documents, appelle le modele ML, route l'agent, genere des rapports et expose le monitoring.

## Architecture Mentale

1. L'utilisateur interagit avec `frontend/app.py`.
2. Streamlit appelle les endpoints FastAPI.
3. FastAPI demarre dans `backend/app/main.py`.
4. Les routes API vivent dans `backend/app/api/`.
5. Les routes appellent la logique metier dans `backend/app/services/`.
6. Les donnees sont representees par les modeles SQLAlchemy dans `backend/app/models/`.
7. Les entrees/sorties API sont validees par Pydantic dans `backend/app/schemas/`.
8. PostgreSQL stocke clients, documents, chunks et predictions.
9. pgvector stocke les embeddings des chunks.
10. Airflow et dbt orchestrent et transforment les donnees.
11. Le monitoring produit un rapport HTML ML et des traces JSONL pour les appels RAG/agent.

## Structure Des Dossiers

- `backend/` : application FastAPI.
- `backend/app/api/` : endpoints REST.
- `backend/app/services/` : logique metier, RAG, ML, agent, monitoring.
- `backend/app/models/` : tables SQLAlchemy.
- `backend/app/schemas/` : schemas Pydantic.
- `backend/app/db/` : connexion DB et initialisation.
- `backend/app/core/` : configuration et logging.
- `frontend/` : dashboard Streamlit.
- `data/sample/` : CSV de demo.
- `data/raw/` : fichiers PDF/CSV uploades, ignore sauf `.gitkeep`.
- `data/processed/` : sorties pipeline, ignore sauf `.gitkeep`.
- `ml/training/` : script d'entrainement churn.
- `ml/models/` : artefacts modele necessaires a la demo.
- `mlruns/` : experiment tracking MLflow local, ignore par Git.
- `pipelines/airflow/` : image Airflow et DAG.
- `pipelines/dbt/` : projet dbt et modeles SQL.
- `pipelines/scripts/` : scripts utilises par Airflow.
- `monitoring/evidently/` : script de generation du rapport monitoring ML.
- `monitoring/logs/` : traces LLM JSONL, ignore sauf `.gitkeep`.
- `monitoring/reports/` : rapport HTML monitoring ML, ignore sauf `.gitkeep`.
- `scripts/dev/` : scripts de lancement, healthcheck et demo seed.
- `docs/` : documentation portfolio, entretien, architecture et walkthrough.

## Role Des Fichiers Importants

### Racine

- `docker-compose.yml` : lance `postgres`, `backend`, `frontend`, `airflow-webserver`, `airflow-scheduler`.
- `README.md` : presentation GitHub du projet.
- `.github/workflows/ci.yml` : CI GitHub Actions.
- `scripts/init-db.sql` : initialise PostgreSQL avec pgvector.

### Backend

- `backend/app/main.py` : cree l'app FastAPI, initialise la DB et enregistre les routers.
- `backend/app/core/config.py` : centralise les variables de configuration.
- `backend/app/core/logging_config.py` : configure les logs.
- `backend/app/db/session.py` : cree l'engine SQLAlchemy et les sessions.
- `backend/app/db/init_db.py` : cree les tables et l'extension `vector`.
- `backend/app/models/customer.py` : table `customers`.
- `backend/app/models/document.py` : tables `documents` et `document_chunks`.
- `backend/app/models/risk_prediction.py` : table `risk_predictions`.

### Routes API

- `backend/app/api/health.py` : `/health` et `/ready`.
- `backend/app/api/documents.py` : upload, listing et processing documents.
- `backend/app/api/rag.py` : question RAG.
- `backend/app/api/customers.py` : import et lecture clients.
- `backend/app/api/risk.py` : prediction, analyse, priorisation et historique.
- `backend/app/api/reports.py` : rapport hebdomadaire.
- `backend/app/api/agent.py` : agent LangGraph.
- `backend/app/api/monitoring.py` : endpoints MLOps et LLMOps.

### Services Backend

- `file_storage.py` : nettoie le nom de fichier et sauvegarde l'upload dans `data/raw`.
- `text_extraction.py` : extrait le texte des PDF et CSV.
- `chunking.py` : decoupe le texte en chunks via `SentenceSplitter`.
- `embedding_service.py` : appelle OpenAI pour embeddings et generation de reponse.
- `rag_service.py` : process document, stocke chunks, recherche vectorielle, reponse RAG.
- `customer_import_service.py` : lit le CSV client et upsert les clients.
- `feature_engineering.py` : transforme les clients en features ML.
- `model_service.py` : charge le modele XGBoost et predit le churn.
- `risk_scoring_service.py` : transforme churn + signaux business en Risk Score.
- `recommendation_service.py` : genere les actions recommandees.
- `report_service.py` : priorise les clients et cree le rapport weekly-risk.
- `riskops_agent.py` : route les questions avec LangGraph.
- `ml_monitoring_service.py` : genere le rapport HTML de data quality/drift.
- `llm_observability_service.py` : ecrit et resume les traces JSONL.

### Frontend

- `frontend/app.py` : une page Streamlit avec sections upload, RAG, ML, RiskOps, pipeline et monitoring.

### Pipelines

- `pipelines/airflow/dags/riskops_daily_pipeline.py` : DAG Airflow.
- `pipelines/scripts/import_sample_customers.py` : import client via API.
- `pipelines/scripts/run_dbt.py` : lance dbt.
- `pipelines/scripts/generate_pipeline_summary.py` : genere un resume pipeline.
- `pipelines/dbt/riskops_dbt/models/staging/stg_customers.sql` : nettoyage source.
- `pipelines/dbt/riskops_dbt/models/intermediate/int_customer_risk_features.sql` : features analytiques.
- `pipelines/dbt/riskops_dbt/models/marts/mart_customer_risk_summary.sql` : table mart.

### Scripts Dev

- `scripts/dev/start.ps1` : build/start Docker, attend les services, affiche les URLs.
- `scripts/dev/healthcheck.ps1` : teste health, ready, Streamlit et Airflow.
- `scripts/dev/demo-seed.ps1` : lance `demo_seed.py`.
- `scripts/dev/demo_seed.py` : prepare une demo complete.
- `scripts/dev/stop.ps1` : arrete les conteneurs.
- `scripts/dev/reset.ps1` : supprime conteneurs et volume PostgreSQL avec confirmation.
- Les `.sh` sont les equivalents Bash.

## Workflow Utilisateur

1. L'utilisateur ouvre Streamlit.
2. Il importe des clients ou documents.
3. Streamlit appelle FastAPI avec `requests`.
4. FastAPI valide la requete avec Pydantic.
5. Les services backend executent la logique.
6. SQLAlchemy lit/ecrit PostgreSQL.
7. La reponse JSON revient a Streamlit.
8. Streamlit affiche tableaux, scores, rapports et monitoring.

## Flux Streamlit Vers FastAPI

`frontend/app.py` utilise `API_URL`, par defaut `http://backend:8000` dans Docker. Chaque bouton appelle un endpoint :

- upload document -> `POST /documents/upload`
- process document -> `POST /documents/{document_id}/process`
- question RAG -> `POST /rag/ask`
- import clients -> `POST /customers/import`
- prediction -> `POST /risk/predict`
- analyse client -> `POST /risk/analyze-customer`
- agent -> `POST /agent/analyze`
- monitoring -> `/monitoring/...`

## Flux Upload Document

1. Streamlit envoie un PDF ou CSV a `POST /documents/upload`.
2. `documents.py` verifie l'extension.
3. `file_storage.py` sauvegarde le fichier dans `data/raw`.
4. Une ligne `Document` est creee dans PostgreSQL.
5. Le document a le statut `uploaded`.
6. `POST /documents/{document_id}/process` lance l'extraction et le RAG indexing.

## Flux RAG

1. `process_document` lit le fichier source.
2. `text_extraction.py` extrait le texte.
3. `chunking.py` decoupe le texte.
4. `embedding_service.py` cree les embeddings OpenAI.
5. `rag_service.py` stocke les chunks dans `document_chunks` avec pgvector.
6. `POST /rag/ask` cree l'embedding de la question.
7. PostgreSQL/pgvector retrouve les chunks similaires.
8. OpenAI genere une reponse basee sur les chunks.
9. La reponse contient les sources.
10. `llm_observability_service.py` trace l'appel.

Sans cle OpenAI, les endpoints RAG retournent une erreur controlee ou une indisponibilite claire.

## Flux Import Clients

1. `POST /customers/import` recoit un CSV.
2. `customer_import_service.py` verifie les colonnes obligatoires.
3. Les colonnes numeriques sont converties.
4. Les clients sont crees ou mis a jour par `customer_external_id`.
5. Les donnees sont stockees dans `customers`.

Colonnes obligatoires : `customer_id`, `name`, `tenure`, `monthly_charges`, `total_charges`, `contract_type`, `support_tickets`, `late_payments`, `churn`.

## Flux ML Churn

1. `ml/training/train_churn_model.py` charge PostgreSQL ou le CSV sample.
2. `feature_engineering.py` construit les features.
3. XGBoost entraine un classifieur churn.
4. MLflow log les parametres, metriques et artefacts.
5. Le modele est sauvegarde dans `ml/models/churn_model.pkl`.
6. Les features sont sauvegardees dans `ml/models/churn_features.json`.
7. `model_service.py` charge ces artefacts pour predire.

## Flux Risk Score

1. `POST /risk/analyze-customer` trouve le client.
2. `model_service.py` predit la probabilite de churn.
3. `risk_scoring_service.py` combine churn, retards de paiement, tickets support, tenure, contrat et valeur client.
4. Le score final est entre 0 et 100.
5. Le niveau est `low`, `medium` ou `high`.
6. Les raisons et actions sont generees.
7. Une ligne est ecrite dans `risk_predictions`.

## Flux Agent LangGraph

1. `POST /agent/analyze` recoit une question.
2. `riskops_agent.py` cree un graphe avec deux noeuds : `route` et `execute`.
3. Le routeur choisit un outil :
   - `analyze_customer` si la question contient un identifiant type `CUST-001`,
   - `weekly_report` si elle parle de rapport,
   - `priority_customers` si elle parle de priorite/risque,
   - `rag` si elle parle de document/source/pdf,
   - `fallback` sinon.
4. L'outil execute renvoie une reponse structuree.
5. L'appel est trace dans JSONL.

## Flux Airflow + dbt

Le DAG `riskops_daily_pipeline` execute :

1. health check API,
2. import sample customers,
3. `dbt run`,
4. `dbt test`,
5. entrainement churn,
6. generation weekly-risk,
7. affichage pipeline summary.

dbt construit :

- `stg_customers` : nettoyage de la table source,
- `int_customer_risk_features` : flags analytiques,
- `mart_customer_risk_summary` : vue prete dashboard.

## Flux Monitoring MLOps Et LLMOps

MLOps :

1. `POST /monitoring/ml/generate-report`.
2. `ml_monitoring_service.py` lit le dataset reference `data/sample/customers_sample.csv`.
3. Il lit les clients actuels PostgreSQL.
4. Il compare valeurs manquantes et drift simple.
5. Il genere `monitoring/reports/ml_data_quality_report.html`.

LLMOps :

1. `POST /rag/ask` et `POST /agent/analyze` sont encapsules par `trace_llm_call`.
2. Chaque trace contient timestamp, operation, question, document id, tool, latence, statut, erreur, sources.
3. Les traces sont ecrites dans `monitoring/logs/llm_traces.jsonl`.
4. Langfuse peut etre active par variables d'environnement, mais le fallback JSONL marche sans secret.

## Carte Des Endpoints

| Endpoint | Methode | Role |
|---|---:|---|
| `/health` | GET | Liveness API + DB + modele + pgvector |
| `/ready` | GET | Readiness DB, tables, modele, dossiers monitoring |
| `/documents/upload` | POST | Upload PDF/CSV |
| `/documents` | GET | Liste documents |
| `/documents/{document_id}` | GET | Detail document |
| `/documents/{document_id}/process` | POST | Extraction, chunks, embeddings |
| `/rag/ask` | POST | Question RAG avec sources |
| `/customers/import` | POST | Import CSV clients |
| `/customers` | GET | Liste clients |
| `/customers/{customer_id}` | GET | Detail client |
| `/risk/predict` | POST | Prediction churn + score simple |
| `/risk/analyze-customer` | POST | Analyse RiskOps complete |
| `/risk/priority-customers` | GET | Clients tries par risque |
| `/risk/history` | GET | Historique predictions |
| `/risk/customers` | GET | Vue clients avec scores |
| `/reports/weekly-risk` | GET | Rapport hebdomadaire |
| `/agent/analyze` | POST | Agent LangGraph controle |
| `/monitoring/ml/generate-report` | POST | Genere rapport ML |
| `/monitoring/ml/report` | GET | Statut rapport ML |
| `/monitoring/ml/report?format=html` | GET | HTML rapport ML |
| `/monitoring/llm/traces` | GET | Liste traces |
| `/monitoring/llm/summary` | GET | Resume traces |

## Carte Des Tables PostgreSQL

### `customers`

Stocke les clients et signaux risque :

- `id`
- `customer_external_id`
- `name`
- `segment`
- `monthly_spend`
- `tenure`
- `monthly_charges`
- `total_charges`
- `contract_type`
- `support_tickets`
- `late_payments`
- `churn`
- `support_ticket_count`
- `unpaid_invoice_count`
- `churn_probability`
- `risk_score`
- `risk_level`
- `created_at`
- `updated_at`

### `documents`

Stocke les metadonnees documents :

- `id`
- `filename`
- `document_type`
- `source_path`
- `status`
- `created_at`
- `processed_at`

### `document_chunks`

Stocke les chunks RAG :

- `id`
- `document_id`
- `chunk_index`
- `content`
- `embedding`
- `metadata`
- `created_at`

### `risk_predictions`

Stocke l'historique RiskOps :

- `id`
- `customer_id`
- `churn_probability`
- `risk_score`
- `risk_level`
- `reasons`
- `recommended_actions`
- `model_version`
- `created_at`

## Carte Des Services Backend

| Service | Responsabilite |
|---|---|
| `file_storage` | Sauvegarde uploads |
| `text_extraction` | Lit PDF/CSV |
| `chunking` | Decoupe texte |
| `embedding_service` | OpenAI embeddings/reponses |
| `rag_service` | Processing document et RAG |
| `customer_import_service` | Import CSV clients |
| `feature_engineering` | Features ML |
| `model_service` | Chargement modele + prediction |
| `risk_scoring_service` | Score business final |
| `recommendation_service` | Actions recommandees |
| `report_service` | Priorisation + weekly report |
| `riskops_agent` | Agent LangGraph |
| `ml_monitoring_service` | Rapport MLOps HTML |
| `llm_observability_service` | Traces LLMOps JSONL |

## Ordre Exact De Lecture Du Code

1. `README.md`
2. `docker-compose.yml`
3. `backend/app/main.py`
4. `backend/app/core/config.py`
5. `backend/app/db/session.py`
6. `backend/app/db/init_db.py`
7. `backend/app/models/customer.py`
8. `backend/app/models/document.py`
9. `backend/app/models/risk_prediction.py`
10. `backend/app/api/health.py`
11. `backend/app/api/customers.py`
12. `backend/app/services/customer_import_service.py`
13. `backend/app/api/risk.py`
14. `backend/app/services/feature_engineering.py`
15. `backend/app/services/model_service.py`
16. `backend/app/services/risk_scoring_service.py`
17. `backend/app/services/report_service.py`
18. `backend/app/api/documents.py`
19. `backend/app/services/file_storage.py`
20. `backend/app/services/text_extraction.py`
21. `backend/app/services/chunking.py`
22. `backend/app/services/embedding_service.py`
23. `backend/app/services/rag_service.py`
24. `backend/app/api/rag.py`
25. `backend/app/services/riskops_agent.py`
26. `backend/app/api/agent.py`
27. `backend/app/services/ml_monitoring_service.py`
28. `backend/app/services/llm_observability_service.py`
29. `backend/app/api/monitoring.py`
30. `frontend/app.py`
31. `ml/training/train_churn_model.py`
32. `pipelines/airflow/dags/riskops_daily_pipeline.py`
33. `pipelines/dbt/riskops_dbt/models/`
34. `scripts/dev/demo_seed.py`

## Technologies A Comprendre

### Python

- Definition : langage principal du projet.
- Pourquoi : ecosysteme backend, data, ML et IA.
- Role : API, scripts, ML, pipelines.
- Avantages : lisible, riche en librairies.
- Limites : performance brute moindre que langages compiles.
- Phrase entretien : "Python me permet de relier backend, data engineering et machine learning dans un meme projet."

### FastAPI

- Definition : framework web Python pour APIs.
- Pourquoi : endpoints types, Swagger automatique.
- Role : backend central.
- Avantages : rapide, clair, compatible Pydantic.
- Limites : necessite discipline d'architecture.
- Phrase entretien : "FastAPI expose les capacites IA sous forme d'APIs testables."

### Streamlit

- Definition : framework Python pour dashboards rapides.
- Pourquoi : demo produit rapide.
- Role : interface utilisateur.
- Avantages : tres rapide pour prototyper.
- Limites : moins adapte aux apps frontend complexes.
- Phrase entretien : "Streamlit sert de dashboard demo connecte a FastAPI."

### PostgreSQL

- Definition : base relationnelle robuste.
- Pourquoi : donnees business persistantes.
- Role : clients, documents, predictions.
- Avantages : SQL, fiabilite, ecosysteme.
- Limites : necessite schema et migrations.
- Phrase entretien : "PostgreSQL garde la partie business fiable et interrogeable."

### SQLAlchemy

- Definition : ORM Python.
- Pourquoi : mapper classes Python vers tables SQL.
- Role : modeles et sessions DB.
- Avantages : abstrait SQL sans le cacher totalement.
- Limites : peut devenir complexe si mal utilise.
- Phrase entretien : "SQLAlchemy structure l'acces aux donnees sans ecrire du SQL partout."

### Pydantic

- Definition : validation de donnees typee.
- Pourquoi : schemas API clairs.
- Role : requetes et reponses FastAPI.
- Avantages : validation automatique.
- Limites : schemas a maintenir.
- Phrase entretien : "Pydantic garantit des contrats API explicites."

### pgvector

- Definition : extension PostgreSQL pour vecteurs.
- Pourquoi : recherche semantique dans Postgres.
- Role : embeddings des chunks.
- Avantages : evite une base vectorielle separee.
- Limites : moins specialise qu'un vector DB dedie a tres grande echelle.
- Phrase entretien : "pgvector permet de faire du RAG dans PostgreSQL."

### RAG

- Definition : Retrieval-Augmented Generation.
- Pourquoi : repondre avec contexte documentaire.
- Role : questions sur documents uploades.
- Avantages : sources, moins d'hallucination.
- Limites : depend de la qualite extraction/retrieval.
- Phrase entretien : "Le RAG connecte le LLM aux documents reels du projet."

### Embeddings

- Definition : vecteurs numeriques representant le sens.
- Pourquoi : comparer question et chunks.
- Role : recherche semantique.
- Avantages : retrouve le sens, pas seulement les mots exacts.
- Limites : cout API et dependance modele.
- Phrase entretien : "Les embeddings transforment le texte en espace vectoriel recherchable."

### Chunking

- Definition : decoupage du texte en morceaux.
- Pourquoi : les LLMs et embeddings travaillent mieux sur des passages limites.
- Role : creation de `document_chunks`.
- Avantages : retrieval plus precis.
- Limites : mauvais decoupage = mauvais contexte.
- Phrase entretien : "Le chunking prepare les documents pour une recherche semantique fiable."

### OpenAI API

- Definition : API de modeles embeddings et chat.
- Pourquoi : generer embeddings et reponses RAG.
- Role : IA generative.
- Avantages : qualite modele, integration simple.
- Limites : cout, latence, besoin de cle.
- Phrase entretien : "OpenAI est utilise uniquement la ou le projet a besoin d'embeddings ou de generation."

### LlamaIndex

- Definition : librairie RAG/indexing.
- Pourquoi : outils de parsing/chunking utiles au RAG.
- Role : `SentenceSplitter` pour le chunking.
- Avantages : composants RAG prets a l'emploi.
- Limites : peut etre lourd si on l'utilise sans controle.
- Phrase entretien : "LlamaIndex fournit des briques RAG, ici gardees simples et inspectables."

### LangGraph

- Definition : framework pour workflows agents.
- Pourquoi : agent controle et explicable.
- Role : router question vers outil.
- Avantages : graphe explicite.
- Limites : plus verbeux qu'une simple fonction.
- Phrase entretien : "LangGraph rend l'agent controlable, pas magique."

### XGBoost

- Definition : modele gradient boosting pour donnees tabulaires.
- Pourquoi : fort baseline churn.
- Role : prediction de churn.
- Avantages : performant sur tabulaire.
- Limites : moins interpretable qu'un modele simple.
- Phrase entretien : "XGBoost donne un modele churn solide pour des features clients."

### Scikit-learn

- Definition : librairie ML Python.
- Pourquoi : split, metriques, outils ML.
- Role : train/test et evaluation.
- Avantages : standard, simple.
- Limites : pas specialise deep learning.
- Phrase entretien : "Scikit-learn fournit les briques d'evaluation ML."

### MLflow

- Definition : tracking d'experiences ML.
- Pourquoi : historiser parametres, metriques, artefacts.
- Role : logs entrainement local.
- Avantages : reproductibilite.
- Limites : ici local, pas serveur distant.
- Phrase entretien : "MLflow montre que le modele est suivi, pas entraine a la main sans trace."

### Airflow

- Definition : orchestrateur de workflows.
- Pourquoi : automatiser une suite de taches.
- Role : DAG daily pipeline.
- Avantages : scheduling, retries, UI.
- Limites : lourd pour une petite demo.
- Phrase entretien : "Airflow montre comment industrialiser le pipeline."

### DAG

- Definition : graphe acyclique dirige de taches.
- Pourquoi : imposer l'ordre execution.
- Role : health -> import -> dbt -> train -> report.
- Avantages : dependances explicites.
- Limites : doit rester simple pour etre maintenable.
- Phrase entretien : "Le DAG rend le pipeline observable et repetable."

### dbt

- Definition : outil de transformation SQL.
- Pourquoi : organiser et tester les modeles analytiques.
- Role : staging, intermediate, mart.
- Avantages : SQL versionne, tests.
- Limites : ne remplace pas l'orchestration ni l'API.
- Phrase entretien : "dbt transforme les donnees metier en tables analytiques propres."

### Docker

- Definition : conteneurisation.
- Pourquoi : environnement reproductible.
- Role : images backend, frontend, Airflow.
- Avantages : isolation, portabilite.
- Limites : build parfois lourd.
- Phrase entretien : "Docker rend la demo reproductible sur une machine."

### Docker Compose

- Definition : orchestration locale multi-conteneurs.
- Pourquoi : lancer backend, frontend, DB, Airflow.
- Role : environnement local complet.
- Avantages : une commande pour tout lancer.
- Limites : pas equivalent a Kubernetes/prod cloud.
- Phrase entretien : "Compose assemble tous les services de la stack locale."

### GitHub Actions

- Definition : CI/CD GitHub.
- Pourquoi : valider automatiquement le repo.
- Role : install, compile, compose config, fichiers docs.
- Avantages : qualite avant merge.
- Limites : pas encore tests integration Postgres.
- Phrase entretien : "GitHub Actions verifie que le projet reste runnable."

### MLOps

- Definition : pratiques de production ML.
- Pourquoi : suivre modele, data quality, artefacts.
- Role : MLflow + rapport monitoring.
- Avantages : fiabilite.
- Limites : monitoring local simple.
- Phrase entretien : "Le MLOps evite que le modele soit une boite noire non suivie."

### LLMOps

- Definition : observabilite des features LLM.
- Pourquoi : comprendre latence, erreurs, usage.
- Role : traces RAG/agent.
- Avantages : debug et audit.
- Limites : pas encore dashboard externe obligatoire.
- Phrase entretien : "Le LLMOps trace ce que font RAG et agent."

### Evidently-Style Monitoring

- Definition : rapport data quality/drift inspire d'Evidently.
- Pourquoi : surveiller les donnees courantes vs reference.
- Role : HTML local.
- Avantages : simple, inspectable.
- Limites : pas un vrai Evidently complet installe.
- Phrase entretien : "Le rapport montre une premiere couche de monitoring ML defensive."

### Langfuse Optionnel

- Definition : plateforme de tracing LLM.
- Pourquoi : export traces LLM si credentials presents.
- Role : option dans `llm_observability_service.py`.
- Avantages : observabilite externe.
- Limites : non requis pour la demo locale.
- Phrase entretien : "Langfuse est optionnel, le projet garde un fallback JSONL."

### JSONL Traces

- Definition : un JSON par ligne.
- Pourquoi : logs simples et append-only.
- Role : traces LLM locales.
- Avantages : facile a lire, parser, ignorer Git.
- Limites : pas une base de donnees d'observabilite.
- Phrase entretien : "JSONL donne une observabilite locale sans dependance externe."

### Health Check

- Definition : endpoint de sante service.
- Pourquoi : savoir si l'API repond.
- Role : `/health`.
- Avantages : utile Docker et debug.
- Limites : ne garantit pas toute la readiness.
- Phrase entretien : "Le health check dit si le service est vivant."

### Readiness Check

- Definition : endpoint de pret-a-servir.
- Pourquoi : verifier DB, tables, modele, dossiers.
- Role : `/ready`.
- Avantages : evite demos sur systeme incomplet.
- Limites : ne teste pas tous les cas metier.
- Phrase entretien : "La readiness dit si le service peut accepter du trafic utile."

## Commandes De Lancement

Windows PowerShell :

```powershell
scripts/dev/start.ps1
```

Si la politique PowerShell bloque :

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev/start.ps1
```

Bash :

```bash
bash scripts/dev/start.sh
```

Docker direct :

```bash
docker compose up -d --build
```

## Commandes Pour Arreter

PowerShell :

```powershell
scripts/dev/stop.ps1
```

Bash :

```bash
bash scripts/dev/stop.sh
```

Docker direct :

```bash
docker compose down
```

## Commandes De Test Et Demo

Healthcheck PowerShell :

```powershell
scripts/dev/healthcheck.ps1
```

Alternative :

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev/healthcheck.ps1
```

Demo seed PowerShell :

```powershell
scripts/dev/demo-seed.ps1
```

Bash :

```bash
bash scripts/dev/healthcheck.sh
bash scripts/dev/demo-seed.sh
```

Docker logs :

```bash
docker compose ps
docker compose logs backend
docker compose logs frontend
docker compose logs airflow-webserver
```

API utiles :

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/customers
curl http://localhost:8000/risk/priority-customers
curl http://localhost:8000/reports/weekly-risk
curl http://localhost:8000/monitoring/llm/summary
```

## URLs Importantes

- FastAPI docs : http://localhost:8000/docs
- Streamlit : http://localhost:8501
- Airflow : http://localhost:8080
- Health : http://localhost:8000/health
- Ready : http://localhost:8000/ready
- ML monitoring HTML : http://localhost:8000/monitoring/ml/report?format=html

## Erreurs Frequentes

- `OPENAI_API_KEY is missing` : normal si aucune cle n'est configuree. Les flux RiskOps sans RAG restent utilisables.
- `Churn model is not trained yet` : lancer `python ml/training/train_churn_model.py` ou `scripts/dev/demo-seed.ps1`.
- `/ready` retourne `503` : verifier PostgreSQL, tables, modele et dossiers monitoring.
- Upload refuse : seuls PDF et CSV sont acceptes.
- CSV client refuse : colonnes obligatoires manquantes ou valeurs numeriques invalides.
- `docker compose config` echoue : verifier Docker Compose et syntaxe YAML.
- PowerShell bloque un script : utiliser `powershell -ExecutionPolicy Bypass -File ...`.
- Bash sous Windows ne trouve pas Docker : Docker Desktop n'est pas integre a WSL ; utiliser PowerShell.
- Rapport ML absent : lancer `POST /monitoring/ml/generate-report` ou `scripts/dev/demo-seed.ps1`.
- Airflow lent au demarrage : attendre que `airflow-webserver` passe healthy.

## Questions Entretien Possibles

1. Pourquoi ce projet n'est pas juste un chatbot ?
Parce qu'il connecte LLM, donnees persistantes, ML, pipelines, monitoring et APIs.

2. Pourquoi FastAPI ?
Pour exposer des endpoints types, testes et documentes automatiquement.

3. Pourquoi PostgreSQL + pgvector ?
PostgreSQL gere les donnees metier et pgvector ajoute la recherche semantique sans base separee.

4. Comment marche le RAG ?
On extrait, chunke, embedde, stocke, retrieve les chunks proches, puis le LLM repond avec sources.

5. Que se passe-t-il sans OpenAI ?
Le RAG est indisponible, mais l'import clients, le ML, le Risk Score, les rapports et l'agent priorite fonctionnent.

6. Pourquoi XGBoost ?
C'est un bon baseline tabulaire pour le churn.

7. Pourquoi LangGraph ?
Pour garder un agent controle, avec routes explicites.

8. Pourquoi Airflow et dbt ?
Airflow orchestre les taches, dbt structure les transformations SQL.

9. Quelle difference entre `/health` et `/ready` ?
`/health` dit si le service repond ; `/ready` dit si les dependances utiles sont pretes.

10. Qu'est-ce que le monitoring LLM ?
Des traces de chaque appel RAG/agent avec latence, statut, erreur et outil choisi.

11. Quelles sont les limites du projet ?
Pas de cloud, pas d'auth, dataset petit, monitoring local, RAG dependant d'OpenAI.

12. Comment le rendre production-ready ?
Ajouter auth, secrets manager, CI integration tests, monitoring externe, alerting, deploiement cloud.

## Resume Final A Apprendre

AI RiskOps Copilot est une application IA complete orientee risque client. Streamlit fournit l'interface, FastAPI expose les APIs, PostgreSQL stocke les donnees, pgvector supporte le RAG, XGBoost predit le churn, LangGraph route les questions, Airflow et dbt orchestrent la data, MLflow suit le modele, et le monitoring trace la qualite ML et les appels LLM. Le projet montre une architecture AI Engineering defendable, pas seulement une demo de chatbot.
