# Chess Agent — FFE

Agent IA pour l'apprentissage des ouvertures d'échecs, développé pour la Fédération Française des Échecs (FFE).

> **Contexte :** POC livré en 2 semaines — voir [`Docs/transcription_projet.md`](Docs/transcription_projet.md) pour le brief complet.

## Structure du projet

```
Projet13/
├── backend/                          # Python 3.12 / Poetry
│   ├── pyproject.toml                # Dépendances
│   ├── poetry.lock
│   ├── Dockerfile                    # Python 3.12-slim + Stockfish
│   ├── .env                          # Variables d'environnement
│   └── app/
│       ├── main.py                   # FastAPI + CORS
│       ├── config.py                 # Settings Pydantic
│       ├── models/chess.py           # Modèles Pydantic
│       ├── api/
│       │   ├── healthcheck.py        # GET /api/v1/healthcheck
│       │   ├── moves.py              # GET /api/v1/moves/{fen}
│       │   ├── evaluate.py           # GET /api/v1/evaluate/{fen}
│       │   ├── vector_search.py      # GET /api/v1/vector-search
│       │   ├── youtube.py            # GET /api/v1/videos/{opening}
│       │   └── advice.py             # GET /api/v1/advice/{fen}
│       ├── agent/
│       │   ├── state.py              # AgentState TypedDict
│       │   └── graph.py              # Graphe LangGraph (6 nœuds)
│       └── services/
│           ├── fen_validator.py      # Validation FEN (python-chess)
│           ├── lichess_service.py    # Client Lichess Explorer API
│           ├── stockfish_service.py  # Wrapper Stockfish UCI
│           ├── milvus_service.py     # Recherche vectorielle Milvus
│           └── youtube_service.py    # Recherche YouTube + cache MongoDB
│
├── frontend/                         # Angular 19
│   ├── package.json                  # ngx-chess-board, @angular/cdk, etc.
│   ├── Dockerfile                    # Multi-stage : build → nginx
│   ├── nginx.conf
│   └── src/app/
│
├── docker-compose.yml                # 6 services
├── .env                              # Variables partagées
├── start.sh                          # Démarrage Docker Compose
├── test_pipeline.sh                  # 13 tests automatisés
└── Docs/
    ├── transcription_projet.md       # Brief complet OpenClassrooms
    ├── STATUS.md                     # État d'avancement
    ├── langgraph_explanation.md
    ├── milvus_explanation.md
    └── ...
```

## Services Docker Compose

| Service | Image | Port | Rôle |
|---|---|---|---|
| **backend** | `Dockerfile` | `8000` | API FastAPI + LangGraph |
| **frontend** | `Dockerfile` | `4200` | App Angular servie par nginx |
| **mongo** | `mongo:7` | `27017` | Cache YouTube (TTL 24h) |
| **milvus-standalone** | `milvusdb/milvus:v2.4.17` | `19530` | Base vectorielle (RAG) |
| **etcd** | `quay.io/coreos/etcd:v3.5.5` | — | Metadata store Milvus |
| **minio** | `minio/minio` | `9000` | Stockage objet Milvus |

## Démarrage rapide

```bash
# 1. Renseigner les clés API dans backend/.env
LICHESS_API_TOKEN=lip_...     # https://lichess.org/account/oauth/token
MISTRAL_API_KEY=...           # API Mistral
YOUTUBE_API_KEY=...           # Optionnel — fallback intégré sinon

# 2. Lancer tous les services
bash start.sh

# 3. Tester
./test_pipeline.sh

# 4. Swagger
open http://localhost:8000/docs
```

## Étapes de développement

1. ✅ Environnement (Poetry, Angular, Docker Compose)
2. ✅ Agent LangGraph + Lichess + Stockfish + Mistral
3. ✅ Milvus RAG (10 articles, search + intégration graphe)
4. ✅ YouTube API + cache MongoDB + fallback curated
5. ⬜ Interface Angular (échiquier interactif + panneau recommandations)
6. ⬜ Packaging final (docker-compose complet, README, démo)
7. ⬜ Étude de faisabilité système d'analyse vidéo (document 8-10 pages, MCP)
8. ⬜ Autoévaluation et mentorat

## Graphe LangGraph

```
START → validate_fen → fetch_lichess → decide_path
                                          ├── théorique → fetch_milvus → fetch_youtube → format_response → Mistral
                                          └── non-théorique → fetch_stockfish → format_response → Mistral
```

## Endpoints API

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/api/v1/healthcheck` | Santé du service |
| `GET` | `/api/v1/moves/{fen}` | Coups théoriques (Lichess) |
| `GET` | `/api/v1/evaluate/{fen}` | Évaluation Stockfish |
| `GET` | `/api/v1/vector-search?q=...` | Recherche RAG (Milvus) |
| `GET` | `/api/v1/videos/{opening}` | Vidéos YouTube (cache → API → fallback) |
| `GET` | `/api/v1/advice/{fen}` | Conseil complet (pipeline LangGraph) |

## Corrections récentes

- **Frontend** : Downgrade Angular 22 → 19 pour compatibilité `ngx-chess-board` + `@angular/cdk`
- **Stockfish** : Suppression de `is_running()` (méthode supprimée de la lib stockfish v5)
- **YouTube** : Tous les imports `pymongo` sont lazy (pas d'échec au démarrage sans la dépendance)
- **MongoDB** : Correction timezone offset-aware vs offset-naive dans le cache YouTube
