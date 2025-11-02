from telegram.ext import ContextTypes


from handler.models.spot_balance import SpotBalance
from .settings import SellSetting
from .models.orderable_spot_balance import (
    OrderableSpotbalance,
)
from handler.models.spot_balance import SpotBalanceMapping
from hypurrquant.logging_config import configure_logging

from typing import List

logger = configure_logging(__name__)

MINIMUM_PER_ORDER = 15  # 최소 주문 금액 (USDC)

CONVERSATION_HANDLER_NAME = "SELL"


def separate_spot_balance(spot_balances: List[SpotBalance]) -> tuple:
    """
    판매 가능한 잔고와 판매 불가능한 잔고를 분리하는 함수.

    Args:
        spot_balances (list): SpotBalance 리스트.

    Returns:
        tuple: 판매 가능한 잔고 리스트, 판매 불가능한 잔고 리스트.
    """
    sellable_balance = []
    unsellable_balance = []

    for spot_balance in spot_balances:
        if spot_balance.Value > MINIMUM_PER_ORDER:
            sellable_balance.append(spot_balance)
        else:
            unsellable_balance.append(spot_balance)

    return sellable_balance, unsellable_balance


def can_operation_sell(context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    판매 가능한 잔고가 있는지 확인하는 함수.

    Args:
        sellable_balance (list): 판매 가능한 잔고 리스트.

    Returns:
        bool: 판매 가능한 잔고가 있는지 여부.
    """
    setting: SellSetting = SellSetting.get_setting(context)
    boolean = len(setting.sellable_balance) > 0
    logger.debug(f"can_operation_sell: {boolean}")
    return boolean


def create_partial_sell_request_body(
    spot_balances: List[SpotBalance], percent: float
) -> List[dict]:
    """
    부분 매도 요청 바디를 생성하는 함수.

    Args:
        spot_balances (list): SpotBalance 리스트.
        percent (float): 매도 비율.

    Returns:
        list: 부분 매도 요청 바디 리스트.
    """

    filterd_balances = [
        {
            "name": balance.Name,
            "value": percent,
        }
        for balance in spot_balances
    ]
    return filterd_balances


def create_sepcific_sell_request_body(
    spot_balances: List[OrderableSpotbalance],
) -> List[dict]:
    """
    부분 매도 요청 바디를 생성하는 함수.

    Args:
        spot_balances (list): SpotBalance 리스트.
        percent (float): 매도 비율.

    Returns:
        list: 부분 매도 요청 바디 리스트.
    """

    filterd_balances = [
        {
            "name": balance.Name,
            "value": 100,
        }
        for balance in spot_balances
        if balance.is_sell
    ]
    logger.debug(f"create_sepcific_sell_request_body: {filterd_balances}")
    return filterd_balances


def generate_summary(spot_balance_mapping: SpotBalanceMapping) -> str:

    # ASCII 표 형태로 문자열 생성
    text = "📊 *Total Summary*\n\n```\n"
    text += "+----------------+--------------+\n"
    text += "|      Item      |    Value     |\n"
    text += "+----------------+--------------+\n"
    text += f"| {'Total Value':<14} | {spot_balance_mapping.stock_total_balance:>11.2f}$ |\n"
    text += f"| {'Total PnL':<14} | {spot_balance_mapping.total_pnl:>11.2f}$ |\n"
    text += f"| {'PnL(%)':<14} | {spot_balance_mapping.total_pnl_percent:>11.2f}% |\n"
    text += "+----------------+--------------+\n"
    text += "```\n"

    return text
