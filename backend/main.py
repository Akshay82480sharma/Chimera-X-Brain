"""Main FastAPI application entry point for Chimera-X Brain.

This is the ONLY entry point. Run with:
    uvicorn main:app --reload
"""

import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.session import init_db
from app.db.cache import init_redis, close_redis
from app.core.health import health_check_loop
from app.api import chat, providers, history, models, memory, projects, knowledge, stats, prompts, tools, admin, ecc, agents, skills, audio
from app.learning import routes as learning_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_redis()
    health_task = asyncio.create_task(health_check_loop())
    yield
    health_task.cancel()
    await close_redis()

app = FastAPI(
    title="Chimera-X Brain",
    description="Local-first Personal AI Router and Memory System",
    version="1.0.0",
    lifespan=lifespan,
)

# Setup CORS for Next.js frontend
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers — each router defines its own prefix
app.include_router(chat.router)
app.include_router(providers.router)
app.include_router(history.router)
app.include_router(models.router)
app.include_router(memory.router)
app.include_router(projects.router)
app.include_router(knowledge.router)
app.include_router(stats.router)
app.include_router(prompts.router)
app.include_router(tools.router)
app.include_router(admin.router)
app.include_router(ecc.router)
app.include_router(audio.router)
app.include_router(agents.router)
app.include_router(skills.router)
app.include_router(learning_routes.router, prefix="/v1/learning", tags=["learning"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "brain": "Chimera-X is active"}


@app.get("/")
async def root():
    return {
        "app": "Chimera-X Brain",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
