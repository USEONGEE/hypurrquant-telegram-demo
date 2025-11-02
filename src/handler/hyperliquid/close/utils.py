from telegram.ext import ContextTypes

from hypurrquant.logging_config import configure_logging
from handler.models.perp_balance import (
    Position,
    PerpBalanceMapping,
)
from .settings import CloseSetting

logger = configure_logging(__name__)

MINIMUM_PER_ORDER = 15  # 최소 주문 금액 (USDC)

CONVERSATION_HANDLER_NAME = "CLOSE"


def separate_position(position: Position) -> tuple:
    """
    판매 가능한 잔고와 판매 불가능한 잔고를 분리하는 함수.
    """

    sellable = {}
    unsellable = {}

    for (
        key,
        position_detail,
    ) in position.oneWay.items():  # TODO twoway는 나중에 추가되면 해야된다.
        if position_detail.positionValue < MINIMUM_PER_ORDER:
            unsellable[key] = position_detail
        else:
            sellable[key] = position_detail

    return Position(oneWay=sellable), Position(oneWay=unsellable)


def generate_summary(perp_balance_mapping: PerpBalanceMapping) -> str:

    # ASCII 표 형태로 문자열 생성
    text = "📊 *Total Summary*\n\n```\n"
    text += "+----------------+--------------+\n"
    text += "|      Item      |    Value     |\n"
    text += "+----------------+--------------+\n"
    text += f"| {'Total Value':<14} | {perp_balance_mapping.total_position_value:>11.2f}$ |\n"
    text += (
        f"| {'Total PnL':<14} | {perp_balance_mapping.totalUnrealizedPnl:>11.2f}$ |\n"
    )
    text += f"| {'PnL(%)':<14} | {perp_balance_mapping.pnlPercentage:>11.2f}% |\n"
    text += "+----------------+--------------+\n"
    text += "```\n"

    return text


def can_operation_close(context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    판매 가능한 잔고가 있는지 확인하는 함수.

    Args:
        sellable_balance (list): 판매 가능한 잔고 리스트.

    Returns:
        bool: 판매 가능한 잔고가 있는지 여부.
    """
    setting: CloseSetting = CloseSetting.get_setting(context)
    boolean = len(list(setting.sellable_balance.oneWay.values())) > 0
    logger.debug(f"can_operation_sell: {boolean}")
    return boolean
