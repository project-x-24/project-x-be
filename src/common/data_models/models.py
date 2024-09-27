import json
import os

# pylint: disable=[wildcard-import, unused-wildcard-import, abstract-method]
from peewee import *
from src.common.data_models.utils import (
    db_pool_enabled,
    get_sub_classes,
    is_test_environment,
)
from src.common.database.database_manager import DatabaseManager
from src.common.database.pooled_database_manager import PooledDatabaseManager

WEIGHT_CREATE_ROW_DEFAULT_VALUE = 1.0

db_config = {
    "name_env_var": "DB_NAME",
    "default_db_name": "project_x_db",
    "host_env_var": "DB_HOST",
    "port_env_var": "DB_PORT",
    "username_env_var": "DB_USERNAME",
    "password_env_var": "DB_PASSWORD",
    "db_alias_name": "project x database",  # Human-readable name for logging purpose
}

USE_DB_POOL = db_pool_enabled() and not is_test_environment()

if USE_DB_POOL:
    db_manager = PooledDatabaseManager(db_config)
else:
    db_manager = DatabaseManager(db_config)


def connect():
    if not USE_DB_POOL:
        models = get_sub_classes(BaseModel)
        db_manager.bind_models(models)
    db_manager.connect()


def close():
    db_manager.close()


db = db_manager.get_db_instance()


class UnknownField(object):
    def __init__(self, *_, **__):
        pass


class JSONField(TextField):
    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)


class BaseModel(Model):
    id = AutoField()
    if USE_DB_POOL:

        class Meta:
            database = db


# Use this format to create data models, keeping it as comment for ref

class Context(BaseModel):
    id = IntegerField()
    name = CharField()
    agent = IntegerField()
    question = CharField()
    answer = CharField()
    created_at = DateTimeField()
    updated_at = DateTimeField()
    deleted_at = DateTimeField(null=True)

    class Meta:
        table_name = "context"

class ToDoList(BaseModel):
    id = IntegerField()
    event = CharField()
    date = CharField()
    created_at = DateTimeField()
    updated_at = DateTimeField()
    deleted_at = DateTimeField(null=True)

    class Meta:
        table_name = "to_do_list"