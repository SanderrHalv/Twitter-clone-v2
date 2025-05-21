# server.py

import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from sqlalchemy import text
from app.database import engine, Base
from app.routers import accounts, tweets
from app.cache import init_cache, close_cache
from app.like_batcher import like_batcher
from app.logging_config import setup_logging

# Configure JSON logging
setup_logging()

app = FastAPI(
    title="Twitter Clone",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    # 1) Schema migration: add user_id only if missing
    logging.info("Running schema migration: ensuring tweets.user_id exists")
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE tweets "
            "ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES accounts(id);"
        ))
    logging.info("Schema migration complete")

    # 2) Create any missing tables (likes, etc.)
    Base.metadata.create_all(bind=engine)
    logging.info("DB tables ready (migrated)")

    # 3) Init cache
    await init_cache()
    logging.info("Cache ready")

    # 4) Start like batcher
    app.state.like_batcher = like_batcher
    like_batcher.start()
    logging.info("Like-batcher started")

@app.on_event("shutdown")
async def on_shutdown():
    await app.state.like_batcher.flush()
    logging.info("Like-batcher flushed")
    await close_cache()
    logging.info("Cache closed")

# Serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
async def serve_spa():
    return FileResponse("static/index.html")

# Health check
@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

# Mount API routers
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(tweets.router,  prefix="/api/tweets",   tags=["tweets"])
