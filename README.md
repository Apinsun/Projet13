# ♟️ Chess Agent FFE

Agent IA pour l'apprentissage des **ouvertures d'échecs**, développé pour la **Fédération Française des Échecs (FFE)** dans le cadre d'un POC (proof of concept).

> **Contexte** : projet OpenClassrooms — voir [`Docs/transcription_projet.md`](Docs/transcription_projet.md) pour le brief complet.

---

## ✨ Ce que fait l'application

Le joueur déplace les pièces sur un échiquier interactif. L'agent IA analyse la position et fournit :

- 📖 **Le nom de l'ouverture** (via l'API Lichess)
- 💡 **Les coups théoriques** les plus joués par les maîtres
- 📚 **Le contexte encyclopédique** de l'ouverture (RAG via Milvus)
- ⚙️ **L'évaluation Stockfish** si la position sort de la théorie
- 🎥 **Des vidéos YouTube** pour approfondir
- 🧠 **Un conseil pédagogique** formulé par Mistral AI

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                Frontend Angular 19                    │
│         (ngx-chess-board + thème sombre)              │
└──────────────────────┬───────────────────────────────┘
                       │ HTTP /api/
┌──────────────────────▼───────────────────────────────┐
│                 Backend FastAPI                        │
│                                                       │
│  Graphe LangGraph :                                    │
│  validate → lichess → [milvus + youtube] ou [stockfish]│
│                    → format (Mistral)                  │
└───┬──────────┬───────────┬───────────┬────────────────┘
    │          │           │           │
┌───▼───┐ ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
│Lichess│ │ Milvus  │ │ MongoDB │ │Stockfish│
│  API  │ │  (RAG)  │ │ (cache) │ │ (moteur)│
└───────┘ └─────────┘ └─────────┘ └─────────┘
```

---

## 🚀 Démarrage rapide (un clic)

### Prérequis

- **Docker** + Docker Compose v2
- Trois clés API (gratuites) :
  | Clé | Où l'obtenir | Optionnelle ? |
  |-----|-------------|---------------|
  | `LICHESS_API_TOKEN` | https://lichess.org/account/oauth/token | ❌ Requise |
  | `MISTRAL_API_KEY` | https://console.mistral.ai/api-keys/ | ❌ Requise |
  | `YOUTUBE_API_KEY` | https://console.cloud.google.com/apis/credentials | ✅ (fallback sinon) |

### Lancement

```bash
# 1. Configurer les clés
cp .env.example .env
# → éditer .env avec vos clés

# 2. Lancer tout
./start.sh
```

C'est tout ! L'application est disponible sur :

| Accès | URL |
|-------|-----|
| 🖥️ **Frontend** | http://localhost:4200 |
| 🔌 **API** | http://localhost:8000 |
| 📚 **Swagger** | http://localhost:8000/docs |

### Tester

```bash
./test_pipeline.sh    # 14 tests automatisés
```

### Arrêter

```bash
docker compose down           # garde les données (volumes)
docker compose down -v        # purge tout
```

---

## 🎬 Démo

Des scénarios prêts à l'emploi pour tester manuellement : voir **[`Docs/demo.md`](Docs/demo.md)**.

---

## 🔌 Endpoints API

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/api/v1/healthcheck` | Santé du service |
| `GET` | `/api/v1/moves/{fen}` | Coups théoriques (Lichess) |
| `GET` | `/api/v1/evaluate/{fen}` | Évaluation Stockfish |
| `GET` | `/api/v1/vector-search?q=...` | Recherche RAG (Milvus) |
| `GET` | `/api/v1/videos/{opening}` | Vidéos YouTube (cache → API → fallback) |
| `GET` | `/api/v1/advice/{fen}` | Conseil complet (pipeline LangGraph) |

---

## 🐳 Services Docker

| Service | Image | Port | Rôle |
|---------|-------|------|------|
| **backend** | `Dockerfile` | `8000` | API FastAPI + LangGraph |
| **frontend** | `Dockerfile` | `4200` | Angular 19 + nginx |
| **mongo** | `mongo:7` | `27017` | Cache YouTube (TTL 24h) |
| **milvus-standalone** | `milvusdb/milvus:v2.4.17` | `19530` | Base vectorielle (RAG) |
| **etcd** | `quay.io/coreos/etcd` | — | Metadata store Milvus |
| **minio** | `minio/minio` | `9000` | Stockage objet Milvus |

---

## 📁 Structure du projet

```
Projet13/
├── backend/                    # Python 3.12 / Poetry
│   ├── app/
│   │   ├── api/                # 6 routes FastAPI
│   │   ├── agent/              # Graphe LangGraph (state + graph)
│   │   ├── services/           # lichess, stockfish, milvus, youtube, fen
│   │   ├── models/             # Modèles Pydantic
│   │   └── config.py           # Settings
│   ├── data/openings/          # 10 articles d'ouvertures (Wikichess)
│   ├── scripts/                # Ingestion Milvus
│   └── Dockerfile
├── frontend/                   # Angular 19
│   ├── src/app/
│   │   ├── components/         # chessboard + recommendations
│   │   ├── services/           # API + state (signals)
│   │   └── models/             # Types TS
│   ├── projects/ngx-chess-board/  # Librairie locale (source OpenClassrooms)
│   └── Dockerfile              # Multi-stage → nginx
├── docker-compose.yml          # 6 services
├── start.sh                    # 🚀 Lancement un clic
├── test_pipeline.sh            # 14 tests automatisés
├── .env.example                # Template de configuration
└── Docs/
    ├── demo.md                 # Scénarios de démonstration
    ├── transcription_projet.md # Brief OpenClassrooms
    └── STATUS.md               # État d'avancement
```

---

## 🔧 Dépannage

| Symptôme | Cause probable | Solution |
|----------|----------------|----------|
| `502 Bad Gateway` sur `/api/` | Backend pas encore prêt | Attendre quelques secondes, relancer |
| `Erreur Stockfish: ...` | Binaire Stockfish absent | `docker compose build backend` |
| Timeout sur `/vector-search` | Milvus en cours de démarrage | Attendre ~90s puis réessayer |
| Vidéos en `"source": "fallback"` | `YOUTUBE_API_KEY` absente | Ajouter la clé dans `.env` |
| `Temporary failure in name resolution` | DNS Docker instable | `docker compose restart backend` |

---

## 🧪 État du projet

| Étape | Statut |
|-------|--------|
| 1. Environnement | ✅ |
| 2. Agent LangGraph | ✅ |
| 3. Milvus RAG | ✅ |
| 4. YouTube API | ✅ |
| 5. Frontend Angular | ✅ |
| 6. Packaging | ✅ |
| 7. Étude de faisabilité vidéo | ⬜ |

---

## 📄 Licence

Projet pédagogique — OpenClassrooms / FFE.
