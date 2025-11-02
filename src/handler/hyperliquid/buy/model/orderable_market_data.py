from pydantic import BaseModel
from typing import Optional
from hypurrquant.models.market_data import MarketData

from hypurrquant.logging_config import configure_logging

logger = configure_logging(__name__)


class OrderableMarketData(BaseModel):
    Tname: str  # CHEF -> ticker
    midPx: float
    MarketCap: float
    dayNtlVlm: float
    change_24h: float
    change_24h_pct: float
    sector: Optional[str] = None

    is_buy: Optional[bool] = True
    value: Optional[float] = None

    @classmethod
    def from_market_data(cls, market_data: MarketData) -> "OrderableMarketData":
        logger.info(f"OrderableMarketData.from_market_data: {market_data}")
        return cls(
            Tname=market_data.Tname,
            midPx=market_data.midPx,
            MarketCap=market_data.MarketCap,
            dayNtlVlm=market_data.dayNtlVlm,
            change_24h=market_data.change_24h,
            change_24h_pct=market_data.change_24h_pct,
            sector=market_data.sector,
        )

    def set_buy(self, boolean: bool):
        self.is_buy = boolean

    def set_value(self, value: float):
        self.value = value
