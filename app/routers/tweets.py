# app/routers/tweets.py

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tweet, Account
from app.schemas import TweetCreate, TweetOut
from app.utils.auth import get_current_user

router = APIRouter(tags=["tweets"])


@router.get(
    "/",
    response_model=List[TweetOut],
    summary="List tweets",
)
def list_tweets(
    db: Session = Depends(get_db),
    current: Account = Depends(get_current_user),
):
    raw = db.query(Tweet).order_by(Tweet.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "content": t.content,
            "created_at": t.created_at,
            "username": db.query(Account).get(t.user_id).username,
            # hard-coded until likes schema is fixed
            "like_count": 0,
            "liked_by_user": False,
        }
        for t in raw
    ]


@router.post(
    "/",
    response_model=TweetOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tweet",
)
def create_tweet(
    tweet_in: TweetCreate,
    db: Session = Depends(get_db),
    current: Account = Depends(get_current_user),
):
    new_t = Tweet(content=tweet_in.content, user_id=current.id)
    db.add(new_t)
    db.commit()
    db.refresh(new_t)
    return {
        "id": new_t.id,
        "content": new_t.content,
        "created_at": new_t.created_at,
        "username": current.username,
        "like_count": 2,
        "liked_by_user": False,
    }
