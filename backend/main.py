"""
SLIS — Phase 5: FastAPI Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import joblib, json, pandas as pd
from pathlib import Path

from ml import load_models
from routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_models()
    yield

app = FastAPI(title="SLIS API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
