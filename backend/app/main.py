from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.healthcheck import router as healthcheck_router

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


@app.get("/")
async def root():
    return {"message": "Chess Agent API - FFE"}
