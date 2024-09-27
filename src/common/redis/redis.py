import os

import redis
from src.common.logger.logger import get_logger
from src.config import REDIS_DB, REDIS_HOST, REDIS_PORT

logger = get_logger("redis")


class RedisConnection:
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        self.redis_connection = None

    def __connect(self) -> None:
        try:
            redis_host = REDIS_HOST
            redis_port = REDIS_PORT
            redis_db = REDIS_DB

            logger.info(f"Connecting to Redis at {redis_host}:{redis_port}")
            pool = redis.ConnectionPool(host=redis_host, port=redis_port, db=redis_db)
            self.redis_connection = redis.Redis(connection_pool=pool)
            logger.info(f"Connected to Redis")
            self.redis_connection.ping()

            logger.info(f"Redis connection test successful!!!")

        except Exception as ee:
            logger.error(ee, exc_info=True)
            self.redis_connection = None

    def get_connection(self):
        if self.redis_connection is None:
            self.__connect()
        return self.redis_connection
