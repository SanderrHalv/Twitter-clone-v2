from fastapi import APIRouter, HTTPException, Depends, status
from typing import List

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tweet, TweetCreate, TweetUpdate, Like
from app.cache import (
    get_tweet_cache,
    set_tweet_cache,
    invalidate_tweet_cache,
    get_recent_tweets,
)
from app.like_batcher import like_batcher
from app.utils.auth import get_current_user

router = APIRouter(
    prefix="/tweets",
    tags=["tweets"],
)


@router.post("/", response_model=Tweet, status_code=status.HTTP_201_CREATED)
async def create_tweet(
    payload: TweetCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Persist the new tweet in the database
    db_tweet = Tweet(content=payload.content, account_id=user.id)
    db.add(db_tweet)
    db.commit()
    db.refresh(db_tweet)

    # Cache the newly created tweet
    await set_tweet_cache(db_tweet)  # so next read is served from Redis
    return db_tweet  # return full tweet including generated ID & timestamps


@router.get("/{tweet_id}", response_model=Tweet)
async def read_tweet(tweet_id: int, db: Session = Depends(get_db)):
    # Try Redis cache first to reduce DB load
    cached = await get_tweet_cache(tweet_id)
    if cached:
        return cached  # hit: return the hash from Redis

    # Cache miss: fetch from DB
    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id).one_or_none()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    # Populate cache for future requests
    await set_tweet_cache(db_tweet)
    return db_tweet


@router.put("/{tweet_id}", response_model=Tweet)
async def update_tweet(
    tweet_id: int,
    payload: TweetUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Ensure tweet exists and belongs to the current user
    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id, Tweet.account_id == user.id).one_or_none()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found or unauthorized")

    # Apply updates and commit
    db_tweet.content = payload.content
    db.commit()
    db.refresh(db_tweet)

    # Update cache with new content
    await set_tweet_cache(db_tweet)
    return db_tweet


@router.delete("/{tweet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Ensure tweet exists and belongs to the current user
    db_tweet = db.query(Tweet).filter(Tweet.id == tweet_id, Tweet.account_id == user.id).one_or_none()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found or unauthorized")

    # Delete from DB
    db.delete(db_tweet)
    db.commit()

    # Invalidate cache so stale data isn’t served
    await invalidate_tweet_cache(tweet_id)
    return None  # 204 No Content has no response body


@router.get("/", response_model=List[Tweet])
async def list_recent_tweets(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    # Attempt to serve from Redis sorted set
    tweets = await get_recent_tweets(skip=skip, limit=limit)
    if tweets:
        return tweets  # hitting cache pages

    # Fallback: query DB, order by creation time descending
    db_tweets = (
        db.query(Tweet)
        .order_by(Tweet.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Cache each one for next time
    for t in db_tweets:
        await set_tweet_cache(t)
    return db_tweets


@router.post("/{tweet_id}/like", status_code=status.HTTP_200_OK)
async def like_tweet(
    tweet_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Ensure tweet exists
    if not db.query(Tweet).filter(Tweet.id == tweet_id).first():
        raise HTTPException(status_code=404, detail="Tweet not found")

    # Record like in-memory; DB update happens in the background batcher
    await like_batcher.add_like(tweet_id)
    return {"message": "Like queued for batch processing"}


@router.get("/search/", response_model=List[Tweet])
async def search_tweets(
    q: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    # Simple substring search in DB (could be replaced/swapped with full-text)
    db_tweets = (
        db.query(Tweet)
        .filter(Tweet.content.ilike(f"%{q}%"))
        .order_by(Tweet.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Cache results for quick follow-up reads
    for t in db_tweets:
        await set_tweet_cache(t)
    return db_tweets
