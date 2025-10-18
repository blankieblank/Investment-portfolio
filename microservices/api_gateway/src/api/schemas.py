from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from db.models import TransactionType, AssetType


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    transaction_type: TransactionType
    quantity: float
    price_per_share: float
    transaction_date: datetime


class TransactionCreate(TransactionBase):
    ticker: str
    asset_type: AssetType = AssetType.STOCK


class Transaction(TransactionBase):
    id: int
    asset_id: int

    class Config:
        from_attributes = True


class PortfolioBase(BaseModel):
    name: str


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioSnapshot(BaseModel):
    current_value: float = 0.0
    last_updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Portfolio(PortfolioBase):
    id: int
    user_id: int
    transactions: List[Transaction] = []
    snapshot: Optional[PortfolioSnapshot] = None

    class Config:
        from_attributes = True
