#!/usr/bin/env bash
# start.sh — Lance toute la stack Docker du POC Chess Agent en un clic
# Usage : ./start.sh

set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

banner() {
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    echo -e "${CYAN}  ♟️  Chess Agent FFE — Démarrage${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
}

# ── 0. Prérequis ─────────────────────────────────
banner
echo ""

if ! command -v docker > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker n'est pas installé.${NC}"
    echo "  Installez Docker Desktop ou Docker Engine : https://docs.docker.com/engine/install/"
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Le daemon Docker ne tourne pas.${NC}"
    echo "  Démarrez Docker Desktop, puis relancez ./start.sh"
    exit 1
fi

echo -e "${GREEN}✓ Docker opérationnel${NC}"

# ── 1. Configuration .env ────────────────────────
echo ""
echo "🔑 Vérification de la configuration..."

if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Fichier .env absent. Création depuis .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}   → Renseignez vos clés API dans .env, puis relancez ./start.sh${NC}"
fi

# Vérification des clés API
if ! grep -qE "LICHESS_API_TOKEN=.+" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  LICHESS_API_TOKEN manquant — /moves et /advice échoueront${NC}"
fi
if ! grep -qE "MISTRAL_API_KEY=.+" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  MISTRAL_API_KEY manquante — l'agent ne pourra pas formuler ses conseils${NC}"
fi
if ! grep -qE "YOUTUBE_API_KEY=.+" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  YOUTUBE_API_KEY manquante — des vidéos de secours seront utilisées${NC}"
fi

# ── 2. Démarrage des services ────────────────────
echo ""
echo "🐳 Démarrage des conteneurs..."
docker compose up -d

# ── 3. Attente de l'API ──────────────────────────
echo ""
echo "⏳ Attente que l'API soit prête..."
API_READY=false
for i in $(seq 1 30); do
    if curl -sf http://localhost:${API_PORT:-8000}/api/v1/healthcheck > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ API prête${NC}"
        API_READY=true
        break
    fi
    sleep 3
done

if [ "$API_READY" = false ]; then
    echo -e "${RED}✗ L'API n'a pas démarré après 90s.${NC}"
    echo "  Vérifiez les logs : docker compose logs backend"
    exit 1
fi

# ── 4. Ingestion Milvus ──────────────────────────
echo ""
echo "📥 Vérification des données Milvus..."
if docker compose exec -T backend poetry run python3 -c "
from pymilvus import connections, utility
connections.connect(host='milvus-standalone', port=19530)
print('exists' if utility.has_collection('chess_openings') else 'missing')
" 2>/dev/null | grep -q "missing"; then
    echo "   🔄 Première exécution : ingestion des articles d'ouvertures..."
    docker compose exec -T backend poetry run python scripts/ingest_openings.py
else
    echo -e "   ${GREEN}✅ Données déjà indexées${NC}"
fi

# ── 5. Résumé ────────────────────────────────────
echo ""
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo -e "  ${GREEN}✅ Stack opérationnelle !${NC}"
echo ""
echo "  🖥️  Frontend  : http://localhost:${FRONTEND_PORT:-4200}"
echo "  🔌 API       : http://localhost:${API_PORT:-8000}"
echo "  📚 Swagger   : http://localhost:${API_PORT:-8000}/docs"
echo ""
echo "  🧪 Tester    : ./test_pipeline.sh"
echo "  🎬 Démo      : voir Docs/demo.md"
echo "  ⏹️  Arrêter   : docker compose down"
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
