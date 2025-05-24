from functools import wraps
from typing import Any, Callable, Optional
from .redis_client import redis_client

def cache_read_through(prefix: str, ttl: Optional[int] = None):
    """
    Декоратор для реализации паттерна сквозного чтения (Cache-Aside)
    
    Args:
        prefix: Префикс для ключа кэша
        ttl: Время жизни кэша в секундах
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Формируем ключ кэша
            cache_key = f"{prefix}:{str(args)}:{str(kwargs)}"
            
            # Пробуем получить данные из кэша
            cached_data = redis_client.get(cache_key)
            if cached_data is not None:
                return cached_data
            
            # Если данных нет в кэше, получаем их из БД
            result = await func(*args, **kwargs)
            
            # Сохраняем результат в кэш
            if result is not None:
                redis_client.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def cache_write_through(prefix: str, invalidate_pattern: Optional[str] = None):
    """
    Декоратор для реализации паттерна сквозной записи (Write-Through)
    
    Args:
        prefix: Префикс для ключа кэша
        invalidate_pattern: Паттерн ключей для инвалидации кэша
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Выполняем операцию записи
            result = await func(*args, **kwargs)
            
            # Инвалидируем кэш
            if invalidate_pattern:
                pattern = f"{prefix}:{invalidate_pattern}"
                # Здесь можно добавить логику для удаления ключей по паттерну
                # Например, используя SCAN и DEL в Redis
            
            return result
        return wrapper
    return decorator 