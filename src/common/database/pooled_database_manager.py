import os
from playhouse.pool import PooledMySQLDatabase
from src.common.database.database import get_logger
from peewee import *


class PooledDatabaseManager:
    def __init__(self, db_config):
        self.logger = get_logger()
        self.db_name = os.environ.get(
            db_config["name_env_var"], db_config["default_db_name"]
        )
        self.db_host = os.environ.get(db_config["host_env_var"], "localhost")
        self.db_port = int(os.environ.get(db_config["port_env_var"], "3306"))
        self.db_username = os.environ.get(db_config["username_env_var"], "root")
        self.db_password = os.environ.get(db_config["password_env_var"], "root")
        self.db_config = db_config
        self.db = self.__initialize_db_connection()
        self.logger.info(
            f"Initializing PooledDatabaseManager for {db_config['db_alias_name']}"
        )

    def __get_db_connection(self):
        return PooledMySQLDatabase(
            self.db_name,
            host=self.db_host,
            port=self.db_port,
            user=self.db_username,
            password=self.db_password,
            max_connections=8,
            stale_timeout=300,
            timeout=0,
            charset="utf8mb4",
            use_unicode=True,
        )

    def __initialize_db_connection(self):
        try:
            return self.__get_db_connection()
        except Exception as exception:
            self.logger.error(
                f'PooledDatabaseManager :: Error creating database instance for {self.db_config["db_alias_name"]}: {exception}'
            )
            raise

    def get_db_instance(self):
        return self.db

    def connect(self):
        try:
            self.db.connect()
            self.logger.info(
                f'PooledDatabaseManager :: Established connection with {self.db_config["db_alias_name"]}'
            )
        except Exception as exception:
            self.logger.error(
                f'PooledDatabaseManager :: Error occurred while connecting with {self.db_config["db_alias_name"]} : {exception}'
            )
            raise

    def close(self):
        try:
            if not self.db.is_closed():
                self.db.close()
        except Exception as exception:
            self.logger.error(
                f'PooledDatabaseManager :: Error closing {self.db_config["db_alias_name"]} connection: {exception}'
            )
            raise
