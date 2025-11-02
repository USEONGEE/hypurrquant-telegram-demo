from enum import Enum


# ================================
# 상태 - 구매 상태를 나타내는 열거형.
# ================================
class BuyOneStates(Enum):
    PAGE = "buy_one_start"
    ORDER_SETTING = "buy_one_order_setting"
    ORDER = "buy_one_order"
