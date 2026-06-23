# Cahier des charges

## 1. Nom du projet

AI RiskOps Copilot

## 2. Objectif

Construire un assistant IA qui aide une entreprise à détecter les risques dans ses documents, ses données clients et ses opérations.

Le projet doit démontrer un niveau professionnel en:

- AI Engineering
- Data Engineering
- Machine Learning
- MLOps
- LLMOps

## 3. Problème à résoudre

Les entreprises ont trop de données dispersées.

Les informations utiles se trouvent dans:

- contrats
- factures
- tickets support
- fichiers CSV
- bases SQL
- rapports internes

Un manager veut savoir rapidement:

- quels clients risquent de partir
- quelles factures sont anormales
- quels contrats contiennent des clauses dangereuses
- quels tickets support deviennent urgents
- quelles actions faire cette semaine

## 4. Utilisateurs ciblés

Utilisateur principal:

- manager business

Utilisateurs secondaires:

- data analyst
- équipe support
- équipe finance
- responsable client
- direction
- recruteur ou jury

## 5. Fonctionnalités MVP

- upload PDF
- upload CSV clients
- stockage PostgreSQL
- schéma prêt pour les embeddings
- dashboard Streamlit
- endpoint FastAPI health check
- base pgvector prête pour RAG
- dataset client de test
- Docker local

## 6. Fonctionnalités avancées

- extraction texte PDF
- chunking
- embeddings OpenAI
- RAG avec sources
- modèle churn avec XGBoost
- suivi MLflow
- agent LangGraph
- Risk Score global
- pipeline Airflow
- transformations dbt
- monitoring Langfuse
- monitoring Evidently AI
- CI/CD GitHub Actions
- déploiement AWS

## 7. Risk Score global

Le Risk Score est un score sur 100.

Il combine:

- probabilité de churn
- nombre de tickets critiques
- factures impayées
- baisse de revenu
- risques contractuels
- signaux négatifs dans les documents

Sortie attendue:

- score global
- raisons principales
- sources utilisées
- top 5 actions recommandées

## 8. Contraintes techniques

- le projet doit tourner localement avec Docker
- le MVP doit rester simple
- les modules doivent être séparés
- le code doit être lisible
- le README doit expliquer le projet clairement
- les données sensibles ne doivent pas être incluses
- les clés API doivent rester dans `.env`

## 9. Livrables

- dépôt projet propre
- backend FastAPI
- dashboard Streamlit
- base PostgreSQL avec pgvector
- documentation projet
- architecture
- roadmap
- README
- fichier ZIP partageable

## 10. Critères de réussite

Le projet est réussi si:

- l'API démarre
- le dashboard démarre
- PostgreSQL fonctionne
- pgvector est activé
- la structure permet d'ajouter RAG, ML et agents
- le projet est facile à expliquer en entretien

