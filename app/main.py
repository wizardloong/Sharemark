from pathlib import Path

from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=Path(__file__).parent.parent / 'env' / '.env')

from api import router as api_router
from websocket import router as ws_router


app = FastAPI()
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)
