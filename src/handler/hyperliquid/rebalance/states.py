from enum import Enum


class RebalanceStates(Enum):
    SELECT_ACTION = "rebalance_start_select_action"
    TOGGLE_ALARM = "rebalance_toggle_alarm"
    TOGGLE_AUTO_TRADING = "rebalance_toggle_auto_trading"


class UnregisterStates(Enum):
    START = "rebalance_unregister_start"
    CONFIRM = "rebalance_unregister_confirm"


class SelectStates(Enum):
    START = "rebalance_select_start"
    CHANGE = "rebalance_select_change"


class PnlStates(Enum):
    START = "rebalance_pnl_start"
    CHANGE = "rebalance_pnl_change"


class RefreshStates(Enum):
    START = "rebalance_refresh_start"
