import pytest
from decimal import Decimal
from unittest.mock import MagicMock
import enum


class TransactionType(enum.Enum):
    BUY = "buy"
    SELL = "sell"


async def calculate_portfolio_value_logic(transactions, ticker_to_price):
    asset_holdings = {}
    for t in transactions:
        asset_holdings.setdefault(t.ticker, 0)
        if t.transaction_type == TransactionType.BUY:
            asset_holdings[t.ticker] += t.quantity
        else:
            asset_holdings[t.ticker] -= t.quantity

    total_value = 0.0
    for ticker, quantity in asset_holdings.items():
        price = ticker_to_price.get(ticker, 0.0)
        total_value += float(quantity) * price
    return total_value


@pytest.mark.asyncio
async def test_calculate_portfolio_value_simple():
    transactions = [
        MagicMock(spec=Transaction, ticker="AAPL", transaction_type=TransactionType.BUY, quantity=Decimal("10.0")),
        MagicMock(spec=Transaction, ticker="GOOGL", transaction_type=TransactionType.BUY, quantity=Decimal("5.0")),
    ]
    prices = {"AAPL": 150.0, "GOOGL": 2800.0}
    total_value = await calculate_portfolio_value_logic(transactions, prices)
    expected_value = (10.0 * 150.0) + (5.0 * 2800.0)
    assert total_value == pytest.approx(expected_value)


@pytest.mark.asyncio
async def test_calculate_portfolio_value_with_sell():
    transactions = [
        MagicMock(spec=Transaction, ticker="AAPL", transaction_type=TransactionType.BUY, quantity=Decimal("10.0")),
        MagicMock(spec=Transaction, ticker="AAPL", transaction_type=TransactionType.SELL, quantity=Decimal("3.0")),
    ]
    prices = {"AAPL": 200.0}
    total_value = await calculate_portfolio_value_logic(transactions, prices)
    expected_value = (10.0 - 3.0) * 200.0
    assert total_value == pytest.approx(expected_value)


@pytest.mark.asyncio
async def test_calculate_portfolio_value_missing_price():
    transactions = [
        MagicMock(spec=Transaction, ticker="AAPL", transaction_type=TransactionType.BUY, quantity=Decimal("10.0")),
        MagicMock(spec=Transaction, ticker="UNKNOWN", transaction_type=TransactionType.BUY, quantity=Decimal("5.0")),
    ]
    prices = {"AAPL": 100.0}
    total_value = await calculate_portfolio_value_logic(transactions, prices)
    expected_value = 10.0 * 100.0
    assert total_value == pytest.approx(expected_value)