from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt
from datetime import timedelta, datetime

from app.database import get_db
from app.models import Account
from app.schemas import AccountCreate, AccountOut, LoginRequest, Token
from app.utils.settings import settings
from app.utils.auth import get_current_user  # <-- import this for `/me`

router = APIRouter(
    tags=["accounts"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

@router.post("/", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def register_account(payload: AccountCreate, db: Session = Depends(get_db)):
    # Check for duplicate username/email
    exists = (
        db.query(Account)
        .filter((Account.username == payload.username) | (Account.email == payload.email))
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    user = Account(
        username=payload.username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login_account(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Account).filter(Account.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=AccountOut)
def read_current_user(user: Account = Depends(get_current_user)):
    return user
