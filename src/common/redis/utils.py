from src.common.redis.redis import RedisConnection


def get_connection():
    redis_connection = RedisConnection()
    return redis_connection.get_connection()


def set_redis_key(redis_key: str, value: str, expiry=3600):
    connection = get_connection()
    connection.set(redis_key, value)
    connection.expire(redis_key, expiry)


def get_by_redis_key(redis_key: str) -> str:
    connection = get_connection()
    value = connection.get(redis_key)
    return value


def delete_redis_key(redis_key: str):
    connection = get_connection()
    connection.delete(redis_key)
