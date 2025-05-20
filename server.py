from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(
    title="Twitter Clone",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/index.html")

from app.routers import accounts, tweets
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(tweets.router, prefix="/api/tweets", tags=["tweets"])
