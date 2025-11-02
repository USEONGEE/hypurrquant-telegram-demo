from telegram.ext import (
    ContextTypes,
)

from hypurrquant.logging_config import configure_logging
from hypurrquant.models.account import Account
from handler.utils.settings import SettingMixin, setting_paths
from handler.command import Command
from pydantic import BaseModel
from typing import List, Optional

logger = configure_logging(__name__)


class _RebalanceSettings(SettingMixin, BaseModel):
    _return_to: str = Command.REBALANCE

    class Config:
        arbitrary_types_allowed = True


@setting_paths("rebalance", "rebalance")
class RebalanceSetting(_RebalanceSettings):
    _return_to: str = Command.HYPERLIQUID_CORE_START

    account: Optional[Account] = None
