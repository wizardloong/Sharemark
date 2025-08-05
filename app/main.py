from fastapi import FastAPI
from dotenv import load_dotenv
import os

from api import router as api_router
from websocket import router as ws_router

load_dotenv()

app = FastAPI()
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)
