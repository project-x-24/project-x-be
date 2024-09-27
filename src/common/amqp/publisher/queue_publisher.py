import json
import pika

from src.common.logger.logger import get_logger
from src.config import RABBIT_URL, TEST_DUMMY_AMQP_PUBLISH


logger = get_logger(__name__)


def get_amqp_connection(amqp_url=None):
    if amqp_url is None:
        amqp_url = RABBIT_URL

    connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
    return connection


def publish_message(channel, exchange, routing_key, message, priority):
    if TEST_DUMMY_AMQP_PUBLISH is False:
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2, priority=priority),
        )

    else:
        logger.warning(
            f"TEST_DUMMY_AMQP_PUBLISH is True - not publishing to queue. Got payload={message}, "
            f"exchange={exchange}, routing_key={routing_key}, priority={priority}"
        )


def publish_to_queue(exchange_name, routing_key, data, amqp_url=None, priority=None):
    connection = get_amqp_connection(amqp_url)

    try:
        channel = connection.channel()
        message = json.dumps(data)
        publish_message(channel, exchange_name, routing_key, message, priority)

    finally:
        connection.close()
