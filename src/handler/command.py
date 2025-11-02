from enum import Enum


class Command(str, Enum):
    START = "start"
    HYPERLIQUID_CORE_START = "hl_start"
    BUY = "spot_buy_strategy"
    BUY_ONE = "spot_buy"
    SELL = "spot_sell"
    PERP_ONE = "perp_open"
    CLOSE = "perp_close"
    REBALANCE = "alarm"
    COPY_TRADING = "copy_trading"
    DCA = "dca"
    GRID = "grid"
    DELTA = "delta_neutral"
    BALANCE = "balance"
    WALLET = "wallet"
    REFERRAL = "referral"
    LPVAULT_AUTO = "lpvault_auto"
    EVM_BALANCE = "evm_balance"

    def __str__(self) -> str:  # f-string에서 값이 나오게
        return self.value
