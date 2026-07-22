"""
Graphe LangGraph pour l'agent échecs.

Flow :
    START → validate_fen → fetch_lichess → decide_path
                                               ├── théorique → fetch_milvus → fetch_youtube → format_response
                                               └── non-théorique → fetch_stockfish → format_response
"""

from langgraph.graph import StateGraph, START, END
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.config import settings
from app.services.lichess_service import get_opening_moves, LichessApiError
from app.services.stockfish_service import evaluate_position, StockfishError
from app.services.fen_validator import validate_fen, InvalidFenError
from app.services.milvus_service import search_openings
from app.services.youtube_service import search_videos


# ── Nœuds du graphe ──────────────────────────────


def validate_fen_node(state: AgentState) -> AgentState:
    """Valide le FEN et lève une erreur si invalide."""
    try:
        validate_fen(state["fen"])
        state["error"] = None
    except InvalidFenError as e:
        state["error"] = str(e)
    return state


async def fetch_lichess_node(state: AgentState) -> AgentState:
    """Interroge Lichess pour les coups théoriques."""
    if state.get("error"):
        return state
    try:
        moves, opening = await get_opening_moves(state["fen"])
        state["lichess_moves"] = [
            {"san": m.san, "uci": m.uci, "white": m.white, "draws": m.draws, "black": m.black}
            for m in moves
        ]
        state["lichess_opening"] = opening.model_dump() if opening else None
        state["is_theoretical"] = len(moves) > 0
    except LichessApiError as e:
        state["error"] = str(e)
        state["is_theoretical"] = False
    return state


def fetch_stockfish_node(state: AgentState) -> AgentState:
    """Évalue la position avec Stockfish (position non-théorique)."""
    if state.get("error"):
        return state
    try:
        evaluation = evaluate_position(state["fen"])
        state["stockfish_score"] = evaluation.score_cp
        state["stockfish_mate"] = evaluation.mate_in
        state["stockfish_best_move"] = evaluation.best_move
    except StockfishError as e:
        state["error"] = str(e)
    return state


def fetch_milvus_node(state: AgentState) -> AgentState:
    """Recherche le contexte WikiChess dans Milvus."""
    if state.get("error"):
        return state

    opening = state.get("lichess_opening")
    if not opening or not opening.get("name"):
        state["rag_context"] = None
        return state

    try:
        results = search_openings(opening["name"], top_k=1)
        if results:
            state["rag_context"] = "\n\n".join(r["text"] for r in results)
        else:
            state["rag_context"] = None
    except Exception:
        # Milvus indisponible → on continue sans contexte
        state["rag_context"] = None
    return state


def fetch_youtube_node(state: AgentState) -> AgentState:
    """Recherche des vidéos YouTube sur l'ouverture identifiée."""
    if state.get("error"):
        return state

    opening = state.get("lichess_opening")
    if not opening or not opening.get("name"):
        state["youtube_videos"] = None
        return state

    try:
        videos, source = search_videos(opening["name"])
        state["youtube_videos"] = [v.model_dump() for v in videos]
    except Exception:
        state["youtube_videos"] = None
    return state


