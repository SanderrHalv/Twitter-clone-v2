# server.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# import your API routers here
from app.routers import accounts, tweets  # adjust to your actual modules

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock this down in prod
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# mount your API under /api
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(tweets.router,   prefix="/api/tweets",   tags=["tweets"])

# html=True makes index.html the default for "/"
app.mount(
    path="/",
    app=StaticFiles(directory=".", html=True),
    name="static",
)

# Serve static files from the "static" directory
app.mount("/static", StaticFiles(directory="static"), name="static")

