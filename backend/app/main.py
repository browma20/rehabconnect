from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from app import create_app

flask_app = create_app()

app = FastAPI(title="RehabConnect API")

# Mount Flask under /api
app.mount("/api", WSGIMiddleware(flask_app))

@app.get("/debug/env")
def debug_env():
    import os
    return {"DATABASE_URL": os.getenv("DATABASE_URL")}

@app.get("/")
def home():
    return {
        "message": "RehabConnect backend is running",
        "docs": "/docs",
        "api_base": "/api"
    }