def format_response_node(state: AgentState) -> AgentState:
    """Formule une réponse en langage naturel via le LLM (Mistral)."""
    if state.get("error"):
        state["response"] = f"❌ Erreur : {state['error']}"
        return state

    llm = ChatMistralAI(
        model=settings.mistral_model,
        mistral_api_key=settings.mistral_api_key,
        temperature=0.3,
    )

    if state["is_theoretical"] and state["lichess_moves"]:
        prompt = _build_theoretical_prompt(state)
    else:
        prompt = _build_engine_prompt(state)

    messages = [
        SystemMessage(content=(
            "Tu es un coach d'échecs pédagogique pour les jeunes joueurs de la "
            "Fédération Française des Échecs. Tu expliques les ouvertures de façon "
            "claire, encourageante et didactique. Tu réponds en français."
        )),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    state["response"] = response.content
    return state


# ── Fonctions de décision ────────────────────────


def decide_path(state: AgentState) -> str:
    """Aiguillage : position théorique → RAG + YouTube, sinon → Stockfish."""
    if state.get("error"):
        return "format_response"
    if state.get("is_theoretical"):
        return "fetch_milvus"
    return "fetch_stockfish"


# ── Construction des prompts ─────────────────────


def _build_theoretical_prompt(state: AgentState) -> str:
    """Prompt pour une position connue de la théorie."""
    opening = state["lichess_opening"]
    moves = state["lichess_moves"][:5]  # Top 5

    moves_text = "\n".join(
        f"  • {m['san']} ({m['uci']}) — "
        f"Blancs: {m['white']/max(1, m['white']+m['draws']+m['black'])*100:.0f}% victoires "
        f"sur {m['white']+m['draws']+m['black']:,} parties de maîtres"
        for m in moves
    )

    opening_text = f"**{opening['name']}** (ECO {opening['eco']})" if opening else "Position de départ"

    return f"""Position analysée : {state['fen']}
Ouverture identifiée : {opening_text}

Coups théoriques les plus joués :
{moves_text}

📚 Contexte encyclopédique :
{state.get('rag_context') or 'Aucune information complémentaire trouvée.'}

🎥 Vidéos recommandées :
{_format_youtube_for_prompt(state.get('youtube_videos'))}

⚠️ Le contexte ci-dessus est fourni par une recherche automatique et peut concerner
une ouverture voisine mais différente. Vérifie sa pertinence avant de l'utiliser :
si le titre ou le contenu ne correspond PAS à l'ouverture identifiée, IGNORE-LE
complètement et base-toi uniquement sur les coups théoriques.

Explique de façon pédagogique ce que cette ouverture signifie pour un jeune joueur :
- Quel est le plan stratégique ?
- Quel coup est le plus populaire et pourquoi ?
- Y a-t-il un piège classique à connaître ?

Utilise le contexte encyclopédique pour enrichir ta réponse.
Si des vidéos sont disponibles, recommande la plus pertinente en fin de réponse.
Réponds en 4-5 phrases maximum, de façon encourageante."""


def _build_engine_prompt(state: AgentState) -> str:
    """Prompt pour une position hors théorie (évaluée par Stockfish)."""
    score = state.get("stockfish_score")
    mate = state.get("stockfish_mate")
    best_move = state.get("stockfish_best_move")

    if mate is not None:
        eval_text = f"Mat en {abs(mate)} coups (avantage {'Blancs' if mate > 0 else 'Noirs'})"
    elif score is not None:
        side = "Blancs" if score > 0 else "Noirs" if score < 0 else "neutre"
        eval_text = f"{'+' if score > 0 else ''}{score / 100:.2f} pions (léger avantage {side})" if abs(score) < 150 else f"{'+' if score > 0 else ''}{score / 100:.2f} pions (avantage {side})"
    else:
        eval_text = "Indisponible"

    return f"""Position analysée : {state['fen']}

⚠️ Cette position n'a pas été trouvée dans la base de parties de maîtres.
Évaluation Stockfish : {eval_text}
Meilleur coup selon le moteur : {best_move or 'Indisponible'}

Explique au jeune joueur :
- Que signifie cette évaluation ?
- Le coup proposé par Stockfish est-il logique ?
- Que faire quand on sort de la théorie ?

Réponds en 3-4 phrases maximum, rassure le joueur et encourage-le à continuer."""


def _format_youtube_for_prompt(videos: list[dict] | None) -> str:
    """Formate les vidéos pour le prompt LLM."""
    if not videos:
        return "Aucune vidéo disponible."
    lines = []
    for v in videos[:3]:
        duration = f" ({v.get('duration')})" if v.get('duration') else ""
        lines.append(f"  • {v['title']}{duration} — {v['channel']}\n    {v['url']}")
    return "\n".join(lines)


# ── Construction du graphe ────────────────────────


def create_graph() -> StateGraph:
    """Construit et compile le graphe LangGraph."""

    graph = StateGraph(AgentState)

    # Déclaration des nœuds
    graph.add_node("validate_fen", validate_fen_node)
    graph.add_node("fetch_lichess", fetch_lichess_node)
    graph.add_node("fetch_stockfish", fetch_stockfish_node)
    graph.add_node("fetch_milvus", fetch_milvus_node)
    graph.add_node("fetch_youtube", fetch_youtube_node)
    graph.add_node("format_response", format_response_node)

    # Arêtes
    graph.add_edge(START, "validate_fen")
    graph.add_edge("validate_fen", "fetch_lichess")
    graph.add_conditional_edges(
        "fetch_lichess",
        decide_path,
        {
            "fetch_milvus": "fetch_milvus",
            "fetch_stockfish": "fetch_stockfish",
            "format_response": "format_response",
        },
    )
    graph.add_edge("fetch_milvus", "fetch_youtube")
    graph.add_edge("fetch_youtube", "format_response")
    graph.add_edge("fetch_stockfish", "format_response")
    graph.add_edge("format_response", END)

    return graph.compile()
