import os
import signal
import tempfile

from threading import Event
from typing import Callable, Hashable, Optional, Tuple

import src.config as config

from src.common.aws.aws import AWS, download_from_s3
from src.common.gs.gs import GS, upload_to_gs
from src.common.socket.pusher import Pusher
from src.common.logger.logger import get_logger


logger = get_logger(__name__)


class ThreadTerminateEvent(object):
    terminate_event = Event()

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(ThreadTerminateEvent, cls).__new__(cls)

        return cls.instance

    def __init__(self):
        pass

    @staticmethod
    def signal_handler(signum: int, frame):
        ThreadTerminateEvent.terminate_event.set()
        raise RuntimeError(f"signal_handler: caught signal={signal.Signals(signum).name}, frame={frame}")

    @staticmethod
    def check_terminate_event():
        if ThreadTerminateEvent.terminate_event.is_set() is True:
            raise RuntimeError(
                f"ThreadTerminateEvent.terminate_event.is_set()={ThreadTerminateEvent.terminate_event.is_set()}"
            )


def push_chat_response(client_id: int, request_event: str, message_content: dict):
    client_channel = f"client_channel_{client_id}"

    payload = {
        "eventName": request_event,
        "message": {
            "content": message_content,
            "status_code": 200,
            "error": None,
        },
    }

    logger.info(f"Going to publish response via Pusher. payload: {payload}")

    pusher_client = Pusher()
    pusher_client.send(client_channel, request_event, payload)


def upload_s3_to_gs(
    s3_bucket: str, s3_key: str, gs_bucket: Optional[str] = config.GS_BUCKET, gs_key: Optional[str] = None
) -> Tuple[str, str]:
    if gs_key is None:
        gs_key = s3_key

    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(s3_key)[-1]) as tmpfile:
        _ = download_from_s3(AWS().get_s3_client(), s3_bucket, s3_key, filename=tmpfile.name)
        upload_to_gs(GS().get_gs_client(), tmpfile.name, gs_bucket, gs_key, public=config.GS_PUBLIC_ACL)

    logger.info(f"Uploaded from {s3_bucket}/{s3_key} to {gs_bucket}/{gs_key}")

    return gs_bucket, gs_key


def function_index_wrapper(func: Callable, index: Hashable) -> Callable:
    def wrap_inner(*args, **kwargs):
        ThreadTerminateEvent.check_terminate_event()

        return (index, func(*args, **kwargs))

    return wrap_inner
