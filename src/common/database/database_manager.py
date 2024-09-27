import os
from src.common.database.database import Database, get_logger
from playhouse.shortcuts import ReconnectMixin
from peewee import MySQLDatabase, SqliteDatabase

from src.config import TEST_MODE


class DatabaseManager(object):
    def __init__(self, db_config):
        self.logger = get_logger()
        self.db_name = os.environ.get(db_config["name_env_var"], db_config["default_db_name"])
        self.db_host = os.environ.get(db_config["host_env_var"], "localhost")
        self.db_port = int(os.environ.get(db_config["port_env_var"], "3306"))
        self.db_username = os.environ.get(db_config["username_env_var"], "root")
        self.db_password = os.environ.get(db_config["password_env_var"], "password")
        self.db_config = db_config
        self.db = self.__initialize_db_connection()
        self.logger.info(f"Initializing DatabaseManager for {db_config['db_alias_name']}")

    def __get_db_connection(self):
        if TEST_MODE is False:

            class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
                pass

            return ReconnectMySQLDatabase(
                self.db_name,
                host=self.db_host,
                port=self.db_port,
                user=self.db_username,
                password=self.db_password,
            )
        else:
            return Database().get_connection(
                db_name=self.db_name,
                db_host=self.db_host,
                db_port=self.db_port,
                db_username=self.db_username,
                db_password=self.db_password,
            )

    def __initialize_db_connection(self):
        try:
            return self.__get_db_connection()
        except Exception as exception:
            self.logger.error(
                f'DatabaseManager :: Error creating database instance for {self.db_config["db_alias_name"]}: {exception}'
            )
            raise

    def bind_models(self, models):
        """To bind the model classes with database"""
        self.db.bind(models)

    def get_db_instance(self):
        return self.db

    def connect(self):
        try:
            self.db.execute_sql("Select 1 as a")  # Actual connection gets created only when we run a sql query
            self.logger.info(f'DatabaseManager :: Established connection with {self.db_config["db_alias_name"]}')
        except Exception as e:
            self.logger.error(f"DatabaseManager :: Error running sample sql query: E:{e}")
            Database().close_connection(db_name=self.db_name, db_host=self.db_host, db_username=self.db_username)
            self.db = Database().get_connection(
                db_name=self.db_name,
                db_host=self.db_host,
                db_port=self.db_port,
                db_username=self.db_username,
                db_password=self.db_password,
            )
            self.db.execute_sql("Select 1 as a")  # Actual connection gets created only when we run a sql query.
            self.logger.info(f'DatabaseManager :: Established connection with {self.db_config["db_alias_name"]}')

    def close(self):
        Database().close_connection(db_name=self.db_name, db_host=self.db_host, db_username=self.db_username)
