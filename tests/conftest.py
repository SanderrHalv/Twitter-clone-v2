# tests/conftest.py

import sys, os
sys.path.insert(0, os.getcwd())

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database
import app.main as main_app
from app.database import Base, get_db
from app.cache import (
    init_cache, close_cache,
    get_tweet_cache, set_tweet_cache,
    invalidate_tweet_cache, get_recent_tweets,
)
from app.like_batcher import like_batcher

# -- 1) In-memory SQLite engine for tests --
TEST_DATABASE_URL = "sqlite:///:memory:"
_test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

# -- 2) Simple async stubs for cache/batcher (unchanged) --
_tweet_store, _recent_list = {}, []

async def _noop_init_cache(): pass
async def _noop_close_cache(): pass
async def _stub_get_tweet_cache(tweet_id): return _tweet_store.get(tweet_id)
async def _stub_set_tweet_cache(tweet):
    data = {"id": tweet.id, "content": tweet.content,
            "created_at": tweet.created_at.isoformat(),
            "updated_at": tweet.updated_at.isoformat(),
            "account_id": tweet.account_id}
    _tweet_store[tweet.id] = data; _recent_list.insert(0, data)
async def _stub_invalidate_tweet_cache(tweet_id):
    _tweet_store.pop(tweet_id, None)
    global _recent_list
    _recent_list = [t for t in _recent_list if t["id"] != tweet_id]
async def _stub_get_recent_tweets(skip=0, limit=100): return _recent_list[skip:skip+limit]

# -- 3) Swap Postgres engine → SQLite & disable app startup hook --
@pytest.fixture(autouse=True)
def swap_engine_and_disable_startup(monkeypatch):
    # Point both modules at our in-memory engine
    monkeypatch.setattr(app.database, "engine", _test_engine)
    monkeypatch.setattr(main_app, "engine", _test_engine)
    # Remove any on_startup handlers (so they don’t try to re-create on wrong engine)
    main_app.app.router.on_startup.clear()
    yield

# -- 4) Create & drop tables around each test --
@pytest.fixture(autouse=True)
def prepare_db():
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)

# -- 5) Override dependencies (DB, cache, batcher) --
@pytest.fixture(autouse=True)
def override_deps(monkeypatch):
    # A) get_db → our session factory
    def _get_test_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    main_app.app.dependency_overrides[get_db] = _get_test_db

    # B) cache lifecycle
    monkeypatch.setattr("app.cache.init_cache", _noop_init_cache)
    monkeypatch.setattr("app.cache.close_cache", _noop_close_cache)
    # C) cache ops
    monkeypatch.setattr("app.cache.get_tweet_cache", _stub_get_tweet_cache)
    monkeypatch.setattr("app.cache.set_tweet_cache", _stub_set_tweet_cache)
    monkeypatch.setattr("app.cache.invalidate_tweet_cache", _stub_invalidate_tweet_cache)
    monkeypatch.setattr("app.cache.get_recent_tweets", _stub_get_recent_tweets)

    # D) like_batcher immediate
    async def _immediate_like(tweet_id: int):
        db = TestingSessionLocal()
        try:
            t = db.query(main_app.Tweet).get(tweet_id)
            if t:
                t.like_count += 1
                db.commit()
        finally:
            db.close()
    monkeypatch.setattr("app.like_batcher.like_batcher.add_like", _immediate_like)

    yield
    main_app.app.dependency_overrides.clear()

# -- 6) TestClient that defers startup until after tables exist --
@pytest.fixture
def client():
    # Use context manager so startup runs *inside* our prepare_db scope
    with TestClient(main_app.app) as c:
        yield c
