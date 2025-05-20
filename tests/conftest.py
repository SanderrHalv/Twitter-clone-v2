import sys
import os

# Ensure the project root directory is on Python’s import path.
sys.path.insert(0, os.getcwd())

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.main as main_app
from app.database import Base
from app.cache import (
    init_cache,
    close_cache,
    get_tweet_cache,
    set_tweet_cache,
    invalidate_tweet_cache,
    get_recent_tweets,
)
from app.like_batcher import like_batcher
import app.routers.accounts as accounts_router
import app.routers.tweets as tweets_router

# ----------------------------------------------------------------
# IN-MEMORY DB SETUP
# ----------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ----------------------------------------------------------------
# STUBBED CACHE
# ----------------------------------------------------------------
_tweet_store = {}
_recent_list = []

async def _noop_init_cache():
    pass

async def _noop_close_cache():
    pass

async def _stub_get_tweet_cache(tweet_id: int):
    return _tweet_store.get(tweet_id)

async def _stub_set_tweet_cache(tweet):
    data = {
        "id": tweet.id,
        "content": tweet.content,
        "created_at": tweet.created_at.isoformat(),
        "updated_at": tweet.updated_at.isoformat(),
        "account_id": tweet.account_id,
    }
    _tweet_store[tweet.id] = data
    _recent_list.insert(0, data)

async def _stub_invalidate_tweet_cache(tweet_id: int):
    _tweet_store.pop(tweet_id, None)
    global _recent_list
    _recent_list = [t for t in _recent_list if t["id"] != tweet_id]

async def _stub_get_recent_tweets(skip: int = 0, limit: int = 100):
    return _recent_list[skip: skip + limit]

# ----------------------------------------------------------------
# OVERRIDE DEPENDENCIES FOR TESTING
# ----------------------------------------------------------------
@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    # 1) Re-create all tables in the in-memory database
    Base.metadata.create_all(bind=engine)

    # 2) Provide a stub get_db dependency for both routers
    def _get_test_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(accounts_router, "get_db", _get_test_db)
    monkeypatch.setattr(tweets_router, "get_db", _get_test_db)

    # 3) Stub out Redis cache lifecycle & operations
    monkeypatch.setattr("app.cache.init_cache", _noop_init_cache)
    monkeypatch.setattr("app.cache.close_cache", _noop_close_cache)
    monkeypatch.setattr("app.cache.get_tweet_cache", _stub_get_tweet_cache)
    monkeypatch.setattr("app.cache.set_tweet_cache", _stub_set_tweet_cache)
    monkeypatch.setattr("app.cache.invalidate_tweet_cache", _stub_invalidate_tweet_cache)
    monkeypatch.setattr("app.cache.get_recent_tweets", _stub_get_recent_tweets)

    # 4) Stub the like_batcher to apply likes immediately
    async def _immediate_add_like(tweet_id: int):
        db = TestingSessionLocal()
        try:
            t = db.query(main_app.Tweet).get(tweet_id)
            if t:
                t.like_count += 1
                db.commit()
        finally:
            db.close()

    monkeypatch.setattr(like_batcher, "add_like", _immediate_add_like)

    yield

@pytest.fixture
def client():
    """
    Provides a FastAPI TestClient with all dependencies overridden
    for isolated, repeatable tests.
    """
    return TestClient(main_app.app)
