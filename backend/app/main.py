import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background ingestion worker
    from app.services.ingestion import ingestion_loop

    task = asyncio.create_task(ingestion_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="SFX Repository", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.auth.router import router as auth_router
from app.routers.favorites import router as favorites_router
from app.routers.sounds import router as sounds_router
from app.routers.tags import router as tags_router

app.include_router(auth_router)
app.include_router(sounds_router)
app.include_router(tags_router)
app.include_router(favorites_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
