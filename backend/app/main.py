import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.config import settings
from app.rate_limit import limiter
from app.routers import (
    admin,
    api_keys,
    auth,
    billing,
    communication,
    live_coach_ws,
    live_session_ws,
    marketplace,
    me,
    media,
    notifications,
    organizations,
    parent,
    privacy,
    public_api,
    teacher,
    webhooks,
)
from app.scheduler import start_scheduler, stop_scheduler

# Phase 17: schema is now owned by Alembic migrations, not `create_all` —
# run `alembic upgrade head` before starting the server (see backend
# README's "Running it" section). This is a real behavior change from
# Phases 10-16: a fresh database with no migrations applied now has zero
# tables, on purpose, rather than silently auto-creating them.
os.makedirs(settings.media_root, exist_ok=True)

app = FastAPI(title="HifzAI API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=settings.media_root), name="media")

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(teacher.router)
app.include_router(parent.router)
app.include_router(admin.router)
app.include_router(notifications.router)
app.include_router(organizations.router)
app.include_router(media.router)
app.include_router(live_session_ws.router)
app.include_router(live_coach_ws.router)
app.include_router(communication.router)
app.include_router(marketplace.router)
app.include_router(api_keys.router)
app.include_router(public_api.router)
app.include_router(privacy.router)
app.include_router(webhooks.router)
app.include_router(billing.router)


@app.on_event("startup")
def _on_startup() -> None:
    # Phase 16: daily engagement check + weekly parent digest. See
    # scheduler.py's docstring for why this is in-process (fine for one
    # server, not for a horizontally-scaled deployment).
    start_scheduler()


@app.on_event("shutdown")
def _on_shutdown() -> None:
    stop_scheduler()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
