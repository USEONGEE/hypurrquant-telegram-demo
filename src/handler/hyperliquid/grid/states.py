from enum import Enum


class GridState(Enum):
    SELECT_ACTION = "grid_start_select_action"


class GridSpotBuyState(Enum):
    START = "grid_spot_buy_start"
    TYPING = "grid_spot_buy_typing"
    CONFIRM = "grid_spot_buy_confirm"


class GridSpotSellState(Enum):
    START = "grid_spot_sell_start"
    TYPING = "grid_spot_sell_typing"
    CONFIRM = "grid_spot_sell_confirm"


class GridCancelState(Enum):
    START = "grid_cancel_start"
    CONFIRM = "grid_cancel_confirm"


class GridPerpOpenState(Enum):
    START = "grid_perp_open_start"
    TYPING = "grid_perp_open_typing"
    CONFIRM = "grid_perp_open_confirm"


class GridPerpCloseState(Enum):
    START = "grid_perp_close_start"
    TYPING = "grid_perp_close_typing"
    CONFIRM = "grid_perp_close_confirm"


class GridStatusState(Enum):
    START = "grid_status_start"
