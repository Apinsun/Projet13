from fastapi import APIRouter, Query
from app.models.chess import VideoResponse
from app.services.youtube_service import search_videos

router = APIRouter(tags=["Videos"])


@router.get("/videos/{opening}", response_model=VideoResponse)
async def get_videos(opening: str, top_k: int = Query(default=3, ge=1, le=5)):
    """
    Retourne des vidéos YouTube pertinentes pour une ouverture.

    Utilise un cache MongoDB (24h) puis l'API YouTube Data v3.
    En cas d'échec (quota dépassé, réseau), des liens de secours sont fournis.

    - **opening** : nom de l'ouverture (ex: Sicilienne, Italienne, Gambit Dame)
    - **top_k** : nombre maximum de vidéos retournées (1-5, défaut 3)
    """
    videos, source = search_videos(opening)
    return VideoResponse(
        opening=opening,
        videos=videos[:top_k],
        source=source,
    )
