import redis.asyncio as aioredis               # use asyncio client from redis-py
from app.utils.settings import settings       # load Redis URL and other configs

# Global Redis client reference
redis_client: aioredis.Redis | None = None

async def init_cache():
    """
    Initialize the Redis connection pool using redis.asyncio.
    Called on application startup before handling requests.
    """
    global redis_client
    redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )

async def close_cache():
    """
    Close the Redis connection pool on shutdown to free resources.
    """
    if redis_client:
        await redis_client.close()

async def get_tweet_cache(tweet_id: int) -> dict | None:
    """
    Retrieve a cached tweet by its ID.
    Returns a dict of tweet fields if present, else None.
    """
    key = f"tweet:{tweet_id}"
    data = await redis_client.hgetall(key)
    if not data:
        return None
    return data

async def set_tweet_cache(tweet) -> None:
    """
    Cache a Tweet object in Redis and add it to the recent-sorted set.
    Called after creating or updating a tweet in the database.
    """
    key = f"tweet:{tweet.id}"
    await redis_client.hset(
        key,
        mapping={
            "id": str(tweet.id),
            "content": tweet.content,
            "created_at": tweet.created_at.isoformat(),
            "updated_at": tweet.updated_at.isoformat(),
            "account_id": str(tweet.account_id),
        },
    )
    score = tweet.created_at.timestamp()
    await redis_client.zadd("tweets:recent", {key: score})

async def invalidate_tweet_cache(tweet_id: int) -> None:
    """
    Remove a tweet from the cache and the recent-sorted set.
    Called after deleting a tweet in the database.
    """
    key = f"tweet:{tweet_id}"
    await redis_client.delete(key)
    await redis_client.zrem("tweets:recent", key)

async def get_recent_tweets(skip: int = 0, limit: int = 100) -> list[dict]:
    """
    Retrieve a paginated list of recent tweets from the cache.
    Falls back to DB if cache is empty (to be handled in router).
    """
    keys = await redis_client.zrevrange("tweets:recent", skip, skip + limit - 1)
    tweets = []
    for key in keys:
        data = await redis_client.hgetall(key)
        if data:
            tweets.append(data)
    return tweets
