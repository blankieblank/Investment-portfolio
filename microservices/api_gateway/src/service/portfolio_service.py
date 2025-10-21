from sqlalchemy.orm import Session, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import models
from api import schemas


async def get_portfolios_by_user(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
    query = (
        select(models.Portfolio)
        .where(models.Portfolio.user_id == user_id)
        .options(joinedload(models.Portfolio.snapshot), joinedload(models.Portfolio.transactions))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def create_user_portfolio(db: Session, portfolio: schemas.PortfolioCreate, user_id: int):
    db_portfolio = models.Portfolio(**portfolio.model_dump(), user_id=user_id)
    db.add(db_portfolio)
    await db.commit()
    await db.refresh(db_portfolio)
    return db_portfolio


async def get_portfolio_by_id(db: Session, portfolio_id: int):
    query = select(models.Portfolio).filter(models.Portfolio.id == portfolio_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()
