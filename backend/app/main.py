from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

from app import create_app

flask_app = create_app()
app = FastAPI(title="RehabConnect API")
app.mount("/", WSGIMiddleware(flask_app))
