import os
import hashlib

from src.common.logger.logger import get_logger
from playhouse.db_url import connect

from src.config import TEST_MODE, TEST_SUITE


logger = get_logger(__name__)


class Database(object):
    __shared_state = {}
    __connections = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

    def get_connection(
        self,
        db_name,
        db_host,
        db_port,
        db_username,
        db_password,
    ):
        db_hash = hashlib.md5(f"{db_host}_{db_username}_{db_name}".encode()).hexdigest()
        if db_hash not in self.__connections.keys() or self.__connections.get(db_hash) is None:
            self.__connections[db_hash] = self.__get_connection(db_name, db_host, db_port, db_username, db_password)
        return self.__connections[db_hash]

    def close_connection(self, db_name, db_host, db_username):
        db_hash = hashlib.md5(f"{db_host}_{db_username}_{db_name}".encode()).hexdigest()
        if db_hash in self.__connections.keys() and self.__connections[db_hash] is not None:
            try:
                self.__connections[db_hash].close()
            except Exception as e:
                logger.error(f"Error closing connection to db_host:{db_host} / db_name:{db_name}. E:{e}")
            try:
                self.__connections.pop(db_hash, None)
            except Exception as e:
                logger.error(
                    f"Error removing connection db_hash->  db_host:{db_host} / db_name:{db_name} from "
                    f"connections dict. E:{e}"
                )

    @staticmethod
    def __get_connection(db_name, db_host, db_port, db_username, db_password):
        if TEST_MODE:
            if TEST_SUITE == "other":
                logger.info("using local sqlite3 database for server...")
                return connect(f"sqlite:///{db_name}.db")
            elif TEST_SUITE == "editor":
                logger.info("using local sqlite3 database for server...")
                return connect(f"sqlite:///{db_name}-qe.db")
        else:
            logger.info("connecting to MySQL.")

        database_url = f"mysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
        return connect(database_url, **{"charset": "utf8mb4", "use_unicode": True})
