from enum import Enum


class CloseStates(Enum):
    CLOSE = "close_start_sell"
    CANCEL = "close_start_cancel"


class CloseAllStates(Enum):
    START = "close_all_start"
    CLOSE = "close_all_close"


class CloseOneStates(Enum):
    START = "close_one_start"
    PAGE = "close_one_page"
    CLOSE = "close_one_close"
    CONFIRM = "close_one_confirm"
