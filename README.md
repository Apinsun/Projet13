# Chess Agent — FFE

Agent IA pour l'apprentissage des ouvertures d'échecs, développé pour la Fédération Française des Échecs (FFE).

> **Contexte :** POC livré en 2 semaines — voir [`Docs/transcription_projet.md`](Docs/transcription_projet.md) pour le brief complet.

## Structure du projet

```
Projet13/
├── backend/                          # Python 3.12 / Poetry
│   ├── pyproject.toml                # Dépendances : fastapi, langgraph, pymilvus, etc.
│   ├── poetry.lock
│   ├── Dockerfile                    # Python 3.12-slim + Stockfish
│   ├── .env                          # Variables d'environnement (YOUTUBE_API_KEY, etc.)
│   └── app/
│       ├── main.py                   # FastAPI + CORS + route racine
│       ├── config.py                 # Settings (Pydantic, lecture du .env)
│       ├── api/
│       │   └── healthcheck.py        # GET /api/v1/healthcheck
│       ├── agent/                    # Futur graphe LangGraph (orchestration)
│       └── services/                 # Futurs services (Lichess, Stockfish, Milvus, YouTube)
│
├── frontend/                         # Angular 22
│   ├── package.json                  # ngx-chess-board, rxjs, etc.
│   ├── Dockerfile                    # Multi-stage : build Angular → nginx
│   ├── nginx.conf                    # Reverse proxy /api/ → backend:8000
│   └── src/app/                      # Code source Angular
│
├── docker-compose.yml                # Orchestration des 5 services
├── .env                              # Variables partagées (ports, clés API)
└── Docs/
    └── transcription_projet.md       # Brief complet du projet OpenClassrooms
```

## Services Docker Compose

| Service | Image/Contexte | Port | Rôle |
|---|---|---|---|
| **backend** | `./backend/Dockerfile` | `8000` | API FastAPI |
| **frontend** | `./frontend/Dockerfile` | `4200` | App Angular servie par nginx |
| **mongo** | `mongo:7` | `27017` | Base de données documentaire |
| **milvus-standalone** | `milvusdb/milvus:v2.4.17` | `19530` | Base vectorielle (RAG) |
| **etcd** | `quay.io/coreos/etcd:v3.5.5` | — | Metadata store pour Milvus |
| **minio** | `minio/minio` | `9000`, `9001` | Stockage objet pour Milvus |

## Démarrage rapide

```bash
# 1. Renseigner la clé YouTube API (optionnel pour les premières étapes)
cp backend/.env backend/.env.local    # et éditer YOUTUBE_API_KEY

# 2. Lancer tous les services
docker compose up -d

# 3. Vérifier
curl http://localhost:8000/api/v1/healthcheck   # → {"status":"ok"}
```

## Étapes de développement

1. ✅ Environnement de développement (Poetry, Angular, Docker Compose)
2. ⬜ Endpoints Lichess (`/moves/{fen}`) et Stockfish (`/evaluate/{fen}`)
3. ⬜ Intégration Milvus + RAG (Wikichess → embeddings → `/vector-search`)
4. ⬜ Intégration YouTube API (`/videos/{opening}`)
5. ⬜ Interface Angular (échiquier interactif + panneau recommandations)
6. ⬜ Packaging final (docker-compose complet, README, démo)
7. ⬜ Étude de faisabilité système d'analyse vidéo (document 8-10 pages, MCP)
8. ⬜ Autoévaluation et mentorat
