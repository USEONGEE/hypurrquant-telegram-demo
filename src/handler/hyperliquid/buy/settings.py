from telegram.ext import (
    ContextTypes,
)

from hypurrquant.logging_config import configure_logging
from hypurrquant.models.market_data import MarketData
from handler.command import Command
from handler.utils.settings import SettingMixin, setting_paths
from api.hyperliquid import StrategyMeta
from .model.orderable_market_data import OrderableMarketData
from .pagenations import (
    MarketDataPagination,
    ConfirmPagination,
)

from pydantic import BaseModel
from typing import List, Optional, Dict, Any

logger = configure_logging(__name__)


class _BuySetting(BaseModel, SettingMixin):
    _return_to: str = Command.BUY

    class Config:
        arbitrary_types_allowed = True  # 사용자 정의 타입 허용


@setting_paths("buy", "buy")
class BuySetting(_BuySetting):
    """
    하위 Market Cap 종목을 선택하고 관련 정보를 저장하는 Pydantic 모델 클래스.
    """

    _return_to: str = Command.HYPERLIQUID_CORE_START
    filterd_stocks: Optional[List[MarketData]] = None
    orderable_market_data: Optional[List[OrderableMarketData]] = None


@setting_paths("buy", "strategy")
class StrategySetting(_BuySetting):
    strategies: Optional[Dict[str, StrategyMeta]] = None
    chosen_strategy_key: Optional[str] = None
    param_keys: Optional[List[str]] = None
    param_index: Optional[int] = 0
    collected_params: Optional[Dict[str, Any]] = None


@setting_paths("buy", "stock_select")
class StockSelectSetting(_BuySetting):
    """
    stock_select 대화(Conversation)에서 사용할 임시 상태를 저장
    """

    pagination: Optional[MarketDataPagination] = None


@setting_paths("buy", "order")
class OrderSetting(_BuySetting):
    """
    stock_select 대화(Conversation)에서 사용할 임시 상태를 저장
    """

    pagination: Optional[ConfirmPagination] = None
