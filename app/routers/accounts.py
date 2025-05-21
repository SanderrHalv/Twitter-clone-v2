# app/routers/accounts.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account
from app.schemas import AccountCreate, AccountOut, Token
from app.utils.auth import get_current_user

# Router without internal prefix
router = APIRouter(tags=["accounts"])

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
    Create a new user account. Password is stored as-is (no hashing).
    Returns the created account (without password field).
    """
    # Build the ORM object using raw password
    new_account = Account(
        username=account_in.username,
        email=account_in.email,
        hashed_password=account_in.password,  # storing as plain text
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
    summary="Login and get an access token",
    response_model=Token,
)
def login_account(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # TODO: implement authentication logic (password check, JWT token creation)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Login not implemented",
    )

@router.get(
    "/me",
    response_model=AccountOut,
    summary="Get current logged-in user",
)
def read_current_user(current: Account = Depends(get_current_user)):
    return current
