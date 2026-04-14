"""
Application entry point.

Creates the FastAPI app, mounts API routers, and configures lifespan hooks.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ad_agent import router as ad_agent_router
from app.api.routes.page_agent import router as page_agent_router
from app.api.routes.edit_agent import router as edit_agent_router
from app.api.routes.renderer import router as renderer_router
from app.api.routes.personalize import router as personalize_router
from app.config import settings  # noqa: F401 — validates env on import

logger = logging.getLogger(__name__)

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)


# ── Lifespan ───────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("🚀 Ad Personalizer starting up")
    yield
    logger.info("👋 Ad Personalizer shutting down")


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Ad → Landing-Page Personalizer",
    version="0.1.0",
    description="Personalize any landing page to match an ad creative.",
    lifespan=lifespan,
)

# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(ad_agent_router, prefix="/api/v1")
app.include_router(page_agent_router, prefix="/api/v1")
app.include_router(edit_agent_router, prefix="/api/v1")
app.include_router(renderer_router, prefix="/api/v1")
app.include_router(personalize_router, prefix="/api/v1")

# ── CORS ───────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:3000",   # fallback CRA / Next dev
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Root & Health ──────────────────────────────────────────────────────────────


@app.get("/", tags=["System"])
async def root():
    """Root — verify the service is online."""
    return {
        "service": "Ad Personalizer",
        "description": "AI-powered ad-to-landing-page personalization engine",
        "status": "online",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health check for monitoring tools (Docker, K8s, etc.)."""
    return {"status": "healthy"}


# ── Dev entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
