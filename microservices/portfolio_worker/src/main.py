import asyncio
import logging
import json
from aiokafka import AIOKafkaConsumer
from .core.config import settings
from .tasks import process_market_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

KAFKA_TOPIC = "market_data"
KAFKA_GROUP_ID = "portfolio_worker_group"


async def consume():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset='earliest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    await consumer.start()
    logging.info(f"Kafka Consumer started for topic '{KAFKA_TOPIC}'. Waiting for messages...")
    try:
        async for message in consumer:
            logging.info(f"Received message: {message.value}")
            price_data = message.value
            process_market_data.delay(price_data)
            logging.info(f"Dispatched task to Celery for ticker: {price_data.get('ticker')}")
    finally:
        await consumer.stop()
        logging.info("Kafka Consumer stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(consume())
    except KeyboardInterrupt:
        logging.info("Consumer process interrupted.")
    except Exception as e:
        logging.error(f"Consumer process failed: {e}", exc_info=True)