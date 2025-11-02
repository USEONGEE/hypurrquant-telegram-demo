from telegram.ext import (
    ContextTypes,
)
from hypurrquant.logging_config import configure_logging
from handler.utils.settings import SettingMixin, setting_paths
from handler.command import Command
from hypurrquant.models.account import Account
from .pagination import SubscriptionPagination

from pydantic import BaseModel
from typing import Optional

logger = configure_logging(__name__)


class _CopytradingSettingMixin(BaseModel, SettingMixin):
    _return_to: str = Command.COPY_TRADING

    class Config:
        arbitrary_types_allowed = True  # 사용자 정의 타입 허용


@setting_paths("copytrading", "copytrading")
class CopytradingSetting(_CopytradingSettingMixin):
    _return_to: str = Command.HYPERLIQUID_CORE_START
    account: Optional[Account] = None


@setting_paths("copytrading", "follow")
class FollowSetting(_CopytradingSettingMixin):
    pagination: Optional[SubscriptionPagination] = None
