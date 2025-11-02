from enum import Enum


# ================================
# 상태 - 구매 상태를 나타내는 열거형.
# ================================
class PerpOneStates(Enum):
    PAGE = "perp_one_start"
    ORDER_SETTING = "perp_one_order_setting"
    BEFORE_ORDER = "perp_one_before_order"
    SELECT_LEVERAGE = "perp_one_select_leverage"
    ORDER = "perp_one_order"
