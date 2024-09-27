import argparse
import logging

from src.common.data_models.bind_models import connect_and_bind_models
from src.common.amqp.worker_config import WorkerConfigs
from src.common.logger.logger import get_logger


logging.getLogger("pika").setLevel(logging.WARNING)

logger = get_logger(__name__)


def main(parser: argparse.ArgumentParser):
    args = vars(parser.parse_args())

    worker_name = args.get("worker", None)
    assert worker_name is not None, "worker_name is None"

    # Get worker config from enum
    worker_config = WorkerConfigs[worker_name]

    connect_and_bind_models()

    logger.info(f"--- Starting {worker_config.name} ---")

    consumer = worker_config.create_consumer()

    try:
        consumer.run()

    except KeyboardInterrupt:
        logger.info(f"\nExiting Worker")
        consumer.stop()
        consumer.close_connection()
        logger.info("Bye!!!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Brand-DNAi Knowledge Extraction Worker")
    parser.add_argument("-w", "--worker", required=True, choices=WorkerConfigs.get_available_configs())

    main(parser)
