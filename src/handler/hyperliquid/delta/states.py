from enum import Enum


class DeltaState(Enum):
    SELECT_ACTION = "delta_start_select_action"


class DeltaOpenState(Enum):
    START = "delta_open_select_ticker"
    PAGE = "delta_open_page"
    AMOUNT_INPUT = "delta_open_amount_input"


class DeltaCloseState(Enum):
    START = "delta_close_select_ticker"
    PAGE = "delta_close_page"
    CONFIRMATION = "delta_close_confirmation"
