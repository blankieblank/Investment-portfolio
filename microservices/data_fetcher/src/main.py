import os
import asyncio
import json
import logging
import httpx
from aiokafka import AIOKafkaProducer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

KAFKA_BROKER = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
KAFKA_TOPIC = "market_data"
TICKERS_TO_WATCH = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
FETCH_INTERVAL_SECONDS = 30


async def get_kafka_producer(broker_url: str) -> AIOKafkaProducer:
    while True:
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=broker_url,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await producer.start()
            logging.info("Successfully connected to Kafka.")
            return producer
        except Exception as e:
            logging.error(f"Failed to connect to Kafka: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)


async def fetch_stock_price(client: httpx.AsyncClient, ticker: str) -> dict or None:
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
    try:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        if 'c' in data and data['c'] != 0:
            return {"ticker": ticker, "price": data['c'], "timestamp": data['t']}
        else:
            logging.warning(f"No price data for {ticker} in response: {data}")
            return None
    except httpx.RequestError as e:
        logging.error(f"Failed to fetch data for {ticker}: {e}")
        return None


async def main():
    if not KAFKA_BROKER or not FINNHUB_API_KEY:
        logging.error("Environment variables KAFKA_BOOTSTRAP_SERVERS and FINNHUB_API_KEY must be set.")
        return

    logging.info(f"Async Data Fetcher starting... Kafka Broker: {KAFKA_BROKER}")
    producer = await get_kafka_producer(KAFKA_BROKER)
    try:
        async with httpx.AsyncClient() as client:
            while True:
                tasks = [fetch_stock_price(client, ticker) for ticker in TICKERS_TO_WATCH]
                results = await asyncio.gather(*tasks)
                for price_data in results:
                    if price_data:
                        try:
                            await producer.send_and_wait(KAFKA_TOPIC, value=price_data, key=price_data["ticker"].encode('utf-8'))
                            logging.info(f"Sent data to Kafka topic '{KAFKA_TOPIC}': {price_data}")
                        except Exception as e:
                            logging.error(f"Failed to send message to Kafka: {e}")
                logging.info(f"--- Cycle finished. Waiting for {FETCH_INTERVAL_SECONDS} seconds. ---")
                await asyncio.sleep(FETCH_INTERVAL_SECONDS)
    finally:
        if producer:
            await producer.stop()
            logging.info("Kafka producer stopped.")

if __name__ == "__main__":
    asyncio.run(main())
