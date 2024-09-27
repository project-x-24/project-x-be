import time

from typing import Optional

from src.common.logger.logger import get_logger
from src.common.amqp.consumer.base_consumer import BaseConsumer, BaseAsyncIOConsumer


logger = get_logger(__name__)


class ReconnectingQueueConsumer(object):
    """This is an example consumer that will reconnect if the nested
    ExampleConsumer indicates that a reconnect is necessary.

    """

    @staticmethod
    def _base_consumer(*args, **kwargs):
        return BaseConsumer(*args, **kwargs)

    def __init__(
        self,
        amqp_url: str,
        queue_name: str,
        routing_key: str,
        callback,
        exchange_name: str,
        exchange_type: str,
        priority: int = None,
        reconnect_delay: Optional[int] = 5,
    ):
        self._reconnect_delay = reconnect_delay
        self._amqp_url = amqp_url
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.callback = callback
        self.priority = priority
        self._consumer = self._base_consumer(
            queue_name=self.queue_name,
            routing_key=self.routing_key,
            callback=self.callback,
            amqp_url=self._amqp_url,
            exchange_name=self.exchange_name,
            exchange_type=self.exchange_type,
            priority=self.priority,
        )

    def run(self):
        while True:
            try:
                self._consumer.run()

            except KeyboardInterrupt:
                self._consumer.stop()
                break
            
            # LL: Re-enable this for now after other thread/close connection fixes - will disable again if this causes 
            # further problems
            self._maybe_reconnect()

    def _maybe_reconnect(self):
        if self._consumer.should_reconnect:
            self._consumer.stop()
            reconnect_delay = self._get_reconnect_delay()
            logger.info("Reconnecting after %d seconds", reconnect_delay)
            time.sleep(reconnect_delay)
            self._consumer = self._base_consumer(
                queue_name=self.queue_name,
                routing_key=self.routing_key,
                callback=self.callback,
                amqp_url=self._amqp_url,
                exchange_name=self.exchange_name,
                priority=self.priority,
            )

    def _get_reconnect_delay(self):
        if self._consumer.was_consuming:
            self._reconnect_delay = 0
        else:
            self._reconnect_delay += 1
        if self._reconnect_delay > 30:
            self._reconnect_delay = 30
        return self._reconnect_delay
    
    def stop(self):
        self._consumer.stop()

    def close_connection(self):
        self._consumer.close_connection()


class ReconnectingAsyncIOQueueConsumer(ReconnectingQueueConsumer):
    @staticmethod
    def _base_consumer(*args, **kwargs):
        return BaseAsyncIOConsumer(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise NotImplementedError(f"ReconnectingAsyncIOQueueConsumer has not been tested")
