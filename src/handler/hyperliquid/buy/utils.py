from .model.orderable_market_data import (
    OrderableMarketData,
)
from hypurrquant.logging_config import configure_logging

from typing import List

logger = configure_logging(__name__)

MINIMUM_PER_ORDER = 20  # 최소 주문 금액 (USDC)

CONVERSATION_HANDLER_NAME = "BUY"


def get_needed_balance(data: List[OrderableMarketData]):
    total = 0
    for i in [d for d in data if d.is_buy]:
        total += i.is_buy
    return total * 20


def is_sufficient_balance(data: List[OrderableMarketData], balance: float):
    logger.debug(f"balance: {balance}, needed: {get_needed_balance(data)}")
    return balance >= get_needed_balance(data)
