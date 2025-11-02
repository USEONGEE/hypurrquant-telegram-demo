from telegram.ext import (
    ContextTypes,
)

from hypurrquant.logging_config import configure_logging
from handler.utils.settings import SettingMixin, setting_paths
from handler.command import Command
from handler.models.perp_balance import Position, PositionDetail
from .pagination import ClosableOrderPagination

from pydantic import BaseModel
from typing import Optional

logger = configure_logging(__name__)


class _CloseSetting(BaseModel, SettingMixin):
    _return_to: str = Command.CLOSE

    class Config:
        arbitrary_types_allowed = True  # 사용자 정의 타입 허용


@setting_paths("close", "close")
class CloseSetting(_CloseSetting):
    _return_to: str = Command.HYPERLIQUID_CORE_START
    sellable_balance: Optional[Position] = None
    unsellable_balance: Optional[Position] = None


@setting_paths("close", "close_one")
class CloseOneSetting(_CloseSetting):
    selected_stock: Optional[PositionDetail] = None
    closable_order_pagination: Optional[ClosableOrderPagination] = None
