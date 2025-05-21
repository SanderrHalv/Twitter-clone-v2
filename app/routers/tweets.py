from fastapi import APIRouter, HTTPException, Depends, status
from typing import List

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tweet as TweetModel
from app.schemas import TweetCreate, TweetUpdate, TweetOut
from app.cache import (
    get_tweet_cache,
    set_tweet_cache,
    invalidate_tweet_cache,
    get_recent_tweets,
)
from app.like_batcher import like_batcher
from app.utils.auth import get_current_user
from app.schemas import AccountCreate, AccountOut, Token


router = APIRouter(
    prefix="/tweets",
    tags=["tweets"],
)


@router.post("/", response_model=TweetOut, status_code=status.HTTP_201_CREATED)
async def create_tweet(
    payload: TweetCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_tweet = TweetModel(content=payload.content, account_id=user.id)
    db.add(db_tweet)
    db.commit()
    db.refresh(db_tweet)

    await set_tweet_cache(db_tweet)
    return db_tweet


@router.get("/{tweet_id}", response_model=TweetOut)
async def read_tweet(tweet_id: int, db: Session = Depends(get_db)):
    cached = await get_tweet_cache(tweet_id)
    if cached:
        return cached

    db_tweet = db.query(TweetModel).filter(TweetModel.id == tweet_id).one_or_none()
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    await set_tweet_cache(db_tweet)
    return db_tweet


@router.put("/{tweet_id}", response_model=TweetOut)
async def update_tweet(
    tweet_id: int,
    payload: TweetUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_tweet = (
        db.query(TweetModel)
        .filter(TweetModel.id == tweet_id, TweetModel.account_id == user.id)
        .one_or_none()
    )
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found or unauthorized")

    db_tweet.content = payload.content
    db.commit()
    db.refresh(db_tweet)

    await set_tweet_cache(db_tweet)
    return db_tweet


@router.delete("/{tweet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_tweet = (
        db.query(TweetModel)
        .filter(TweetModel.id == tweet_id, TweetModel.account_id == user.id)
        .one_or_none()
    )
    if not db_tweet:
        raise HTTPException(status_code=404, detail="Tweet not found or unauthorized")

    db.delete(db_tweet)
    db.commit()

    await invalidate_tweet_cache(tweet_id)
    return None


@router.get("/", response_model=List[TweetOut])
async def list_recent_tweets(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    tweets = await get_recent_tweets(skip=skip, limit=limit)
    if tweets:
        return tweets

    db_tweets = (
        db.query(TweetModel)
        .order_by(TweetModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    for t in db_tweets:
        await set_tweet_cache(t)
    return db_tweets


@router.post("/{tweet_id}/like", status_code=status.HTTP_200_OK)
async def like_tweet(
    tweet_id: int,
    user=Depends(get_current_user),
):
    await like_batcher.add_like(tweet_id)
    return {"message": "Like queued for batch processing"}


@router.get("/search/", response_model=List[TweetOut])
async def search_tweets(
    q: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    db_tweets = (
        db.query(TweetModel)
        .filter(TweetModel.content.ilike(f"%{q}%"))
        .order_by(TweetModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    for t in db_tweets:
        await set_tweet_cache(t)
    return db_tweets
