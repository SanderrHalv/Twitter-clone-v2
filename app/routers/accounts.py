from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt

from app.database import get_db
from app.models import Account, AccountCreate, AccountOut
from app.utils.settings import settings
from app.utils.auth import get_current_user
import logging

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def register_account(payload: AccountCreate, db: Session = Depends(get_db)):
    """
    Register a new user account. Hashes password and stores user.
    """
    # Check for existing username or email
    if db.query(Account).filter((Account.username == payload.username) | (Account.email == payload.email)).first():
        logging.warning(f"Registration attempt with existing username/email: {payload.username}/{payload.email}")
        raise HTTPException(status_code=400, detail="Username or email already registered")

    hashed_pw = pwd_context.hash(payload.password)
    db_user = Account(username=payload.username, email=payload.email, hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    logging.info(f"New user registered: {db_user.username}")
    return db_user

@router.post("/login")
def login_account(payload: AccountCreate, db: Session = Depends(get_db)):
    """
    Authenticate user and return a JWT token.
    """
    user = db.query(Account).filter(Account.username == payload.username).first()
    if not user or not pwd_context.verify(payload.password, user.hashed_password):
        logging.warning(f"Failed login attempt for user: {payload.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create JWT token with expiry
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {"sub": str(user.id)}
    expire = settings.datetime.utcnow() + access_token_expires
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    logging.info(f"User logged in: {user.username}")
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=AccountOut)
def read_current_user(user=Depends(get_current_user)):
    """
    Get the profile of the current authenticated user.
    """
    logging.debug(f"Profile viewed for user: {user.username}")
    return user
