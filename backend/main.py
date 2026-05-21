import os
import sys

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from database import engine, Base
from websocket import manager

# Allow tests to override the database engine
_db_engine = engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=_db_engine)
    yield


app = FastAPI(title="Agent Coop", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from routers import health, rooms, members, join, messages, webhooks, locks, agent_status, websocket

app.include_router(health.router)
app.include_router(rooms.router)
app.include_router(join.router)
app.include_router(members.router)
app.include_router(messages.router)
app.include_router(webhooks.router)
app.include_router(locks.router)
app.include_router(agent_status.router)
app.include_router(websocket.router)

# Static files (Frontend)
FRONTEND_BUILD = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist"
)

if os.path.isdir(FRONTEND_BUILD):
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
