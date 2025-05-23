# app/schemas.py

from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import List, Optional


# --- Account Schemas ---

class AccountCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class AccountOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Tweet Schemas ---

class TweetCreate(BaseModel):
    content: str

class TweetUpdate(BaseModel):
    content: str

class TweetOut(BaseModel):
    id: int
    content: str
    created_at: datetime
    username: str
    like_count: int
    liked_by_user: bool

    model_config = ConfigDict(from_attributes=True)