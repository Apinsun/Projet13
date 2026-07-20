from fastapi import APIRouter

from app.services.milvus_service import search_openings

router = APIRouter(tags=["Vector Search"])


class SearchRequest:
    """Modèle pour la requête de recherche (utilisé via query params)."""
    pass


@router.get("/vector-search")
async def vector_search(q: str, top_k: int = 3):
    """
    Recherche vectorielle dans la base de connaissances Wikichess.

    Args:
        q: Requête textuelle (ex: "Sicilienne Najdorf")
        top_k: Nombre de résultats (défaut: 3)
    """
    results = search_openings(q, top_k=top_k)
    return {
        "query": q,
        "results": results,
    }
