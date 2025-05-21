# server.py (project root)

import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.database import engine             # for metadata.create_all
from app import models                      # registers ORM models
from app.routers import accounts, tweets
from app.cache import init_cache, close_cache
from app.like_batcher import like_batcher
from app.logging_config import setup_logging

# 1) Logging
setup_logging()

# 2) FastAPI app, with docs/schema under /api
app = FastAPI(
    title="Twitter Clone",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
)

# 3) Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten in prod!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4) Startup / Shutdown hooks
@app.on_event("startup")
async def on_startup():
    # ensure tables exist
    models.Base.metadata.create_all(bind=engine)
    logging.info("DB tables ready")

    # init Redis
    await init_cache()
    logging.info("Cache ready")

    # start like-batcher background thread/task
    app.state.like_batcher = like_batcher
    like_batcher.start()
    logging.info("Like-batcher started")

@app.on_event("shutdown")
async def on_shutdown():
    # flush pending likes
    await app.state.like_batcher.flush()
    logging.info("Likes flushed")

    # close cache
    await close_cache()
    logging.info("Cache closed")

# 5) Static / Frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
async def serve_spa():
    return FileResponse("static/index.html")

# 6) Health check (optional)
@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

# 7) API Routers
#    Each router (“dumb”—no internal prefix) is mounted *once* with its full /api/... path.
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(tweets.router,  prefix="/api/tweets",   tags=["tweets"])
