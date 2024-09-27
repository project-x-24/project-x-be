from typing import Optional

from src.common.socket.constants import SocketErrorMessage
from src.common.logger.logger import get_logger
from src.common.socket.pusher import Pusher

logger = get_logger(__name__)


class SocketPublisher(object):
    def __init__(self, client_id: int) -> None:
        self.client_id = client_id
        self.__set_channel(client_id)
        self.__load_pusher_client()

    def __set_channel(self, client_id: Optional[int]):
        if client_id is None:
            raise RuntimeError(
                f"Failed to initialize socket publisher. Error in configuring client channel. Client ID is None."
            )
        self.channel = f"client_channel_{client_id}"
        logger.info(f"Client channel set successfully.")

    def __load_pusher_client(self):
        try:
            self.pusher_client = Pusher()

        except Exception as e:
            logger.error(f"Error while initializing socket publisher. {e}")
            raise e

    def send(self, event_name: str, message_content: dict, socket_error_message: Optional[SocketErrorMessage] = None):
        try:
            if socket_error_message is not None:
                status_code = socket_error_message.status_code
                error = {
                    "error_code": socket_error_message.error_code,
                    "message": socket_error_message.error_message,
                }

            else:
                status_code = 200
                error = None

            payload = {
                "eventName": event_name,
                "message": {
                    "content": message_content,
                    "status_code": status_code,
                    "error": error,
                },
            }

            logger.info(f"Going to publish response via Pusher. payload: {payload}")
            self.pusher_client.send(self.channel, event_name, payload)

        except Exception as e:
            logger.error(f"Socket Error - {e}", exc_info=True)
            raise e
