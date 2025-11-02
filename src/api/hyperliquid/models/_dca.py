from typing import TypedDict
from datetime import datetime
from typing_extensions import Literal


class TimeBaseDCADict(TypedDict):
    id: str  # alias에 따라 실제 JSON key는 _id
    public_key: str
    symbol: str
    type: Literal["spot", "perp"]
    is_buy: bool
    amount: float
    interval_seconds: int
    next_time: datetime
    remaining_count: int
