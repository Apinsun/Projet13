from pydantic import BaseModel, Field


# ── Lichess / Moves ──────────────────────────────

class TheoreticalMove(BaseModel):
    """Un coup théorique retourné par l'API Lichess."""
    san: str = Field(description="Notation algébrique (ex: e4, Nf3)")
    uci: str = Field(description="Notation UCI (ex: e2e4, g1f3)")
    white: int = Field(description="Parties gagnées par les Blancs (en nombre)")
    draws: int = Field(description="Parties nulles (en nombre)")
    black: int = Field(description="Parties gagnées par les Noirs (en nombre)")
    average_rating: int = Field(default=0, description="Classement Elo moyen des parties")


class OpeningInfo(BaseModel):
    """Informations sur l'ouverture identifiée."""
    name: str | None = Field(default=None, description="Nom de l'ouverture (ex: Sicilian Defense)")
    eco: str | None = Field(default=None, description="Code ECO (ex: B30)")


class MoveResponse(BaseModel):
    """Réponse de l'endpoint /moves/{fen}."""
    fen: str = Field(description="Position FEN analysée")
    opening: OpeningInfo | None = Field(default=None)
    moves: list[TheoreticalMove] = Field(default_factory=list, description="Coups théoriques possibles")


# ── Stockfish / Evaluate ─────────────────────────

class EngineEvaluation(BaseModel):
    """Évaluation d'une position par Stockfish."""
    fen: str = Field(description="Position FEN évaluée")
    score_cp: int | None = Field(default=None, description="Évaluation en centipawns (positif = avantage Blancs)")
    mate_in: int | None = Field(default=None, description="Mat annoncé dans N coups (null si pas de mat)")
    best_move: str | None = Field(default=None, description="Meilleur coup en notation UCI")
    depth: int = Field(default=0, description="Profondeur de recherche")


# ── Erreurs ──────────────────────────────────────

class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée."""
    detail: str = Field(description="Message d'erreur")
    fen: str | None = Field(default=None)
