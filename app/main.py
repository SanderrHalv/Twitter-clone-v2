import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.database import engine             # bring in engine definition only
from app import models                      # register ORM models (no create_all here)
from app.routers import accounts, tweets
from app.cache import init_cache, close_cache
from app.like_batcher import like_batcher
from app.logging_config import setup_logging

# ----------------------------------------------------------------
# LOGGING SETUP
# ----------------------------------------------------------------
# Initialize structured logging before anything else
setup_logging()

# ----------------------------------------------------------------
# FASTAPI APP INITIALIZATION
# ----------------------------------------------------------------
app = FastAPI(title="Twitter Clone API with A2 enhancements")

# Compress large responses (>1KB) to save bandwidth
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Allow CORS for all origins (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(accounts.router)  # /accounts endpoints
app.include_router(tweets.router)    # /tweets endpoints

# ----------------------------------------------------------------
# LIFECYCLE: STARTUP & SHUTDOWN
# ----------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    # 1) Ensure DB tables exist (moved here so import never triggers a DB call)
    models.Base.metadata.create_all(bind=engine)
    logging.info("Database tables created/verified on startup")

    # 2) Initialize Redis cache
    await init_cache()
    logging.info("Redis cache initialized")

    # 3) Start like-batcher background task
    app.state.like_batcher = like_batcher
    like_batcher.start()
    logging.info("Like-batcher started")

@app.on_event("shutdown")
async def on_shutdown():
    # Flush any pending likes
    await app.state.like_batcher.flush()
    logging.info("Flushed batched likes on shutdown")

    # Close Redis connections
    await close_cache()
    logging.info("Redis cache connection closed")

# ----------------------------------------------------------------
# SIMPLE ENDPOINTS
# ----------------------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "Welcome to the Twitter Clone API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
