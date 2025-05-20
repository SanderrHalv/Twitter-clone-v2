# server.py
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

# Import your FastAPI app
from app.main import app as api_app

# Create a new FastAPI app that will serve both API and static files
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the API app
app.mount("/api", api_app)

# Mount static files
app.mount("/static", StaticFiles(directory="."), name="static")

# Serve index.html at root
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html", "r") as f:
        content = f.read()
    # Update the API_URL in the HTML to use relative paths
    content = content.replace("const API_URL = '...'", "const API_URL = '/api'")
    return HTMLResponse(content=content)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)