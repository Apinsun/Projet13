"""
Service YouTube : recherche de vidéos avec cache MongoDB et fallback.

Fonctionnement :
1. Vérifie le cache MongoDB (TTL 24h)
2. Si absent, appelle l'API YouTube Data v3
3. Si l'API échoue (quota, réseau), utilise des liens hardcodés
"""

import logging
from datetime import datetime, timezone

from app.config import settings
from app.models.chess import VideoResult

logger = logging.getLogger(__name__)

# Cache TTL : 24 heures
CACHE_TTL_SECONDS = 86_400

# ── Fallback : liens curated par ouverture ──────

FALLBACK_VIDEOS: dict[str, list[dict]] = {
    "sicilienne": [
        {
            "title": "La Défense Sicilienne expliquée simplement",
            "url": "https://www.youtube.com/watch?v=qM4e7g2eWwc",
            "channel": "BlitzStream",
            "duration": "25:00",
            "views": "500k+",
        },
        {
            "title": "Sicilienne Najdorf - Les bases",
            "url": "https://www.youtube.com/watch?v=0Ba2j0FyGPU",
            "channel": "GM Finegold",
            "duration": "45:00",
            "views": "200k+",
        },
    ],
    "italienne": [
        {
            "title": "La Partie Italienne (Giuoco Piano) - Cours complet",
            "url": "https://www.youtube.com/watch?v=4UjAMA5QV4I",
            "channel": "Échecs & Stratégie",
            "duration": "30:00",
            "views": "150k+",
        },
    ],
    "espagnole": [
        {
            "title": "L'Espagnole (Ruy Lopez) - Guide complet",
            "url": "https://www.youtube.com/watch?v=U0h3xRpMqCM",
            "channel": "GM Naroditsky",
            "duration": "40:00",
            "views": "300k+",
        },
    ],
    "française": [
        {
            "title": "La Défense Française expliquée",
            "url": "https://www.youtube.com/watch?v=5h3C5qCqK7A",
            "channel": "Échecs & Stratégie",
            "duration": "20:00",
            "views": "100k+",
        },
    ],
    "caro-kann": [
        {
            "title": "Défense Caro-Kann - Les fondamentaux",
            "url": "https://www.youtube.com/watch?v=rmVEUxLQJ5Q",
            "channel": "BlitzStream",
            "duration": "22:00",
            "views": "120k+",
        },
    ],
    "dame": [
        {
            "title": "Le Gambit Dame expliqué pas à pas",
            "url": "https://www.youtube.com/watch?v=K2dFkPxUsOo",
            "channel": "GM Finegold",
            "duration": "35:00",
            "views": "250k+",
        },
    ],
}

GENERIC_FALLBACK = [
    {
        "title": "Apprendre les ouvertures aux échecs - Guide complet",
        "url": "https://www.youtube.com/watch?v=6IegDENuxUY",
        "channel": "BlitzStream",
        "duration": "30:00",
        "views": "1M+",
    },
]


def _get_mongo():
    """Retourne la connexion MongoDB (import lazy)."""
    from pymongo import MongoClient

    client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
    db = client[settings.mongo_db_name]
    return client, db


def _ensure_ttl_index(db):
    """Crée l'index TTL sur youtube_cache si absent."""
    try:
        from pymongo import ASCENDING
        from pymongo.errors import PyMongoError

        collection = db.youtube_cache
        collection.create_index(
            [("created_at", ASCENDING)],
            expireAfterSeconds=CACHE_TTL_SECONDS,
        )
    except PyMongoError:
        pass  # Index déjà existant ou MongoDB indisponible


def _search_cache(db, opening: str) -> list[dict] | None:
    """Recherche des vidéos en cache pour une ouverture."""
    try:
        from pymongo.errors import PyMongoError

        _ensure_ttl_index(db)
        doc = db.youtube_cache.find_one({"opening": opening.lower()})
        if doc:
            age = datetime.now(timezone.utc).timestamp() - doc["created_at"].replace(tzinfo=timezone.utc).timestamp()
            if age < CACHE_TTL_SECONDS:
                logger.info(f"Cache HIT pour '{opening}' (âge: {age:.0f}s)")
                return doc["videos"]
    except PyMongoError as e:
        logger.warning(f"Cache MongoDB indisponible: {e}")
    return None


def _store_cache(db, opening: str, videos: list[dict]) -> None:
    """Stocke les vidéos dans le cache MongoDB."""
    try:
        from pymongo.errors import PyMongoError

        _ensure_ttl_index(db)
        db.youtube_cache.replace_one(
            {"opening": opening.lower()},
            {
                "opening": opening.lower(),
                "videos": videos,
                "created_at": datetime.now(timezone.utc),
            },
            upsert=True,
        )
        logger.info(f"Cache STORE pour '{opening}' ({len(videos)} vidéos)")
    except PyMongoError as e:
        logger.warning(f"Impossible de stocker dans le cache: {e}")


def _call_youtube_api(opening: str) -> list[dict]:
    """Appelle l'API YouTube Data v3 et retourne les vidéos brutes."""
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    if not settings.youtube_api_key:
        raise ValueError("YOUTUBE_API_KEY non configurée")

    youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)

    query = f"{opening} chess opening tutorial explication"
    logger.info(f"YouTube API: search '{query}'")

    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        videoDuration="medium",  # 4-20 minutes
        order="relevance",
        maxResults=5,
        relevanceLanguage="fr",
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        snippet = item["snippet"]
        videos.append({
            "title": snippet["title"],
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "channel": snippet["channelTitle"],
            "duration": None,  # Nécessite un appel supplémentaire (coûteux en quota)
            "views": None,
        })

    return videos


def _find_fallback(opening: str) -> list[dict]:
    """Trouve le fallback le plus pertinent par mot-clé."""
    query = opening.lower().strip()
    for key, videos in FALLBACK_VIDEOS.items():
        if key in query or query in key:
            return videos
    return GENERIC_FALLBACK


def search_videos(opening: str) -> tuple[list[VideoResult], str]:
    """
    Cherche des vidéos YouTube pour une ouverture.

    Stratégie : cache MongoDB → YouTube API → fallback hardcoded.

    Args:
        opening: Nom de l'ouverture (ex: "Sicilienne", "Italienne").

    Returns:
        Tuple (liste de VideoResult, source).
    """
    client, db = _get_mongo()

    try:
        # 1. Cache MongoDB
        cached = _search_cache(db, opening)
        if cached:
            client.close()
            videos = [VideoResult(**v) for v in cached]
            return videos, "cache"

        # 2. YouTube API
        try:
            raw_videos = _call_youtube_api(opening)
            if raw_videos:
                _store_cache(db, opening, raw_videos)
                client.close()
                videos = [VideoResult(**v) for v in raw_videos]
                return videos, "api"
        except (ValueError, Exception) as e:
            logger.warning(f"YouTube API indisponible pour '{opening}': {e}")

        # 3. Fallback hardcoded
        raw_videos = _find_fallback(opening)
        _store_cache(db, opening, raw_videos)
        client.close()
        videos = [VideoResult(**v) for v in raw_videos]
        return videos, "fallback"

    finally:
        try:
            client.close()
        except Exception:
            pass
