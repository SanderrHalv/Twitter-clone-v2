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
    summary="List tweets (likes disabled)",
)
def list_tweets(
    db: Session = Depends(get_db),
    current: Account = Depends(get_current_user),
):
    """
    Return all tweets with author username.
    like_count and liked_by_user are always 0/False for now.
    """
    raw = db.query(Tweet).order_by(Tweet.created_at.desc()).all()
    result = []
    for t in raw:
        author = db.query(Account).get(t.user_id)
        result.append({
            "id": t.id,
            "content": t.content,
            "created_at": t.created_at,
            "username": author.username if author else "unknown",
            "like_count": 0,
            "liked_by_user": False,
        })
    return result


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
