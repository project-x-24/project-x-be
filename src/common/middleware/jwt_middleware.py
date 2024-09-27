import falcon
import jwt
from src.common.logger.logger import get_logger

logger = get_logger(__name__)


class JWTMiddleware(object):
    def __init__(self, secret):
        self.secret = secret

    def _api_path_whitelist(self, api_path):
        whitelist_path = [
            "/api/health",
            "/api/public/fonts",
        ]

        return api_path in whitelist_path

    def _token_is_valid(self, full_token):
        try:
            parts = full_token.split(" ")
            token = parts[-1]

            payload = jwt.decode(f"{token}", self.secret, algorithms=['HS256'], verify=True)
            client_id = int(payload.get("clientId", 0))
            user_id = int(payload.get("id", 0))
            return True, user_id, client_id
        except jwt.DecodeError as err:
            logger.info(f"Token validation failed Error :{err}")
            return False, None, None
        except Exception as e:
            logger.info(f"Token parsing Error :{e}")
            return False, None, None

    def process_resource(self, req, resp, resource, params):  # pylint: disable=unused-argument
        logger.debug("Processing request in AuthMiddleware: ")

        # skip jwt auth for health check request
        if self._api_path_whitelist(req.path):
            return

        token = req.get_header("Authorization")

        if token is None:
            description = "Please provide an auth token " "as part of the request."

            raise falcon.HTTPUnauthorized(title="Auth token required", description=description)

        is_valid, user_id, client_id = self._token_is_valid(token)
        if is_valid is False:
            description = "The provided auth token is not valid. " "Please request a new token and try again."

            raise falcon.HTTPUnauthorized(title="Authentication required", description=description)

        req.user_id = user_id
        req.client_id = client_id
        req.jwt = token.split(" ")[1]


class DummyJWTMiddleware(object):
    def process_resource(self, req, resp, resource, params):  # pylint: disable=unused-argument
        req.user_id = 1
        req.client_id = 1
