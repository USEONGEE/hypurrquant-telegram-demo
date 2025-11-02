from telegram.ext import (
    ContextTypes,
)

from hypurrquant.models.perp_market_data import (
    MarketData as PerpMarketData,
)
from hypurrquant.logging_config import configure_logging
from handler.utils.settings import SettingMixin, setting_paths
from handler.command import Command
from .pagination import PerpMarketDataPagination

from pydantic import BaseModel
from typing import Optional

logger = configure_logging(__name__)


class _PerpOneSetting(BaseModel, SettingMixin):
    _return_to: str = Command.PERP_ONE

    class Config:
        arbitrary_types_allowed = True  # 사용자 정의 타입 허용


@setting_paths("perp_one", "perp_one")
class PerpOneSetting(_PerpOneSetting):
    _return_to: str = Command.HYPERLIQUID_CORE_START

    perp_market_data_pagination: PerpMarketDataPagination = None
    position: Optional[str] = None
    leverage: Optional[int] = None
    selected_ticker: Optional[PerpMarketData] = None
