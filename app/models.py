from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base  # Base should be the declarative base from your database setup

# ----------------------------------------------------------------
# ORM MODELS
# ----------------------------------------------------------------

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tweets = relationship("Tweet", back_populates="author")
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")  # Fixed: back_populates "account" (see Like.account)

class Tweet(Base):
    __tablename__ = "tweets"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)

    author = relationship("Account", back_populates="tweets")
    likes = relationship("Like", back_populates="tweet", cascade="all, delete-orphan") # Added: relationship to Like
    like_count = Column(Integer, default=0, nullable=False)

    __table_args__ = (UniqueConstraint('id', name='uq_tweet_id'),)  # (Optional: this is redundant since id is PK)

class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False)
    user_id  = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ensure one like per user per tweet
    __table_args__ = (UniqueConstraint("tweet_id", "user_id", name="uix_tweet_user"),)

    # relationships
    tweet = relationship("Tweet", back_populates="likes")
    user  = relationship("Account", back_populates="likes")
