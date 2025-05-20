from pydantic import BaseSettings, Field
from datetime import timedelta, datetime

class Settings(BaseSettings):
    # Database & cache URLs
    database_url: str
    redis_url: str

    # JWT authentication
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30  # default expiry

    # Caching (optional TTLs)
    tweet_cache_ttl_seconds: int = Field(3600, description="Time to live for tweet cache entries")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def access_token_expire_delta(self) -> timedelta:
        """Helper to get expiry as timedelta."""
        return timedelta(minutes=self.access_token_expire_minutes)

    @property
    def now(self) -> datetime:
        """UTC now for token expiry calculations."""
        return datetime.utcnow()

# Instantiate a single settings object for import
settings = Settings()
