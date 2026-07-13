from fastapi import APIRouter, HTTPException
from app.models.chess import MoveResponse
from app.services.fen_validator import validate_fen, InvalidFenError
from app.services.lichess_service import get_opening_moves, LichessApiError

router = APIRouter(tags=["Moves"])


@router.get("/moves/{fen:path}", response_model=MoveResponse)
async def get_moves(fen: str):
    """
    Retourne les coups théoriques pour une position FEN donnée.

    Interroge l'API Lichess Opening Explorer. Si la position est connue,
    retourne la liste des coups théoriques avec leurs statistiques
    (taux de victoire Blancs/Nuls/Noirs) et le nom de l'ouverture.
    """
    try:
        validate_fen(fen)
    except InvalidFenError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        moves, opening = await get_opening_moves(fen)
    except LichessApiError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return MoveResponse(
        fen=fen,
        opening=opening,
        moves=moves,
    )
