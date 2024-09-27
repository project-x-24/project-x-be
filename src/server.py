import falcon
from src.common.health_resource import HealthResource
from src.common.context_resource import ContextResource
from src.common.todo_resource import ToDoResource
from src.common.file_resource import FileResource
from src.common.data_models.bind_models import connect_and_bind_models
from src.common.middleware.db_connection_middleware import DBConnectionMiddleware
from src.common.middleware.jwt_middleware import DummyJWTMiddleware, JWTMiddleware
from falcon_marshmallow import Marshmallow

from src.config import JWT_SECRET


def create_app(test_mode=False):
    if test_mode is False:
        # Initialize DB connection on server start
        connect_and_bind_models()
        _app = falcon.App(
            middleware=[
                DBConnectionMiddleware(),
                # JWTMiddleware(JWT_SECRET),
                # Marshmallow(),
                falcon.CORSMiddleware(allow_origins="trypencil.com", allow_credentials="*"),
            ]
        )
    else:
        _app = falcon.App(
            middleware=[
                DummyJWTMiddleware(),
                Marshmallow(),
                falcon.CORSMiddleware(allow_origins="*", allow_credentials="*"),
            ]
        )

    _app.add_route("/api/health", HealthResource())
    _app.add_route("/api/files", FileResource())
    _app.add_route("/api/context", ContextResource())
    _app.add_route("/api/todo", ToDoResource())

    return _app


app = create_app()