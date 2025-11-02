from typing import TypedDict, List
from datetime import datetime
from typing_extensions import Literal


class ReferralDetailDict(TypedDict):
    public_key: str
    total_earned: float
    paid_amount: float
    unpaid_amount: float
    first_ts: datetime
    last_ts: datetime
    last_paid_ts: datetime


class ReferralSummaryDict(TypedDict):
    num_referees: int
    total_earned: float
    total_paid: float
    total_unpaid: float
    details: List[ReferralDetailDict]


class EvmBalanceItemDto(TypedDict):
    ticker: str
    address: str
    raw_amount: int
    decimal: int
    decimal_amount: float


class EvmBalanceDto(TypedDict):
    native: EvmBalanceItemDto
    wrapped: EvmBalanceItemDto
    erc20: dict[str, EvmBalanceItemDto]


# ================================
# 계좌 정보 DTO
# ================================
class AccountDto:
    def __init__(self, nickname, public_key, is_active, is_approved_builder_fee):
        self.nickname = nickname
        self.public_key = public_key
        self.is_active = is_active
        self.is_approved_builder_fee = is_approved_builder_fee
