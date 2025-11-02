from enum import Enum


class CopytradingStates(Enum):
    SELECT_ACTION = "copytrading_start_select_action"


class SelectStates(Enum):
    START = "copytrading_select_start"
    CHANGE = "copytrading_select_change"


class UnregisterStates(Enum):
    START = "copytrading_unregister_start"
    CONFIRM = "copytrading_unregister_confirm"


class SellTypeStates(Enum):
    START = "copytrading_sell_type_start"
    CHANGE = "copytrading_sell_type_change"


class PnlStates(Enum):
    START = "copytrading_pnl_start"
    CHANGE = "copytrading_pnl_change"


class LeverageStates(Enum):
    START = "copytrading_leverage_start"
    CHANGE = "copytrading_leverage_change"


class OrderValueStates(Enum):
    START = "copytrading_order_value_start"
    CHANGE = "copytrading_order_value_change"


class SubscribeStates(Enum):
    START = "copytrading_subscribe_start"
    SUBSCRIBE = "copytrading_subscribe_subscribe"


class UnsubscribeStates(Enum):
    START = "copytrading_unsubscribe_start"
    UNSUBSCRIBE = "copytrading_unsubscribe_unsubscribe"


class RefreshStates(Enum):
    START = "copytrading_refresh_start"


class FollowStates(Enum):
    START = "copytrading_follow_start"
    PAGE = "copytrading_follow_page"
    FOLLOW = "copytrading_follow_follow"
    GO_BACK = "copytrading_follow_go_back"
