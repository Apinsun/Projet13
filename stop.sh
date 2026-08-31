#!/usr/bin/env bash
# stop.sh — Arrête toute la stack Docker du POC Chess Agent
# Usage : ./stop.sh [--purge]

set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo -e "${CYAN}  ♟️  Chess Agent FFE — Arrêt${NC}"
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo ""

if [ "$1" = "--purge" ]; then
    echo -e "${YELLOW}🧹 Arrêt et suppression des volumes (données Milvus/Mongo)...${NC}"
    docker compose down -v
else
    echo "⏹️  Arrêt des conteneurs (les données sont conservées)..."
    docker compose down
fi

echo ""
echo -e "${GREEN}✅ Stack arrêtée.${NC}"
echo ""
if [ "$1" != "--purge" ]; then
    echo "  💡 Pour redémarrer : ./start.sh"
    echo "  🧹 Pour tout purger (données incluses) : ./stop.sh --purge"
fi
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
