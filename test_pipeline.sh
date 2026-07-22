#!/usr/bin/env bash
# test_pipeline.sh — Teste tous les endpoints du POC (pipeline Docker complet)
# Usage : ./test_pipeline.sh

HOST=${1:-localhost}
PORT=${2:-8000}
BASE="http://$HOST:$PORT/api/v1"
PASS=0
FAIL=0

green() { echo -e "\033[32m$1\033[0m"; }
red()   { echo -e "\033[31m$1\033[0m"; }
cyan()  { echo -e "\033[36m$1\033[0m"; }

test_endpoint() {
    local label="$1"
    local method="$2"
    local url="$3"
    local expected_code="$4"

    printf "  %-55s " "$label"
    http_code=$(curl -s -o /tmp/test_resp.json -w "%{http_code}" --max-time 30 -X "$method" "$url")

    if [ "$http_code" = "$expected_code" ]; then
        green "✅ $http_code"
        PASS=$((PASS + 1))
    else
        red "❌ $http_code (attendu $expected_code)"
        echo "    $(head -c 200 /tmp/test_resp.json 2>/dev/null)"
        FAIL=$((FAIL + 1))
    fi
}

echo "═══════════════════════════════════════════"
echo "  🧪 Chess Agent POC — Tests Pipeline"
echo "     Cible : $BASE"
echo "═══════════════════════════════════════════"
echo ""

# ── FENs de test ─────────────────────────────
FEN_START="rnbqkbnr%2Fpppppppp%2F8%2F8%2F8%2F8%2FPPPPPPPP%2FRNBQKBNR%20w%20KQkq%20-%200%201"
FEN_E4="rnbqkbnr%2Fpppppppp%2F8%2F8%2F4P3%2F8%2FPPPP1PPP%2FRNBQKBNR%20b%20KQkq%20-%200%201"
FEN_RANDOM="8%2F8%2F8%2F8%2F8%2F3k4%2F8%2F3K4%20w%20-%20-%200%201"
FEN_INVALID="toto"

# ── 1. Healthcheck ───────────────────────────
echo "🏥 Healthcheck"
test_endpoint "GET /healthcheck" GET "$BASE/healthcheck" 200
echo ""

# ── 2. Moves (Lichess) ───────────────────────
echo "📖 Moves (Lichess Opening Explorer)"
test_endpoint "Position de départ (20 coups théoriques)" GET "$BASE/moves/$FEN_START" 200
test_endpoint "Après 1.e4 → King's Pawn Game" GET "$BASE/moves/$FEN_E4" 200
test_endpoint "FEN invalide → 400" GET "$BASE/moves/$FEN_INVALID" 400
echo ""

# ── 3. Evaluate (Stockfish) ──────────────────
echo "⚙️  Evaluate (Stockfish dans Docker)"
test_endpoint "Position de départ" GET "$BASE/evaluate/$FEN_START" 200
test_endpoint "Position rois seuls" GET "$BASE/evaluate/$FEN_RANDOM" 200
echo ""

# ── 4. Vector Search (Milvus) ────────────────
echo "🔍 Vector Search (Milvus RAG)"
test_endpoint "Recherche 'Sicilienne'" GET "$BASE/vector-search?q=Sicilienne&top_k=2" 200
test_endpoint "Recherche 'Gambit Dame'" GET "$BASE/vector-search?q=Gambit%20Dame" 200
echo ""

# ── 5. YouTube Videos ────────────────────────
echo "🎥 YouTube Videos"
test_endpoint "Recherche 'Sicilienne'" GET "$BASE/videos/Sicilienne?top_k=2" 200
test_endpoint "Recherche 'Italienne'" GET "$BASE/videos/Italienne" 200
test_endpoint "Recherche 'Gambit Dame'" GET "$BASE/videos/Gambit%20Dame" 200
echo ""

# ── 6. Advice (pipeline complet) ─────────────
echo "🧠 Advice (LangGraph : Lichess + Milvus + Stockfish + Mistral)"
test_endpoint "Conseil après 1.e4 (théorique + RAG)" GET "$BASE/advice/$FEN_E4" 200
test_endpoint "Conseil position rois seuls (Stockfish)" GET "$BASE/advice/$FEN_RANDOM" 200
echo ""

# ── Résumé ───────────────────────────────────
echo "═══════════════════════════════════════════"
TOTAL=$((PASS + FAIL))
echo "  Résultats : $PASS/$TOTAL réussis"
if [ $FAIL -eq 0 ]; then
    green "  🎉 Tous les tests passent !"
else
    red "  ⚠️  $FAIL test(s) en échec"
fi
echo "═══════════════════════════════════════════"
