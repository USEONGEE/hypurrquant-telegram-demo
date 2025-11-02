from telegram.ext import (
    ContextTypes,
)

from hypurrquant.models.market_data import MarketData
from .pagination import MarketDataPagination
from hypurrquant.logging_config import configure_logging
from handler.utils.settings import SettingMixin, setting_paths
from handler.command import Command

from pydantic import BaseModel
from typing import Optional

logger = configure_logging(__name__)


class _BuyOneSetting(BaseModel, SettingMixin):
    CALLBACK_COMMAND: str = Command.BUY_ONE

    class Config:
        arbitrary_types_allowed = True  # 사용자 정의 타입 허용


@setting_paths("buy_one", "buy_one")
class BuyOneSetting(_BuyOneSetting):
    """
    하위 Market Cap 종목을 선택하고 관련 정보를 저장하는 Pydantic 모델 클래스.
    """

    CALLBACK_COMMAND: str = Command.HYPERLIQUID_CORE_START
    market_data_pagination: MarketDataPagination = None
    selected_ticker: Optional[MarketData] = None
