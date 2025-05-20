from pydantic import BaseModel
from datetime import datetime

# ----------- Account Schemas -----------

class AccountBase(BaseModel):
    username: str
    email: str

class AccountCreate(AccountBase):
    pass

class Account(AccountBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# ----------- Tweet Schemas -----------

class TweetBase(BaseModel):
    content: str

class TweetCreate(TweetBase):
    pass

class Tweet(TweetBase):
    id: int
    account_id: int
    created_at: datetime

    class Config:
        from_attributes = True  # This replaces orm_mode = True
