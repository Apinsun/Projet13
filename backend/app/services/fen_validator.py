import chess


class InvalidFenError(ValueError):
    """Levée lorsqu'un FEN est invalide."""

    def __init__(self, fen: str, reason: str = "Format FEN invalide"):
        self.fen = fen
        self.reason = reason
        super().__init__(f"FEN invalide '{fen}': {reason}")


def validate_fen(fen: str) -> chess.Board:
    """
    Valide une chaîne FEN et retourne l'objet Board python-chess.

    Raises:
        InvalidFenError: si le FEN est syntaxiquement ou sémantiquement invalide.
    """
    try:
        board = chess.Board(fen)
    except ValueError as e:
        raise InvalidFenError(fen, str(e)) from e

    # Vérifications supplémentaires : le board doit être légal
    if not board.is_valid():
        raise InvalidFenError(fen, "La position n'est pas légalement atteignable")

    return board


def fen_to_api_format(fen: str) -> str:
    """
    Convertit un FEN au format utilisé pour l'API Lichess (remplace les espaces par des underscores).
    Utile si l'API nécessite ce format (l'Opening Explorer accepte les deux).
    """
    return fen.replace(" ", "_")
