from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import SessionLocal

router = APIRouter(prefix="/accounts", tags=["Accounts"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Account)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    db_account = crud.get_account_by_username(db, username=account.username)
    if db_account:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_email = crud.get_account_by_email(db, email=account.email)
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return crud.create_account(db=db, account=account)

@router.get("/", response_model=list[schemas.Account])
def list_accounts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    accounts = crud.get_accounts(db, skip=skip, limit=limit)
    return accounts

@router.get("/{account_id}", response_model=schemas.Account)
def get_account(account_id: int, db: Session = Depends(get_db)):
    db_account = crud.get_account_by_id(db, account_id=account_id)
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return db_account

@router.get("/search/", response_model=list[schemas.Account])
def search_accounts(query: str, db: Session = Depends(get_db)):
    accounts = crud.search_accounts(db, query=query)
    return accounts