# Technologies et explications entretien

## Python

Ce que c'est:

Python est un langage de programmation très utilisé en data, IA et backend.

Pourquoi on l'utilise:

Il possède un grand écosystème pour le machine learning, les APIs et le traitement de données.

Rôle dans le projet:

Python sert à écrire le backend, le RAG, les modèles ML et les pipelines.

Avantages:

- simple à lire
- très utilisé en IA
- beaucoup de bibliothèques

Limites:

- moins rapide que Go ou Java pour certains services très lourds

Phrase entretien:

J'utilise Python car c'est le standard pour connecter data, machine learning et IA générative.

## FastAPI

Ce que c'est:

FastAPI est un framework Python pour créer des APIs.

Pourquoi on l'utilise:

Il permet d'exposer les fonctionnalités IA sous forme de services.

Rôle dans le projet:

Il connecte le frontend, la base de données, le RAG, le modèle ML et l'agent.

Avantages:

- rapide
- documentation automatique
- moderne

Limites:

- il faut bien gérer la structure, la sécurité et les erreurs

Phrase entretien:

FastAPI me permet de transformer mes modèles et workflows IA en services utilisables par une application.

## PostgreSQL

Ce que c'est:

PostgreSQL est une base de données relationnelle.

Pourquoi on l'utilise:

Elle est fiable, mature et très utilisée en entreprise.

Rôle dans le projet:

Elle stocke les clients, documents, scores, feedbacks et métadonnées.

Avantages:

- robuste
- compatible SQL
- adaptée aux données métier

Limites:

- demande une bonne modélisation des tables

Phrase entretien:

PostgreSQL garde les données métier structurées du projet.

## pgvector

Ce que c'est:

pgvector est une extension PostgreSQL qui stocke des embeddings.

Pourquoi on l'utilise:

Elle permet de faire de la recherche sémantique dans les documents.

Rôle dans le projet:

Elle stocke les vecteurs des chunks pour retrouver les passages proches d'une question.

Avantages:

- simple
- intégré à PostgreSQL
- suffisant pour un MVP

Limites:

- moins spécialisé que Pinecone ou Weaviate à grande échelle

Phrase entretien:

pgvector me permet d'ajouter la recherche vectorielle directement dans PostgreSQL.

## Streamlit

Ce que c'est:

Streamlit est un outil Python pour créer une interface data rapidement.

Pourquoi on l'utilise:

Il permet de créer une démo claire sans perdre du temps sur le frontend.

Rôle dans le projet:

Il affiche le dashboard, les uploads, les questions et les scores.

Avantages:

- rapide
- simple
- adapté aux projets data

Limites:

- moins flexible qu'un frontend React ou Next.js

Phrase entretien:

J'utilise Streamlit pour livrer vite une interface claire autour du système IA.

## Docker

Ce que c'est:

Docker permet de lancer une application dans des conteneurs.

Pourquoi on l'utilise:

Il évite les problèmes d'environnement entre machines.

Rôle dans le projet:

Il lance PostgreSQL, FastAPI et Streamlit ensemble.

Avantages:

- reproductible
- proche des pratiques entreprise
- facilite le déploiement

Limites:

- demande de comprendre les volumes, réseaux et variables d'environnement

Phrase entretien:

Docker garantit que le projet tourne de la même façon sur ma machine et sur une autre.

## LlamaIndex

Ce que c'est:

LlamaIndex est un framework pour connecter des documents à un LLM.

Pourquoi on l'utilise:

Il simplifie la construction d'un système RAG.

Rôle dans le projet:

Il gérera ingestion, chunking, recherche et réponses avec sources.

Avantages:

- très bon pour documents
- compatible avec plusieurs LLMs
- utile pour RAG

Limites:

- certaines abstractions peuvent cacher la logique interne

Phrase entretien:

LlamaIndex sert à transformer mes documents en base de connaissance interrogeable.

## LangGraph

Ce que c'est:

LangGraph est un framework pour créer des agents IA sous forme de workflow.

Pourquoi on l'utilise:

Il permet de contrôler les étapes de décision.

Rôle dans le projet:

Il choisira entre RAG, SQL, modèle ML ou génération de rapport.

Avantages:

- contrôlable
- testable
- explicable

Limites:

- plus complexe qu'un simple chatbot

Phrase entretien:

LangGraph me permet de créer un agent IA contrôlé qui suit un workflow métier explicable.

## XGBoost

Ce que c'est:

XGBoost est un algorithme de machine learning basé sur des arbres de décision.

Pourquoi on l'utilise:

Il est très performant sur les données tabulaires.

Rôle dans le projet:

Il prédira le risque de churn client.

Avantages:

- performant
- robuste
- très utilisé en entreprise

Limites:

- ne comprend pas le texte brut sans transformation

Phrase entretien:

J'utilise XGBoost car il reste une référence pour prédire des risques sur données structurées.

## MLflow

Ce que c'est:

MLflow est un outil de suivi des expériences machine learning.

Pourquoi on l'utilise:

Il aide à comparer les modèles, paramètres et métriques.

Rôle dans le projet:

Il tracera les entraînements du modèle churn.

Avantages:

- rend les expériences reproductibles
- facilite la comparaison des modèles
- utile pour MLOps

Limites:

- ne remplace pas un monitoring complet en production

Phrase entretien:

MLflow me permet de prouver quel modèle a été entraîné, avec quelles données et quelles performances.

