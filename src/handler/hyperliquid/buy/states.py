# .stock_select.py

from telegram.ext import (
    ConversationHandler,
)

from enum import Enum, auto


class MarketStrategyState(Enum):
    UPTREND = "BUY_STRATEGY_STATE|UPTREND"  # 상승장
    DOWNTREND = "BUY_STRATEGY_STATE|DOWNTREND"  # 하락장
    SIDEWAYS = "BUY_STRATEGY_STATE|SIDEWAYS"  # 횡보장


# ================================
# 상태 - 구매 상태를 나타내는 열거형.
# ================================
class BuyStates(Enum):
    SELECT_STRATEGY = "buy_select_strategy"
    SELECT_STOCK = "buy_select_stock"
    SELECT_STOCK_SHOW = "buy_select_stock_show"
    ORDER = "buy_order"


# ================================
# 내부 State
# ================================
class StrategyStates(Enum):
    START = "buy_strategy_start"
    SELECTING_STRATEGY = "buy_selecting_strategy"
    ASKING_PARAMS = "buy_asking_params"
    # 대화가 끝난 후 상태 (사용 여부에 따라 생성)
    END = ConversationHandler.END


# =============== #
# 내부 상태 정의 #
# =============== #
class StockSelectStates(Enum):
    START = "buy_stock_select_start"
    PAGE = "buy_stock_select_page"
    END = ConversationHandler.END


# =============== #
# 내부 상태 정의 #
# =============== #
class OrderStates(Enum):
    START = "buy_order_start"
    PURCHASE_AMOUNT_SELECTION = "buy_order_purchase_amount_selection"
