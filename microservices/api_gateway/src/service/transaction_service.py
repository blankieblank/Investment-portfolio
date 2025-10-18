from sqlalchemy.orm import Session
from sqlalchemy.future import select

from db import models
from api import schemas


async def get_or_create_asset(db: Session, ticker: str, asset_type: models.AssetType):
    query = select(models.Asset).filter(models.Asset.ticker == ticker)
    result = await db.execute(query)
    db_asset = result.scalar_one_or_none()

    if not db_asset:
        db_asset = models.Asset(ticker=ticker, asset_type=asset_type, name=ticker)
        db.add(db_asset)
        await db.commit()
        await db.refresh(db_asset)
    return db_asset


async def create_portfolio_transaction(db: Session, transaction: schemas.TransactionCreate, portfolio_id: int):
    asset = await get_or_create_asset(db, ticker=transaction.ticker, asset_type=transaction.asset_type)

    db_transaction = models.Transaction(
        portfolio_id=portfolio_id,
        asset_id=asset.id,
        transaction_type=transaction.transaction_type,
        quantity=transaction.quantity,
        price_per_share=transaction.price_per_share,
        transaction_date=transaction.transaction_date
    )
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)
    return db_transaction
