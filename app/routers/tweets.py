# app/routers/tweets.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tweet, Like, Account
from app.schemas import TweetCreate, TweetOut
from app.utils.auth import get_current_user

router = APIRouter(tags=["tweets"])


@router.get(
    "/",
    response_model=List[TweetOut],
    summary="List tweets with like info",
)
def list_tweets(
    db: Session = Depends(get_db),
    current: Account = Depends(get_current_user),
):
    raw_tweets = db.query(Tweet).order_by(Tweet.created_at.desc()).all()

    result = []
    for t in raw_tweets:
        # Lookup the author’s username via the Account model
        author = db.query(Account).get(t.user_id)
        username = author.username if author else "unknown"

        result.append({
            "id": t.id,
            "content": t.content,
            "created_at": t.created_at,
            "username": username,
            "like_count": len(t.likes),
            "liked_by_user": any(l.user_id == current.id for l in t.likes),
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
    new_tweet = Tweet(
        content=tweet_in.content,
        user_id=current.id,
    )
    db.add(new_tweet)
    db.commit()
    db.refresh(new_tweet)

    return {
        "id": new_tweet.id,
        "content": new_tweet.content,
        "created_at": new_tweet.created_at,
        "username": current.username,
        "like_count": 0,
        "liked_by_user": False,
    }


@router.post(
    "/{tweet_id}/like",
    summary="Like a tweet",
    status_code=status.HTTP_200_OK,
)
def like_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    current: Account = Depends(get_current_user),
):
    tweet = db.query(Tweet).get(tweet_id)
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    like = Like(tweet_id=tweet_id, user_id=current.id)
    db.add(like)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Already liked")
    return {"detail": "Liked"}


@router.delete(
    "/{tweet_id}/like",
    summary="Unlike a tweet",
    status_code=status.HTTP_200_OK,
)
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
