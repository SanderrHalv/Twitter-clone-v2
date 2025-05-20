import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.database import Base, engine                 # SQLAlchemy Base & engine for DB setup
from app import models                                 # ensure models are registered before table creation
from app.routers import accounts, tweets                # core account & tweet endpoints
from app.cache import init_cache, close_cache           # Redis cache init/teardown
from app.like_batcher import like_batcher               # background batcher for likes
from app.logging_config import setup_logging            # structured logging setup

# ----------------------------------------------------------------
# DATABASE MIGRATIONS
# ----------------------------------------------------------------
# Automatically create any missing tables on startup.
# This ensures your new DB-cache and like-batcher can use the same schema.
models.Base.metadata.create_all(bind=engine)

# ----------------------------------------------------------------
# LOGGING
# ----------------------------------------------------------------
# Initialize structured logging (JSON format, request tracing, etc.)
# before the app is instantiated so all logs—including startup—
# use the correct handlers and format.
setup_logging()

# ----------------------------------------------------------------
# FASTAPI APP SETUP
# ----------------------------------------------------------------
app = FastAPI(title="Twitter Clone API with A2 enhancements")

# Compress large responses to save bandwidth.
# Only responses >1 KB are gzipped to avoid overhead on small payloads.
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Enable CORS for development/demo; tighten to specific origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # TODO: restrict to your front-end domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register your routers for account & tweet functionality
app.include_router(accounts.router)  # register /accounts/*
app.include_router(tweets.router)    # register /tweets/*

# ----------------------------------------------------------------
# LIFECYCLE EVENTS
# ----------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    # Initialize the Redis client pool and any DB-cache prep
    await init_cache()
    logging.info("Redis cache initialized")

    # Start background like-batcher thread/task for batching like writes
    app.state.like_batcher = like_batcher
    like_batcher.start()
    logging.info("Like-batcher started")

@app.on_event("shutdown")
async def on_shutdown():
    # Flush any pending like events to the DB so none are lost
    await app.state.like_batcher.flush()
    logging.info("Flushed remaining likes on shutdown")

    # Gracefully close Redis connections
    await close_cache()
    logging.info("Redis cache connection closed")

# ----------------------------------------------------------------
# BASIC ENDPOINTS
# ----------------------------------------------------------------
@app.get("/")
def read_root():
    # Simple root message for sanity checks
    return {"message": "Welcome to the Twitter Clone API"}

@app.get("/health")
def health_check():
    # Health-check endpoint for load balancer / orchestrator
    return {"status": "ok"}
