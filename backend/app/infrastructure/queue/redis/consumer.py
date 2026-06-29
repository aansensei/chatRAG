import json
import logging
import os
import signal
from typing import Callable

import redis

logger = logging.getLogger(__name__)

_running = True


def _handle_signal(signum, frame):
    global _running
    logger.info("Shutdown signal received — stopping after current message.")
    _running = False


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


def _get_redis() -> redis.Redis:
    return redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True, protocol=2)


def consume(queue_name: str, handler: Callable[[dict], None], block_timeout: int = 5) -> None:
    r = _get_redis()
    logger.info(f"Listening on {queue_name}")
    while _running:
        try:
            result = r.blpop(queue_name, timeout=block_timeout)
            if result is None:
                continue
            _, raw = result
            try:
                message = json.loads(raw)
                handler(message)
            except Exception:
                logger.exception(f"Handler error for message: {raw[:200]}")
        except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError):
            pass
        except Exception:
            logger.exception("Unexpected error in consumer loop")
            import time
            time.sleep(1)
