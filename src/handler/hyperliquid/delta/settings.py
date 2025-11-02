from hypurrquant.logging_config import configure_logging
from handler.utils.settings import SettingMixin, setting_paths
from handler.command import Command
from hypurrquant.models.account import Account
from .pagination import (
    DeltaSymbolPagination,
    DeltaClosePagination,
)

from pydantic import BaseModel
from typing import Optional

logger = configure_logging(__name__)


class _DeltaSettingMixin(BaseModel, SettingMixin):
    _return_to: str = Command.DELTA

    class Config:
        arbitrary_types_allowed = True


@setting_paths("delta", "delta")
class DeltaSetting(_DeltaSettingMixin):
    """
    Base class for delta settings.
    This class can be extended for different types of delta settings.
    """

    _return_to: str = Command.HYPERLIQUID_CORE_START

    pagination: Optional[DeltaSymbolPagination] = None
    close_pagination: Optional[DeltaClosePagination] = None
    total_usdc: Optional[float] = None


@setting_paths("delta", "delta_open")
class DeltaOpenSetting(_DeltaSettingMixin):
    """
    Settings specific to the Delta Open operation.
    This class can be extended for more specific delta open settings.
    """

    ticker: Optional[Account] = None


@setting_paths("delta", "delta_close")
class DeltaCloseSetting(_DeltaSettingMixin):
    """
    Settings specific to the Delta Close operation.
    This class can be extended for more specific delta close settings.
    """

    ticker: Optional[Account] = None
