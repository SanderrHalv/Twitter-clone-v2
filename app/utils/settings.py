# app/utils/settings.py

import os
from datetime import timedelta, datetime
from dotenv import load_dotenv

# Load .env from the project root 
load_dotenv()

class Settings:
    # Core URLs and keys (now guaranteed loaded into os.environ if present)
    database_url: str = os.getenv("DATABASE_URL", "")
    redis_url: str = os.getenv("REDIS_URL", "")

    secret_key: str = os.getenv("SECRET_KEY", "")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Cache config
    tweet_cache_ttl_seconds: int = int(os.getenv("TWEET_CACHE_TTL_SECONDS", "3600"))

    @property
    def access_token_expire_delta(self) -> timedelta:
        return timedelta(minutes=self.access_token_expire_minutes)

    @property
    def now(self) -> datetime:
        return datetime.utcnow()

settings = Settings()
