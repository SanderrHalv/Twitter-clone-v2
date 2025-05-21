# app/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class Account(Base):
    __tablename__ = "accounts"

    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email    = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ─── Relationships ──────────────────────────────────────────────────────────
    tweets = relationship(
        "Tweet",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    likes = relationship(
        "Like",
        back_populates="user",
        cascade="all, delete-orphan",
    )

class Tweet(Base):
    __tablename__ = "tweets"

    id         = Column(Integer, primary_key=True, index=True)
    content    = Column(String, nullable=False)
    user_id    = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ─── Relationships ──────────────────────────────────────────────────────────
    user  = relationship(
        "Account",
        back_populates="tweets",
    )
    likes = relationship(
        "Like",
        back_populates="tweet",
        cascade="all, delete-orphan",
    )

class Like(Base):
    __tablename__ = "likes"

    id         = Column(Integer, primary_key=True, index=True)
    tweet_id   = Column(Integer, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False)
    user_id    = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ensure one like per user per tweet
    __table_args__ = (
        UniqueConstraint("tweet_id", "user_id", name="uix_tweet_user"),
    )

    # ─── Relationships ──────────────────────────────────────────────────────────
    tweet = relationship(
        "Tweet",
        back_populates="likes",
    )
    user  = relationship(
        "Account",
        back_populates="likes",
    )
