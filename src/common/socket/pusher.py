import pusher
import src.config as config

from src.common.logger.logger import get_logger


logger = get_logger(__name__)


class FakeSender(object):
    def __init__(self):
        pass

    def trigger(self, *args, **kwargs):
        logger.info(f"fake pusher trigger() received args={args}, kwargs={kwargs}")


class Pusher(object):
    __shared_state = {}
    __pusher_inited = False

    def __init__(self):
        self.__dict__ = self.__shared_state
        if self.__pusher_inited is False:
            self.__pusher_inited = True
            self.__pusher_sender = self.__get_sender()

    @staticmethod
    def __get_sender():
        if config.USE_FAKE_PUSHER is True:
            logger.warning(f"USE_FAKE_PUSHER={config.USE_FAKE_PUSHER} - using fake pusher")
            sender = FakeSender()

        else:
            sender = pusher.Pusher(
                app_id=config.SOKETI_APP_ID,
                key=config.SOKETI_KEY,
                secret=config.SOKETI_SECRET,
                cluster=config.SOKETI_CLUSTER,
                host=config.SOKETI_HOST,
                ssl=config.SOKETI_ENABLE_SSL,
            )

            logger.info(f"Sender Pusher. Host: {config.SOKETI_HOST}.")

        return sender

    def send(self, channels, event_name, data):
        if self.__pusher_sender is None:
            self.__pusher_sender = self.__get_sender()

        logger.info(f"Pusher::trigger channels:{channels} - event: {event_name} - data: {data}")

        return self.__pusher_sender.trigger(channels, event_name, data)
