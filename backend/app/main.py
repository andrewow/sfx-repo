import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


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

app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key, https_only=True)


@app.middleware("http")
async def force_https_scheme(request, call_next):
    """Render terminates TLS at the proxy, so the app sees http://.
    Fix the scheme so url_for() generates https:// URLs."""
    if request.headers.get("x-forwarded-proto") == "https":
        request.scope["scheme"] = "https"
    return await call_next(request)


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


# Serve frontend static files — must be after API routes
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the React SPA for any non-API route."""
        file_path = STATIC_DIR / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
