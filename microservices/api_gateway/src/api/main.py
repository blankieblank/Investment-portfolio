import asyncio
import logging
import json
from fastapi import FastAPI
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaConsumer
from prometheus_fastapi_instrumentator import Instrumentator
from .routers import auth, portfolios, ws
from .ws_manager import manager
from core.config import settings

KAFKA_UPDATES_TOPIC = "portfolio_updates"
KAFKA_CONSUMER_GROUP = "api_gateway_group"


async def kafka_consumer_task():
    consumer = AIOKafkaConsumer(
        KAFKA_UPDATES_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_CONSUMER_GROUP,
        auto_offset_reset='latest'
    )
    await consumer.start()
    try:
        async for message in consumer:
            try:
                data = json.loads(message.value.decode('utf-8'))
                user_id = data.get("user_id")
                if user_id:
                    await manager.send_personal_message(data, user_id)
            except Exception as e:
                logging.error(f"Error processing Kafka message: {e}")
    finally:
        await consumer.stop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting Kafka consumer task...")
    app.state.kafka_consumer_task = asyncio.create_task(kafka_consumer_task())
    yield
    logging.info("Stopping Kafka consumer task...")
    app.state.kafka_consumer_task.cancel()
    await app.state.kafka_consumer_task


app = FastAPI(
    title="Investment Portfolio API",
    description="API для управления инвестиционным портфелем",
    version="0.1.0",
    lifespan=lifespan
)
Instrumentator().instrument(app).expose(app)

# @app.get("/", tags=["Root"])
# def read_root():
#     return {"status": "healthy", "message": "Welcome to Investment Portfolio API!"}


@app.get("/", response_class=FileResponse)
async def read_root():
    return "index.html"


app.include_router(auth.router)
app.include_router(portfolios.router)
app.include_router(ws.router)
