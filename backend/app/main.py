from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.healthcheck import router as healthcheck_router
from app.api.moves import router as moves_router
from app.api.evaluate import router as evaluate_router
from app.api.advice import router as advice_router
from app.api.vector_search import router as vector_search_router

app = FastAPI(
    title="Chess Agent API",
    description="Agent IA pour l'apprentissage des ouvertures d'échecs - FFE",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(healthcheck_router, prefix="/api/v1")
app.include_router(moves_router, prefix="/api/v1")
app.include_router(evaluate_router, prefix="/api/v1")
app.include_router(advice_router, prefix="/api/v1")
app.include_router(vector_search_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Chess Agent API - FFE"}
