import redis
from src.settings import settings

# ================= redis 설정 =================

client = redis.Redis(
  host=settings.redis_host,
  port=settings.redis_port,
  db=settings.redis_db
)