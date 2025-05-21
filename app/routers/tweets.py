from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import logging

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tweet as TweetModel
from app.schemas import TweetCreate, TweetUpdate, TweetOut
from app.utils.auth import get_current_user

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