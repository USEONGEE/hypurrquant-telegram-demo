from typing import TypedDict


class USDCBalanceItem(TypedDict):
    public_key: str
    nickname: str
    spot_usdc: float
    withdrawable: float


class USDCBalanceResult(TypedDict, total=False):
    spot_usdc: float
    withdrawable: float
