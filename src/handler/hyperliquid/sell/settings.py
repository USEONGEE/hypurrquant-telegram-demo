from telegram.ext import (
    ContextTypes,
)

from hypurrquant.logging_config import configure_logging
from handler.models.spot_balance import SpotBalance
from handler.utils.settings import SettingMixin, setting_paths
from handler.command import Command
from .pagenation import SellableOrderPagination

from pydantic import BaseModel
from typing import List, Optional

logger = configure_logging(__name__)


class _SellSetting(BaseModel, SettingMixin):
    _return_to: str = Command.SELL

    class Config:
        arbitrary_types_allowed = True


@setting_paths("sell", "sell")
class SellSetting(_SellSetting):
    """
    하위 Market Cap 종목을 선택하고 관련 정보를 저장하는 Pydantic 모델 클래스.
    """

    _return_to: str = Command.HYPERLIQUID_CORE_START

    sellable_balance: Optional[List[SpotBalance]] = None
    unsellable_balance: Optional[List[SpotBalance]] = None


@setting_paths("sell", "specific")
class SellSepcificSetting(_SellSetting):
    sellable_order_pagination: Optional[SellableOrderPagination] = None


@setting_paths("sell", "all")
class SellAllSetting(_SellSetting):
    pass
