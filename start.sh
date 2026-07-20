#!/usr/bin/env bash
# start.sh — Lance toute la stack Docker du POC Chess Agent
# Usage : ./start.sh

set -e
cd "$(dirname "$0")"

echo "═══════════════════════════════════════════"
echo "  ♟️  Chess Agent POC — Démarrage Docker"
echo "═══════════════════════════════════════════"

# 1. Copier .env si nécessaire
if [ ! -f backend/.env ] || ! grep -q "LICHESS_API_TOKEN=lip_" backend/.env 2>/dev/null; then
    echo "⚠️  backend/.env incomplet : vérifie LICHESS_API_TOKEN et MISTRAL_API_KEY"
fi

# 2. Lancer tous les services
echo ""
echo "🐳 Démarrage des conteneurs..."
docker compose up -d

echo "   ⏳ Attente que l'API soit prête..."
for i in $(seq 1 15); do
    if curl -sf http://localhost:8000/api/v1/healthcheck > /dev/null 2>&1; then
        echo "   ✅ API prête"
        break
    fi
    sleep 2
done

# 3. Ingestion des données Milvus (si pas déjà fait)
echo ""
echo "📥 Vérification des données Milvus..."
if docker compose exec -T backend poetry run python3 -c "
from pymilvus import connections, utility
connections.connect(host='milvus-standalone', port=19530)
print('exists' if utility.has_collection('chess_openings') else 'missing')
" 2>/dev/null | grep -q "missing"; then
    echo "   🔄 Première exécution : ingestion des données..."
    docker compose exec -T backend poetry run python scripts/ingest_openings.py
else
    echo "   ✅ Données déjà indexées"
fi

echo ""
echo "═══════════════════════════════════════════"
echo "  ✅ Stack opérationnelle !"
echo ""
echo "  API      : http://localhost:8000"
echo "  Swagger  : http://localhost:8000/docs"
echo "  Frontend : http://localhost:4200"
echo ""
echo "  Pour tester : ./test_pipeline.sh"
echo "  Pour arrêter : docker compose down"
echo "═══════════════════════════════════════════"
