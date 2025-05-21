from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import logging

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tweet as TweetModel, Account, Like
from app.schemas import TweetCreate, TweetUpdate, TweetOut
from app.utils.auth import get_current_user

from sqlalchemy.exc import IntegrityError

router = APIRouter(tags=["tweets"])  # no internal prefix

@router.get("/", response_model=List[TweetOut])
async def list_recent_tweets(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    Simple implementation that bypasses cache for debugging.
    """
    try:
        # Simple direct database query without cache
        db_tweets = (
            db.query(TweetModel)
            .order_by(TweetModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return db_tweets
    except Exception as e:
        # Log the actual error for debugging
        logging.error(f"Error fetching tweets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.post("/", response_model=TweetOut, status_code=status.HTTP_201_CREATED)
async def create_tweet(
    payload: TweetCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Simplified tweet creation without cache for debugging
    """
    try:
        db_tweet = TweetModel(content=payload.content, account_id=user.id)
        db.add(db_tweet)
        db.commit()
        db.refresh(db_tweet)
        return db_tweet
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating tweet: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tweet: {str(e)}"
        )

@router.post("/{tweet_id}/like", summary="Like a tweet")
def like_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    current: Account = Depends(get_current_user),
):
    # ensure tweet exists
    tweet = db.query(TweetModel).filter_by(id=tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    # try to add a like
    like = Like(tweet_id=tweet_id, user_id=current.id)
    db.add(like)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # already liked
        raise HTTPException(status_code=400, detail="Already liked")
    return {"detail": "Liked"}

@router.delete("/{tweet_id}/like", summary="Unlike a tweet")
def unlike_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    current: Account = Depends(get_current_user),
):
    like = db.query(Like).filter_by(tweet_id=tweet_id, user_id=current.id).first()
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    db.delete(like)
    db.commit()
    return {"detail": "Unliked"}

# Update your GET /tweets/ endpoint to include a flag:
@router.get("/", summary="List tweets with like info")
def list_tweets(
    db: Session = Depends(get_db),
    current: Account = Depends(get_current_user),
):
    tweets = db.query(TweetModel).order_by(TweetModel.created_at.desc()).all()
    result = []
    for t in tweets:
        result.append({
            "id": t.id,
            "content": t.content,
            "created_at": t.created_at,
            "username": t.user.username,
            "like_count": len(t.likes),
            "liked_by_user": any(l.user_id == current.id for l in t.likes),
        })
    return result