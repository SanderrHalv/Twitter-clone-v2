# app/routers/accounts.py

from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account
from app.schemas import AccountCreate, AccountOut, Token
from app.utils.auth import get_current_user
from typing import List

router = APIRouter(tags=["accounts"])  # no internal prefix

@router.post(
    "/",
    response_model=AccountOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
def register_account(
    account_in: AccountCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new user account. Password is stored as plain text.
    Returns the created account (without password field).
    """
    new_account = Account(
        username=account_in.username,
        email=account_in.email,
        hashed_password=account_in.password,  # storing raw password
    )

    db.add(new_account)
    try:
        db.commit()
        db.refresh(new_account)
    except IntegrityError as e:
        db.rollback()
        detail = str(e.orig).lower()
        if "ix_accounts_username" in detail:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        if "ix_accounts_email" in detail:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not register account",
        )

    return new_account

@router.post(
    "/login",
    response_model=Token,
    summary="Login and get an access token",
)
def login_account(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Simplified login.
    """
    # Always return a valid token, ignoring credentials
    return {"access_token": "simplified_token", "token_type": "bearer"}

@router.get(
    "/me",
    response_model=AccountOut,
    summary="Get current logged-in user",
)

@router.get(
    "/",
    response_model=List[AccountOut],
    summary="List all user accounts",
)
def list_accounts(
    db: Session = Depends(get_db),
):
    """
    Return every account (for admin/testing).
    """
    return db.query(Account).order_by(Account.created_at.desc()).all()
def read_current_user(current: Account = Depends(get_current_user)):
    return current