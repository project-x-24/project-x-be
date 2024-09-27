"""
LL: THIS IS UNTESTED
"""
import json
import pika

from typing import Optional

from src.config import RABBIT_URL
from src.common.logger.logger import get_logger


logger = get_logger(__name__)


def get_amqp_connection(amqp_url: Optional[str] = None) -> pika.BlockingConnection:
    if amqp_url is None:
        amqp_url = RABBIT_URL

    connection = pika.BlockingConnection(pika.URLParameters(amqp_url))

    return connection


def publish_message(
    channel: pika.channel.Channel,
    exchange: str,
    routing_key: str,
    message: dict,
    priority: Optional[int] = 0,
):
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2, priority=priority),
    )


def publish_delayed_message(
    exchange_name: str,
    routing_key: str,
    data: dict,
    delay: str,
    priority: Optional[int] = None,
):
    connection = get_amqp_connection()
    try:
        channel = connection.channel()
        message = json.dumps(data)
        channel.basic_publish(
            exchange_name,
            routing_key,
            message,
            properties=pika.BasicProperties(delivery_mode=2, headers={"x-delay": f"{delay}"}, priority=priority),
        )
    finally:
        connection.close()


def publish(
    exchange_name: str,
    routing_key: str,
    data: dict,
    amqp_url: Optional[str] = None,
    priority: Optional[int] = 0,
):
    connection = get_amqp_connection(amqp_url)

    try:
        channel = connection.channel()
        message = json.dumps(data)

        publish_message(channel, exchange_name, routing_key, message, priority)

    finally:
        connection.close()


def declare_exchange(
    channel: pika.channel.Channel,
    exchange_name: str,
    exchange_type: Optional[str] = "topic",
    durable: Optional[bool] = True,
):
    channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=durable)


def declare_queue(
    channel: pika.channel.Channel,
    queue_name: str,
    exchange_name: str,
    routing_key: str,
    durable: Optional[bool] = True,
    priority: Optional[int] = None,
):
    if priority is None:
        channel.queue_declare(queue=queue_name, durable=durable)

    else:
        channel.queue_declare(queue=queue_name, durable=durable, arguments={"x-max-priority": 255})

    channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)


def configure_queue(
    amqp_url: str,
    exchange_name: str,
    queue_name: str,
    routing_key: str,
    durable: Optional[bool] = True,
    exchange_type: Optional[str] = "topic",
    priority: Optional[int] = None,
):
    logger.info(f"Configuring queue {queue_name} on exchange {exchange_name}")

    connection = get_amqp_connection(amqp_url)

    try:
        channel = connection.channel()

        logger.info(f"Declaring exchange {exchange_name}")

        if exchange_type == "x-delayed-message":
            channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=durable,
                arguments={"x-delayed-type": "topic"},
            )
        else:
            channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=durable)

        logger.info(f"Creating {queue_name} queue")

        if priority is None:
            channel.queue_declare(queue=queue_name, durable=durable)

        else:
            channel.queue_declare(
                queue=queue_name,
                durable=durable,
                arguments={"x-max-priority": 255},
            )

        channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)

        logger.info("Queue created")

    finally:
        connection.close()

        logger.info(f"Exchange:{exchange_name} declared")
        logger.info(f"Queue:{queue_name} created & bound with routing key: {routing_key}")
        logger.info("Connection closed.")
