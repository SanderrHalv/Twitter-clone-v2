from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account
from app.utils.settings import settings
import logging

# OAuth2 scheme: expects Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/accounts/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Dependency to retrieve the current user based on JWT token.
    Raises 401 if token is missing, invalid, or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            logging.warning("JWT payload missing subject")
            raise credentials_exception
    except JWTError:
        logging.warning("JWT decode error", exc_info=True)
        raise credentials_exception

    user = db.query(Account).filter(Account.id == int(user_id)).one_or_none()
    if user is None:
        logging.warning(f"User not found for ID: {user_id}")
        raise credentials_exception

    logging.debug(f"Authenticated user: {user.username}")
    return user
