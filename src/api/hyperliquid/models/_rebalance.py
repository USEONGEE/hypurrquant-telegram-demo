from pydantic import BaseModel


class RebalanceDetailDto(BaseModel):
    public_key: str
    target_pnl_percent: float
    pnl_alarm: str
    auto_trading: str
