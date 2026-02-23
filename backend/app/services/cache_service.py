from app.core.redis_client import get_redis

BLACKLIST_PREFIX = "blacklist:"
TOKEN_CACHE_PREFIX = "token:"
TOKEN_TTL = 1800

async def cache_token(user_id: str, token: str):
    redis = await get_redis()
    await redis.setex(f"{TOKEN_CACHE_PREFIX}{user_id}", TOKEN_TTL, token)

async def is_token_blacklisted(token: str) -> bool:
    redis = await get_redis()
    result = await redis.get(f"{BLACKLIST_PREFIX}{token}")
    return result is not None

async def blacklist_token(token: str):
    redis = await get_redis()
    await redis.setex(f"{BLACKLIST_PREFIX}{token}", TOKEN_TTL, "1")

async def push_transaction_to_stream(transaction_data: dict):
    redis = await get_redis()
    await redis.xadd("transactions_stream", transaction_data)

async def get_stream_length() -> int:
    redis = await get_redis()
    return await redis.xlen("transactions_stream")