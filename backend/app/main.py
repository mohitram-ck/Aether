from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, transactions, analytics
from app.core.config import settings
from app.core.redis_client import get_redis, close_redis

app = FastAPI(
    title=settings.APP_NAME,
    description="High-frequency financial transaction engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await get_redis()
    print("Redis connected")

@app.on_event("shutdown")
async def shutdown():
    await close_redis()
    print("Redis disconnected")

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(analytics.router)

@app.get("/health")
async def health():
    return {"status": "Aether is running"}