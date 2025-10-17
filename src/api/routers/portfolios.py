from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api import schemas
from api.dependencies import get_db, get_current_user
from service import portfolio_service, transaction_service
from db import models

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


@router.post("/", response_model=schemas.Portfolio, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio: schemas.PortfolioCreate, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return await portfolio_service.create_user_portfolio(db=db, portfolio=portfolio, user_id=current_user.id)


@router.get("/", response_model=List[schemas.Portfolio])
async def read_portfolios(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    portfolios = await portfolio_service.get_portfolios_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return portfolios


@router.post("/{portfolio_id}/transactions/", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction_for_portfolio(
    portfolio_id: int,
    transaction: schemas.TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_portfolio = await portfolio_service.get_portfolio_by_id(db, portfolio_id=portfolio_id)
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if db_portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add transaction to this portfolio")
    return await transaction_service.create_portfolio_transaction(db=db, transaction=transaction, portfolio_id=portfolio_id)
