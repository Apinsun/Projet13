from typing import TypedDict


class AgentState(TypedDict):
    """État partagé du graphe LangGraph."""

    # Entrée
    fen: str

    # Résultat Lichess
    lichess_moves: list[dict]
    lichess_opening: dict | None

    # Résultat Stockfish (seulement si position non-théorique)
    stockfish_score: int | None
    stockfish_mate: int | None
    stockfish_best_move: str | None

    # Décision
    is_theoretical: bool

    # Résultat RAG (Milvus / WikiChess)
    rag_context: str | None

    # Résultat final
    response: str
    error: str | None
