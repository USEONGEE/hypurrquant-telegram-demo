from enum import Enum


class BalanceStates(Enum):
    SELECT_ACTION = "balance_select_action"


class PerpToSpotStates(Enum):
    START = "balance_perp_to_spot_start"
    PERP_TO_SPOT = "balance_perp_to_spot"


class SpotToPerpStates(Enum):
    START = "balance_spot_to_perp_start"
    SPOT_TO_PERP = "balance_spot_to_perp"


class SpotDetailStates(Enum):
    START = "balance_spot_detail_start"
    PAGE = "balance_spot_detail_page"
    DETAIL = "balance_spot_detail"
    GO_BACK = "balance_spot_detail_go_back"


class PerpDetailStates(Enum):
    START = "balance_perp_detail_start"
    PAGE = "balance_perp_detail_page"
    DETAIL = "balance_perp_detail"
    GO_BACK = "balance_perp_detail_go_back"


class SendUsdcStates(Enum):
    START = "balance_send_start"
    SELEC_WALLET_TYPE = "balance_send_select_wallet_type"
    SELECT_ACCOUNT = "balance_send_select_account"
    SELECT_AMOUNT = "balance_send_select_amount"


class RefreshStates(Enum):
    START = "balance_refresh_start"
