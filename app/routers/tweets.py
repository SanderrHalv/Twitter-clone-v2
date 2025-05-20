from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import SessionLocal
from pydantic import BaseModel

router = APIRouter(prefix="/tweets", tags=["Tweets"])

# Henter DB dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TweetUpdate(BaseModel):
    content: str

# Oppretter en tweet for en spesifikk konto
@router.post("/{account_id}", response_model=schemas.Tweet)
def create_tweet(account_id: int, tweet: schemas.TweetCreate, db: Session = Depends(get_db)):
    # Sjekker om kontoen eksisterer
    account = crud.get_account_by_id(db, account_id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return crud.create_tweet(db=db, tweet=tweet, account_id=account_id)

# Lister alle tweets
@router.get("/", response_model=list[schemas.Tweet])
def list_tweets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_tweets(db, skip=skip, limit=limit)

# Søker etter tweets med nøkkelord
@router.get("/search/", response_model=list[schemas.Tweet])
def search_tweets(keyword: str, db: Session = Depends(get_db)):
    return crud.search_tweets(db, keyword=keyword)

# Søk tweets med hashtag
@router.get("/hashtags/{tag}", response_model=list[schemas.Tweet])
def search_hashtags(tag: str, db: Session = Depends(get_db)):
    return crud.search_hashtags(db, tag=tag)

# Henter en spesifikk tweet
@router.get("/{tweet_id}", response_model=schemas.Tweet)
def get_tweet(tweet_id: int, db: Session = Depends(get_db)):
    tweet = crud.get_tweet(db, tweet_id=tweet_id)
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    return tweet

# Oppdaterer en tweet
@router.put("/{tweet_id}", response_model=schemas.Tweet)
def update_tweet(tweet_id: int, tweet_update: TweetUpdate, db: Session = Depends(get_db)):
    tweet = crud.update_tweet(db, tweet_id=tweet_id, content=tweet_update.content)
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    return tweet

# Sletter en tweet
@router.delete("/{tweet_id}")
def delete_tweet(tweet_id: int, db: Session = Depends(get_db)):
    success = crud.delete_tweet(db, tweet_id=tweet_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tweet not found")
    return {"detail": "Tweet deleted successfully"}