import asyncio
import json
import logging
import redis.asyncio as redis
from sqlalchemy.future import select
from aiokafka import AIOKafkaProducer

from .celery_app import celery_app
from .core.config import settings
from .db.session import get_db
from .db import models


LATEST_PRICES_KEY = "latest_prices"
KAFKA_UPDATES_TOPIC = "portfolio_updates"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def calculate_portfolio_value(db, redis_client, portfolio_id: int) -> float:
    transactions_result = await db.execute(
        select(models.Transaction).where(models.Transaction.portfolio_id == portfolio_id)
    )
    transactions = transactions_result.scalars().all()
    if not transactions:
        return 0.0
    asset_holdings = {}
    asset_ids_to_tickers = {}
    for t in transactions:
        asset_holdings.setdefault(t.asset_id, 0)
        asset_ids_to_tickers[t.asset_id] = None
        if t.transaction_type == models.TransactionType.BUY:
            asset_holdings[t.asset_id] += t.quantity
        else:
            asset_holdings[t.asset_id] -= t.quantity
    if not asset_ids_to_tickers:
        return 0.0
    asset_results = await db.execute(
        select(models.Asset).where(models.Asset.id.in_(asset_ids_to_tickers.keys()))
    )
    for asset in asset_results.scalars().all():
        asset_ids_to_tickers[asset.id] = asset.ticker

    tickers_needed = list(filter(None, asset_ids_to_tickers.values()))
    if not tickers_needed:
        return 0.0

    asset_prices = await redis_client.hmget(LATEST_PRICES_KEY, tickers_needed)
    ticker_to_price = {
        ticker: float(price)
        for ticker, price in zip(tickers_needed, asset_prices) if price is not None
    }
    total_value = 0.0
    for asset_id, quantity in asset_holdings.items():
        ticker = asset_ids_to_tickers.get(asset_id)
        if ticker:
            price = ticker_to_price.get(ticker, 0.0)
            total_value += float(quantity) * price
    return total_value


async def process_price_update(ticker: str, price: float):
    logging.info(f"--- Starting recalculation process for ticker {ticker}... ---")
    redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
    kafka_producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
    try:
        await kafka_producer.start()
        async for db in get_db():
            asset_result = await db.execute(select(models.Asset).where(models.Asset.ticker == ticker))
            asset = asset_result.scalar_one_or_none()
            if not asset:
                logging.warning(f"Asset with ticker '{ticker}' not in DB. Cannot process.")
                return

            portfolio_result = await db.execute(
                select(models.Transaction.portfolio_id).where(models.Transaction.asset_id == asset.id).distinct()
            )
            portfolio_ids = portfolio_result.scalars().all()
            for portfolio_id in portfolio_ids:
                logging.info(f"Recalculating value for portfolio_id: {portfolio_id}")
                new_value = await calculate_portfolio_value(db, redis_client, portfolio_id)
                snapshot_result = await db.execute(select(models.PortfolioSnapshot).where(models.PortfolioSnapshot.portfolio_id == portfolio_id))
                snapshot = snapshot_result.scalar_one_or_none()
                if snapshot:
                    snapshot.current_value = new_value
                else:
                    snapshot = models.PortfolioSnapshot(portfolio_id=portfolio_id, current_value=new_value)
                    db.add(snapshot)
                portfolio_result_for_user = await db.execute(select(models.Portfolio).where(models.Portfolio.id == portfolio_id))
                portfolio = portfolio_result_for_user.scalar_one_or_none()

                if portfolio:
                    update_message = {
                        "event": "portfolio_updated",
                        "portfolio_id": portfolio_id,
                        "user_id": portfolio.user_id,
                        "new_value": float(new_value)
                    }
                    await kafka_producer.send_and_wait(KAFKA_UPDATES_TOPIC, json.dumps(update_message).encode('utf-8'))
                    logging.info(f"Sent update notification for portfolio {portfolio_id} to Kafka.")
            await db.commit()
            logging.info(f"Committed DB updates for portfolios affected by {ticker}.")
    finally:
        await redis_client.close()
        await kafka_producer.stop()


@celery_app.task(name="process_market_data")
def process_market_data(price_data: dict):
    ticker = price_data.get("ticker")
    price = price_data.get("price")
    if not ticker or not price:
        logging.warning(f"Received invalid price data in Celery task: {price_data}")
        return
    logging.info(f"[TASK RECEIVED] Processing data for {ticker} at price {price}.")
    try:
        asyncio.run(process_price_update(ticker, price))
    except Exception as e:
        logging.error(f"An exception occurred while processing price update for {ticker}: {e}", exc_info=True)