from sqlalchemy.orm import Session
from sqlalchemy import desc
from . import models, schemas
from datetime import datetime, timezone

# Account operations
def get_account_by_id(db: Session, account_id: int):
    return db.query(models.Account).filter(models.Account.id == account_id).first()

def get_account_by_username(db: Session, username: str):
    return db.query(models.Account).filter(models.Account.username == username).first()

def get_account_by_email(db: Session, email: str):
    return db.query(models.Account).filter(models.Account.email == email).first()

def get_accounts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Account).offset(skip).limit(limit).all()

def create_account(db: Session, account: schemas.AccountCreate):
    db_account = models.Account(username=account.username, email=account.email)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

def search_accounts(db: Session, query: str):
    return db.query(models.Account).filter(models.Account.username.ilike(f"%{query}%")).all()

# Tweet operations
def get_tweet(db: Session, tweet_id: int):
    return db.query(models.Tweet).filter(models.Tweet.id == tweet_id).first()

def get_tweets(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Tweet).order_by(desc(models.Tweet.created_at)).offset(skip).limit(limit).all()

def create_tweet(db: Session, tweet: schemas.TweetCreate, account_id: int):
    db_tweet = models.Tweet(content=tweet.content, account_id=account_id)
    db.add(db_tweet)
    db.commit()
    db.refresh(db_tweet)
    return db_tweet

def update_tweet(db: Session, tweet_id: int, content: str):
    db_tweet = db.query(models.Tweet).filter(models.Tweet.id == tweet_id).first()
    if db_tweet:
        db_tweet.content = content
        db_tweet.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_tweet)
    return db_tweet

def delete_tweet(db: Session, tweet_id: int):
    db_tweet = db.query(models.Tweet).filter(models.Tweet.id == tweet_id).first()
    if db_tweet:
        db.delete(db_tweet)
        db.commit()
        return True
    return False

def search_tweets(db: Session, keyword: str):
    return db.query(models.Tweet).filter(models.Tweet.content.ilike(f"%{keyword}%")).all()

def search_hashtags(db: Session, tag: str):
    return db.query(models.Tweet).filter(models.Tweet.content.ilike(f"%#{tag}%")).all()