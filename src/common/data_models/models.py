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

# class AiModels(BaseModel):
#     name = CharField()
#     display_name = CharField()
#     model_type_id = IntegerField()
#     model_provider_id = IntegerField()
#     model_code = CharField()
#     metadata = JSONField()
#     created_at = DateTimeField()
#     deleted_at = DateTimeField(null=True)
#     updated_at = DateTimeField()

#     class Meta:
#         table_name = "AiModels"


# class ChatHistories(BaseModel):
#     user_id = IntegerField()
#     client_id = IntegerField()
#     session_id = CharField()
#     message = JSONField(null=True)  # json
#     metadata = JSONField(null=True)  # json
#     created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
#     deleted_at = DateTimeField(null=True)

#     class Meta:
#         table_name = "ChatHistories"


# class AssetTypes(BaseModel):
#     name = CharField()
#     created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
#     updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
#     deleted_at = DateTimeField(null=True)

#     class Meta:
#         table_name = "AssetTypes"


# class Assets(BaseModel):
#     client_id = IntegerField()
#     user_id = IntegerField()
#     parent_id = IntegerField(null=True)
#     file_name = CharField(null=True)
#     language = CharField(null=True)
#     s3_key = CharField(null=True)
#     s3_bucket = CharField(null=True)
#     asset_type = ForeignKeyField(column_name="asset_type_id", field="id", model=AssetTypes)
#     metadata = JSONField(null=True)  # json
#     created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
#     updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
#     deleted_at = DateTimeField(null=True)

#     class Meta:
#         table_name = "Assets"
#         indexes = (
#             (("client_id", "user_id", "asset_type_id"), False),
#             (("client_id", "user_id", "parent_id"), False),
#         )
