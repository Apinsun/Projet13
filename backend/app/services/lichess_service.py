import httpx
from app.models.chess import TheoreticalMove, OpeningInfo
from app.config import settings


class LichessApiError(Exception):
    """Erreur lors de l'appel à l'API Lichess."""


async def get_opening_moves(fen: str) -> tuple[list[TheoreticalMove], OpeningInfo | None]:
    """
    Interroge l'API Lichess Opening Explorer pour une position donnée.

    Utilise l'endpoint /masters (parties de maîtres) pour obtenir
    les coups théoriques et le nom de l'ouverture.

    Nécessite un token API Lichess dans la config (LICHESS_API_TOKEN).

    Args:
        fen: Position au format FEN.

    Returns:
        Tuple (liste de coups théoriques, infos d'ouverture).

    Raises:
        LichessApiError: si l'API est injoignable, retourne une erreur,
                         ou si le token est manquant.
    """
    token = settings.lichess_api_token.get_secret_value()
    if not token:
        raise LichessApiError(
            "Token API Lichess manquant. "
            "Générez un token sur https://lichess.org/account/oauth/token "
            "et ajoutez LICHESS_API_TOKEN dans le fichier .env"
        )

    url = f"{settings.lichess_api_url}/masters"
    params = {"fen": fen}

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise LichessApiError(
                f"Lichess API a retourné {e.response.status_code}: "
                f"vérifiez votre token et la position FEN"
            ) from e
        except httpx.RequestError as e:
            raise LichessApiError(f"Impossible de joindre l'API Lichess: {e}") from e

    moves = []
    for m in data.get("moves", []):
        moves.append(TheoreticalMove(
            san=m["san"],
            uci=m["uci"],
            white=m.get("white", 0),
            draws=m.get("draws", 0),
            black=m.get("black", 0),
            average_rating=m.get("averageRating", 0),
        ))

    opening = None
    if data.get("opening"):
        opening = OpeningInfo(
            name=data["opening"].get("name"),
            eco=data["opening"].get("eco"),
        )

    return moves, opening
