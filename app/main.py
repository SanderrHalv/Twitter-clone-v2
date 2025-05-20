from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.database import Base, engine
from app import models
from app.routers import accounts, tweets

# Lager databasen og tabellene
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Twitter Clone API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins - you can restrict this in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Inkluder routers
app.include_router(accounts.router)
app.include_router(tweets.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Twitter Clone API"}