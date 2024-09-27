import os
import time

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional


from src.chat.processor import chat_processor
import src.config as config

from src.common.amqp.consumer.queue_consumer import (
    ReconnectingQueueConsumer,
    ReconnectingAsyncIOQueueConsumer,
)
from src.common.logger.logger import get_logger
from src.knowledge_extraction.processor import knowledge_extraction_processor

logger = get_logger(__name__)


def test_processor(params: dict):
    logger.info(f"passthrough_message_processor() got input params: {params}")
    logger.info(f"Sleeping for 5 seconds")
    for i in range(5, 0, -1):
        logger.info(f"{i}")
        time.sleep(1)

    logger.info(f"passthrough_message_processor() completed")


@dataclass(frozen=True)
class WorkerConfig:
    message_processor: Callable
    queue: str
    routing_key: str
    bind_to_delay_exchange: bool = False
    priority: int = config.X_MAX_PRIORITY


class WorkerConfigs(Enum):
    # Declare workers here
    TEST_PROCESSOR = WorkerConfig(
        message_processor=test_processor,
        queue=os.environ.get("TEST_QUEUE", "test_queue"),
        routing_key=os.environ.get("TEST_ROUTING_KEY", "*.test.processor"),
        bind_to_delay_exchange=True,
    )

    CHAT_PROCESSOR = WorkerConfig(
        message_processor=chat_processor,
        queue=config.CHAT_PROCESSOR_QUEUE,
        routing_key=config.CHAT_PROCESSOR_ROUTING_KEY,
        bind_to_delay_exchange=False,
    )

    KNOWLEDGE_EXTRACTION_PROCESSOR = WorkerConfig(
        message_processor=knowledge_extraction_processor,
        queue=config.KNOWLEDGE_EXTRACTION_PROCESSOR_QUEUE,
        routing_key=config.KNOWLEDGE_EXTRACTION_PROCESSOR_ROUTING_KEY,
        priority=config.KNOWLEDGE_EXTRACTION_PROCESSOR_MESSAGE_PRIORITY,
        bind_to_delay_exchange=False,
    )

    @staticmethod
    def get_available_configs():
        return tuple([k.name for k in WorkerConfigs])

    def create_consumer(self, asyncio: Optional[bool] = False) -> ReconnectingQueueConsumer:
        # Ajai - Currently we are using ReconnectingQueueConsumer, keep asyncio False
        # AsyncIO consumer is not tested
        if asyncio is True:
            self.consumer_constructor = ReconnectingAsyncIOQueueConsumer

        else:
            self.consumer_constructor = ReconnectingQueueConsumer
        logger.info(f"Creating a {self.consumer_constructor}")

        self.exchange_name = config.EXCHANGE_NAME
        self.exchange_type = "topic"
        logger.info(f"Bind to delay exchange is set to {self.value.bind_to_delay_exchange}")

        if self.value.bind_to_delay_exchange is True:
            self.exchange_name = config.DELAY_EXCHANGE_NAME
            self.exchange_type = "x-delayed-message"

        logger.info(f"Binding {self.name} to exchange: {self.exchange_name}")
        consumer = self.consumer_constructor(
            queue_name=self.value.queue,
            routing_key=self.value.routing_key,
            callback=self.value.message_processor,
            amqp_url=config.RABBIT_URL,
            exchange_name=self.exchange_name,
            exchange_type=self.exchange_type,
            priority=self.value.priority,
        )
        return consumer
