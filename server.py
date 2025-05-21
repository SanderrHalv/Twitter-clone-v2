# server.py

import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
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
    from sqlalchemy import text
    from app.database import engine, Base

    logging.info("Resetting likes table to match schema…")
    with engine.begin() as conn:
        # Drop only the likes table (so recreate_all will rebuild it)
        conn.execute(text("DROP TABLE IF EXISTS likes;"))
    logging.info("Dropped old likes table (if any)")

    # Now create any missing tables: tweets, accounts, and likes
    Base.metadata.create_all(bind=engine)
    logging.info("DB tables ready (with likes table rebuilt)")

    # …your cache + batcher startup here…

@app.on_event("shutdown")
async def on_shutdown():
    await app.state.like_batcher.flush()
    logging.info("Like-batcher flushed")
    await close_cache()
    logging.info("Cache closed")

# ─── file logging ─────────────────────────────────────────────────
log_file = "app.log"
file_handler = RotatingFileHandler(
    filename=log_file,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=2,             # keep up to 2 old files
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
)
file_handler.setFormatter(file_formatter)
# attach to root logger
logging.getLogger().addHandler(file_handler)

# ─── Request logging middleware ──────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request, call_next):
    logger = logging.getLogger("requests")
    logger.info(f"Received {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Responded {response.status_code} to {request.method} {request.url.path}")
    return response

# ─── Logs endpoint ───────────────────────────────────────────────────────────
@app.get("/logs", response_class=PlainTextResponse, summary="Fetch the application log")
def get_logs():
    """
    Returns the contents of the application log file.
    """
    try:
        with open(log_file, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Log file not found.\n"

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
