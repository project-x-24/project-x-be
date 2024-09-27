#!/usr/bin/env python3
"""
LL: STILL UNTESTED
"""
import time
import threading

import src.config as config

from src.common.amqp.worker_config import WorkerConfigs
from src.common.amqp.utils.queue_utils import publish
from src.common.logger.logger import get_logger


logger = get_logger(__name__)


def consumer_thread():
    worker_config = WorkerConfigs.TEST_PROCESSOR
    consumer = worker_config.create_consumer()

    try:
        consumer.run()

    except KeyboardInterrupt:
        logger.info(f"\nExiting Worker")
        consumer.stop()
        consumer.close_connection()
        logger.info("Bye!!!")


def publisher_thread():
    payload = {
        "dummy_key_01": {
            "dummy_subkey_01": "dummy_value_01",
            "dummy_subkey_02": "dummy_value_02",
        }
    }

    for i in range(5):
        logger.info(f"Publishing message {i}")

        payload.update({"message_number": i})

        publish(
            exchange_name=config.EXCHANGE_NAME,
            routing_key=WorkerConfigs.TEST_PROCESSOR.value.routing_key,
            data=payload,
            amqp_url=config.RABBIT_URL,
            priority=0,
        )

        time.sleep(5)


def main():
    t1 = threading.Thread(target=consumer_thread, daemon=True)
    t2 = threading.Thread(target=publisher_thread, daemon=True)

    t1.start()
    t2.start()

    try:
        for t in (t1, t2):
            while t.isAlive():
                t.join(5)

    except KeyboardInterrupt:
        logger.info("\nKeyboardInterrupt catched.\nTerminate main thread.")


if __name__ == "__main__":
    main()
