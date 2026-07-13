from fastapi import APIRouter, HTTPException
from app.models.chess import EngineEvaluation
from app.services.fen_validator import validate_fen, InvalidFenError
from app.services.stockfish_service import evaluate_position, StockfishError

router = APIRouter(tags=["Evaluate"])


@router.get("/evaluate/{fen:path}", response_model=EngineEvaluation)
async def evaluate(fen: str):
    """
    Évalue une position FEN avec Stockfish.

    Retourne l'évaluation en centipawns (score > 0 = avantage Blancs),
    ou en nombre de coups avant mat, ainsi que le meilleur coup.
    """
    try:
        validate_fen(fen)
    except InvalidFenError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        return evaluate_position(fen)
    except StockfishError as e:
        raise HTTPException(status_code=503, detail=str(e))
