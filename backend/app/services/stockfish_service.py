from stockfish import Stockfish
from app.config import settings
from app.models.chess import EngineEvaluation


class StockfishError(Exception):
    """Erreur lors de l'évaluation par Stockfish."""


def _get_engine() -> Stockfish:
    """Crée une instance Stockfish configurée."""
    engine = Stockfish(
        path=settings.stockfish_path,
        parameters={
            "Threads": 2,
            "Hash": 64,
        },
    )
    # Initialise l'engine avec la position de départ (démarre le processus)
    engine.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    return engine


def evaluate_position(fen: str, depth: int = 15) -> EngineEvaluation:
    """
    Évalue une position avec Stockfish.

    Args:
        fen: Position au format FEN.
        depth: Profondeur de recherche (défaut 15).

    Returns:
        EngineEvaluation avec score et meilleur coup.

    Raises:
        StockfishError: si Stockfish n'est pas disponible ou échoue.
    """
    try:
        engine = _get_engine()
        engine.set_fen_position(fen)

        evaluation = engine.get_evaluation()
        best_move = engine.get_best_move()

        score_cp = None
        mate_in = None

        if evaluation["type"] == "cp":
            score_cp = evaluation["value"]
        elif evaluation["type"] == "mate":
            mate_in = evaluation["value"]

        return EngineEvaluation(
            fen=fen,
            score_cp=score_cp,
            mate_in=mate_in,
            best_move=best_move,
            depth=depth,
        )

    except Exception as e:
        raise StockfishError(f"Erreur Stockfish: {e}") from e
