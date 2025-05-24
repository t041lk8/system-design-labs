import os
import json
from typing import Any, Optional
import redis
from redis.exceptions import RedisError

class RedisClient:
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True
        )
        self.default_ttl = 3600  # 1 час по умолчанию

    def get(self, key: str) -> Optional[Any]:
        """Получение данных из кэша"""
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except (RedisError, json.JSONDecodeError):
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Сохранение данных в кэш"""
        try:
            ttl = ttl or self.default_ttl
            return self.client.setex(
                key,
                ttl,
                json.dumps(value)
            )
        except (RedisError, TypeError):
            return False

    def delete(self, key: str) -> bool:
        """Удаление данных из кэша"""
        try:
            return bool(self.client.delete(key))
        except RedisError:
            return False

    def exists(self, key: str) -> bool:
        """Проверка существования ключа в кэше"""
        try:
            return bool(self.client.exists(key))
        except RedisError:
            return False

# Создаем глобальный экземпляр клиента
redis_client = RedisClient() 