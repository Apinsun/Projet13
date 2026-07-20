from fastapi import APIRouter, HTTPException

from app.agent.state import AgentState
from app.agent.graph import create_graph
from app.services.fen_validator import validate_fen, InvalidFenError

router = APIRouter(tags=["Advice"])

# Le graphe est compilé une seule fois au démarrage
_graph = create_graph()


@router.get("/advice/{fen:path}")
async def get_advice(fen: str):
    """
    Demande un conseil à l'agent IA pour une position FEN.

    Le graphe LangGraph orchestre :
    1. Validation du FEN
    2. Recherche des coups théoriques (Lichess)
    3. Si position connue → explication pédagogique (Mistral)
    4. Si position inconnue → évaluation Stockfish → explication (Mistral)
    """
    try:
        validate_fen(fen)
    except InvalidFenError as e:
        raise HTTPException(status_code=400, detail=str(e))

    initial_state: AgentState = {
        "fen": fen,
        "lichess_moves": [],
        "lichess_opening": None,
        "stockfish_score": None,
        "stockfish_mate": None,
        "stockfish_best_move": None,
        "rag_context": None,
        "is_theoretical": False,
        "response": "",
        "error": None,
    }

    result = await _graph.ainvoke(initial_state)

    return {
        "fen": fen,
        "opening": result.get("lichess_opening"),
        "theoretical": result["is_theoretical"],
        "moves": result.get("lichess_moves", []),
        "stockfish_evaluation": {
            "score_cp": result.get("stockfish_score"),
            "mate_in": result.get("stockfish_mate"),
            "best_move": result.get("stockfish_best_move"),
        } if not result["is_theoretical"] else None,
        "advice": result["response"],
    }
