import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Numeric, func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class AssetType(enum.Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    ETF = "etf"


class TransactionType(enum.Enum):
    BUY = "buy"
    SELL = "sell"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    portfolios = relationship("Portfolio", back_populates="owner")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    owner = relationship("User", back_populates="portfolios")
    transactions = relationship("Transaction", back_populates="portfolio")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    asset_type = Column(Enum(AssetType), nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Numeric(18, 9), nullable=False)
    price_per_share = Column(Numeric(18, 9), nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    portfolio = relationship("Portfolio", back_populates="transactions")
    asset = relationship("Asset")
