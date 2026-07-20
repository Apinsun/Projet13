from sentence_transformers import SentenceTransformer
from pymilvus import Collection, connections
from app.config import settings

# Modèle et connexion chargés une seule fois au démarrage
_model: SentenceTransformer | None = None
_collection: Collection | None = None
_connected: bool = False


def _ensure_connection():
    global _connected
    if not _connected:
        connections.connect(
            host=settings.milvus_host,
            port=settings.milvus_port,
        )
        _connected = True


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    return _model


def _get_collection() -> Collection:
    global _collection
    _ensure_connection()
    if _collection is None:
        _collection = Collection(name=settings.milvus_collection_name)
        _collection.load()
    return _collection


def search_openings(query: str, top_k: int = 3, min_score: float = 0.5) -> list[dict]:
    """
    Recherche vectorielle dans la base Milvus.

    Args:
        query: Texte de la requête (ex: "Sicilienne Najdorf")
        top_k: Nombre de résultats à retourner.
        min_score: Score minimum de similarité (0 à 1). Les résultats
                   en dessous sont ignorés.

    Returns:
        Liste de {name, text, score}. Liste vide si aucun résultat pertinent.
    """
    model = _get_model()
    collection = _get_collection()

    # Vectoriser la requête (préfixe requis par le modèle E5)
    query_embedding = model.encode(
        [f"query: {query}"],
        normalize_embeddings=True,
    )

    # Recherche
    results = collection.search(
        data=query_embedding.tolist(),
        anns_field="embedding",
        param={"metric_type": "IP", "params": {"nprobe": 4}},
        limit=top_k,
        output_fields=["name", "text"],
    )

    # Formater les résultats (filtrer par score minimum)
    hits = []
    for hit in results[0]:
        if hit.distance >= min_score:
            hits.append({
                "name": hit.entity.get("name"),
                "text": hit.entity.get("text"),
                "score": hit.distance,
            })

    return hits
