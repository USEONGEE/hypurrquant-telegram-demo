from enum import Enum


class SellStates(Enum):
    SELL = "sell"
    CANCEL = "cancel"


class AllStates(Enum):
    START = "sell_all_start"
    SELL = "sell_all"


class SpecificStates(Enum):
    START = "sell_specific_start"
    PAGE = "sell_specific_page"
    SELL = "sell_specific"
