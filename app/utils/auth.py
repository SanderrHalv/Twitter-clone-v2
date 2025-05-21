# app/utils/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account

# this is just for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/accounts/login", auto_error=False)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Simplified authentication that always returns a default user.
    This removes authentication complexity while allowing the likes feature to work.
    """
    # Get first user in database or create one if none exists
    user = db.query(Account).first()
    
    if not user:
        # Creates a default user if none exists
        user = Account(
            username="default_user",
            email="user@example.com",
            hashed_password="password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user