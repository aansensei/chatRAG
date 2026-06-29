from dotenv import load_dotenv; load_dotenv()
import redis, os
r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), protocol=2)
print("queue:ocr   =", r.llen("queue:ocr"))
print("queue:chunk =", r.llen("queue:chunk"))
print("queue:embed =", r.llen("queue:embed"))
