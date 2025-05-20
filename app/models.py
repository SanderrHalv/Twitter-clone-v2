from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    func,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.database import Base

# ----------------------------------------------------------------
# ORM MODELS
# ----------------------------------------------------------------

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)   # fast lookups
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tweets = relationship("Tweet", back_populates="author")  # 1–M link
    likes = relationship("Like", back_populates="tweet")    # 1–M via Like.tweet

class Tweet(Base):
    __tablename__ = "tweets"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)  # allow longer tweets
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)

    author = relationship("Account", back_populates="tweets")
    like_count = Column(Integer, default=0, nullable=False)  # persisted count for display
    __table_args__ = (UniqueConstraint('id', name='uq_tweet_id'),)

class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id"), nullable=False, index=True)
    count = Column(Integer, default=0, nullable=False)  # aggregated like count
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tweet = relationship("Tweet", back_populates="likes")


# ----------------------------------------------------------------
# Pydantic SCHEMAS
# ----------------------------------------------------------------

class AccountCreate(BaseModel):
    username: str
    email: EmailStr
    password: str  # write-only

class AccountOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True  # allow ORM objects to be returned directly

class TweetCreate(BaseModel):
    content: str

class TweetUpdate(BaseModel):
    content: str

class Tweet(BaseModel):
    id: int
    content: str
    created_at: datetime
    updated_at: datetime
    account_id: int
    like_count: int

    class Config:
        orm_mode = True
