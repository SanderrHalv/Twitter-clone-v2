import asyncio
import logging
from collections import defaultdict
from datetime import timedelta

from app.database import SessionLocal  # SQLAlchemy session factory
from app.models import Like             # ORM model for likes

class LikeBatcher:
    """
    Batches like increments in memory and writes them to the database
    in bulk at regular intervals or on shutdown.
    """

    def __init__(self, interval: int = 5):
        # interval (in seconds) between automatic flushes
        self.interval = interval
        # in-memory counter: {tweet_id: count}
        self._counters = defaultdict(int)
        # event loop task reference
        self._task = None
        # lock to protect counters across coroutines
        self._lock = asyncio.Lock()
        # flag to signal shutdown
        self._running = False

    def start(self):
        """
        Begin the periodic flush loop.
        Called once during application startup.
        """
        if not self._running:
            self._running = True
            # schedule the background task
            self._task = asyncio.create_task(self._run())

    async def stop(self):
        """
        Stop the periodic loop and perform one final flush.
        Called during application shutdown.
        """
        self._running = False
        if self._task:
            # wait for background task to finish
            await self._task
        await self.flush()

    async def _run(self):
        """
        Internal loop that flushes counters every `interval` seconds.
        """
        logging.info(f"LikeBatcher running: flush every {self.interval}s")
        while self._running:
            # wait for next interval
            await asyncio.sleep(self.interval)
            await self.flush()  # flush any collected likes

    async def add_like(self, tweet_id: int):
        """
        Record a like for a given tweet in the in-memory counter.
        Called by the tweet router whenever a user likes a tweet.
        """
        async with self._lock:
            self._counters[tweet_id] += 1
            logging.debug(f"Queued like for tweet {tweet_id} (total queued: {self._counters[tweet_id]})")

    async def flush(self):
        """
        Flush all queued like counts to the database in a single transaction.
        Resets the in-memory counters afterward.
        """
        async with self._lock:
            if not self._counters:
                logging.debug("LikeBatcher flush called but no likes to process")
                return  # nothing to do

            # snapshot and reset counters
            batch = dict(self._counters)
            self._counters.clear()

        # perform bulk update in a transaction
        session = SessionLocal()
        try:
            logging.info(f"Flushing {sum(batch.values())} likes across {len(batch)} tweets")
            for tweet_id, count in batch.items():
                # Use an INSERT ... ON CONFLICT or UPDATE query to increment likes
                # Here, we assume Like model has fields tweet_id and count
                like_obj = session.query(Like).filter(Like.tweet_id == tweet_id).one_or_none()
                if like_obj:
                    like_obj.count += count
                else:
                    like_obj = Like(tweet_id=tweet_id, count=count)
                    session.add(like_obj)
            session.commit()
            logging.info("LikeBatcher flush successful")
        except Exception:
            session.rollback()
            logging.exception("Error flushing likes to the database")
        finally:
            session.close()

# instantiate a singleton batcher with a default 5-second flush interval
like_batcher = LikeBatcher(interval=5)