#!/usr/bin/env bash
# run_all.sh — Build, lance et teste tout le pipeline dans Docker
# Usage : ./run_all.sh

set -e
cd "$(dirname "$0")"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo -e "${CYAN}  ♟️  Chess Agent POC — Pipeline Docker complet${NC}"
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo ""

# ── 1. Build ────────────────────────────────────────
echo -e "${CYAN}[1/4] Build des images Docker...${NC}"
echo "      (peut prendre 5-10 min, surtout le backend avec PyTorch)"
docker compose build --parallel backend frontend 2>&1 | tail -5
echo ""

# ── 2. Démarrage ────────────────────────────────────
echo -e "${CYAN}[2/4] Démarrage des conteneurs...${NC}"
docker compose up -d

echo "      ⏳ Attente des services..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/api/v1/healthcheck > /dev/null 2>&1; then
        echo -e "      ${GREEN}✅ API prête${NC}"
        break
    fi
    sleep 3
done
echo ""

# ── 3. Ingestion Milvus ─────────────────────────────
echo -e "${CYAN}[3/4] Vérification des données Milvus...${NC}"
if docker compose exec -T backend poetry run python3 -c "
from pymilvus import connections, utility
connections.connect(host='milvus-standalone', port=19530)
print('exists' if utility.has_collection('chess_openings') else 'missing')
" 2>/dev/null | grep -q "missing"; then
    echo "      🔄 Ingestion des données..."
    docker compose exec -T backend poetry run python scripts/ingest_openings.py 2>&1 | tail -3
else
    echo "      ✅ Données déjà présentes"
fi
echo ""

# ── 4. Tests ────────────────────────────────────────
echo -e "${CYAN}[4/4] Lancement des tests...${NC}"
echo ""

PASS=0
FAIL=0
BASE="http://localhost:8000/api/v1"

FEN_START="rnbqkbnr%2Fpppppppp%2F8%2F8%2F8%2F8%2FPPPPPPPP%2FRNBQKBNR%20w%20KQkq%20-%200%201"
FEN_E4="rnbqkbnr%2Fpppppppp%2F8%2F8%2F4P3%2F8%2FPPPP1PPP%2FRNBQKBNR%20b%20KQkq%20-%200%201"
FEN_RANDOM="8%2F8%2F8%2F8%2F8%2F3k4%2F8%2F3K4%20w%20-%20-%200%201"
FEN_INVALID="toto"

test_endpoint() {
    local label="$1"
    local url="$2"
    local expected="$3"
    printf "  %-55s " "$label"
    code=$(curl -s -o /tmp/chess_test.json -w "%{http_code}" --max-time 30 "$url")
    if [ "$code" = "$expected" ]; then
        echo -e "${GREEN}✅ $code${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}❌ $code (attendu $expected)${NC}"
        FAIL=$((FAIL + 1))
    fi
}

echo "🏥 Healthcheck"
test_endpoint "GET /healthcheck" "$BASE/healthcheck" 200

echo ""
echo "📖 Moves (Lichess)"
test_endpoint "Position de départ" "$BASE/moves/$FEN_START" 200
test_endpoint "Après 1.e4" "$BASE/moves/$FEN_E4" 200
test_endpoint "FEN invalide → 400" "$BASE/moves/$FEN_INVALID" 400

echo ""
echo "⚙️  Evaluate (Stockfish)"
test_endpoint "Position de départ" "$BASE/evaluate/$FEN_START" 200
test_endpoint "Rois seuls (hors théorie)" "$BASE/evaluate/$FEN_RANDOM" 200

echo ""
echo "🔍 Vector Search (Milvus RAG)"
test_endpoint "Recherche 'Sicilienne'" "$BASE/vector-search?q=Sicilienne" 200
test_endpoint "Recherche 'Gambit Dame'" "$BASE/vector-search?q=Gambit%20Dame" 200

echo ""
echo "🧠 Advice (pipeline complet)"
test_endpoint "Conseil après 1.e4" "$BASE/advice/$FEN_E4" 200
test_endpoint "Position hors théorie" "$BASE/advice/$FEN_RANDOM" 200

echo ""
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
TOTAL=$((PASS + FAIL))
echo "  Résultats : $PASS/$TOTAL"
if [ $FAIL -eq 0 ]; then
    echo -e "  ${GREEN}🎉 Tous les tests passent !${NC}"
else
    echo -e "  ${RED}⚠️  $FAIL test(s) en échec${NC}"
fi
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo ""
echo "  API      : http://localhost:8000"
echo "  Swagger  : http://localhost:8000/docs"
echo "  Frontend : http://localhost:4200"
echo ""
echo "  Pour arrêter : docker compose down"
