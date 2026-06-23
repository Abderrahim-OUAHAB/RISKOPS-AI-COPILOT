# Guide de lancement

## Prérequis

Installer:

- Docker
- Docker Compose
- Git

## Lancer le projet

Depuis la racine du projet:

```bash
cp .env.example .env
docker compose up --build
```

## Vérifier l'API

Ouvrir:

```text
http://localhost:8000/health
```

Résultat attendu:

```json
{
  "status": "ok",
  "service": "riskops-api",
  "version": "0.1.0"
}
```

## Ouvrir la documentation API

```text
http://localhost:8000/docs
```

## Ouvrir l'interface

```text
http://localhost:8501
```

## Erreurs possibles

### Port déjà utilisé

Changer le port dans `docker-compose.yml`.

### Base non prête

Relancer:

```bash
docker compose down
docker compose up --build
```

### Clé OpenAI absente

Ce n'est pas bloquant pour le setup.

Elle sera utilisée dans le module RAG.

