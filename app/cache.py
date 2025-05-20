import aioredis
from app.utils.settings import settings  # load Redis URL and other configs

# Global Redis client reference
redis = None

async def init_cache():
    """
    Initialize the Redis connection pool using aioredis.
    Called on application startup before handling requests.
    """
    global redis
    redis = await aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )  # create Redis client with UTF-8 responses

async def close_cache():
    """
    Close the Redis connection pool on shutdown to free resources.
    """
    await redis.close()

async def get_tweet_cache(tweet_id: int) -> dict | None:
    """
    Retrieve a cached tweet by its ID.
    Returns a dict of tweet fields if present, else None.
    """
    key = f"tweet:{tweet_id}"
    data = await redis.hgetall(key)
    if not data:
        return None  # cache miss
    # Convert string timestamps back to appropriate types if needed
    # e.g. data["created_at"] = datetime.fromisoformat(data["created_at"]), etc.
    return data

async def set_tweet_cache(tweet) -> None:
    """
    Cache a Tweet object in Redis and add it to the recent-sorted set.
    Called after creating or updating a tweet in the database.
    """
    key = f"tweet:{tweet.id}"
    # Store tweet fields in a hash
    await redis.hset(
        key,
        mapping={
            "id": str(tweet.id),
            "content": tweet.content,
            "created_at": tweet.created_at.isoformat(),  # ISO string for ordering
            "updated_at": tweet.updated_at.isoformat(),
            "account_id": str(tweet.account_id),
        },
    )
    # Score by timestamp for sorted retrieval
    score = tweet.created_at.timestamp()
    await redis.zadd("tweets:recent", {key: score})

async def invalidate_tweet_cache(tweet_id: int) -> None:
    """
    Remove a tweet from the cache and the recent-sorted set.
    Called after deleting a tweet in the database.
    """
    key = f"tweet:{tweet_id}"
    await redis.delete(key)
    await redis.zrem("tweets:recent", key)

async def get_recent_tweets(skip: int = 0, limit: int = 100) -> list[dict]:
    """
    Retrieve a paginated list of recent tweets from the cache.
    Falls back to DB if cache is empty (to be handled in router).
    """
    # Get keys for the requested range (highest scores first)
    keys = await redis.zrevrange("tweets:recent", skip, skip + limit - 1)
    tweets = []
    for key in keys:
        data = await redis.hgetall(key)
        if data:
            tweets.append(data)
    return tweets
