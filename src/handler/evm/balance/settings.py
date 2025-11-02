from hypurrquant.logging_config import configure_logging

from api import EvmBalanceItemDto
from handler.command import Command
from handler.utils.settings import SettingMixin, setting_paths
from handler.command import Command
from .pagination import EvmBalancePagination, EvmSendPagination
from pydantic import BaseModel
from typing import Optional

logger = configure_logging(__name__)


class _EvmBalanceSetting(BaseModel, SettingMixin):
    _return_to: str = Command.EVM_BALANCE

    class Config:
        arbitrary_types_allowed = True


@setting_paths("evm_balance", "evm_balance")
class EvmBalanceSetting(_EvmBalanceSetting):
    """
    Base class for EvmBalance settings.
    This class can be extended for different types of EvmBalance settings.
    """

    pagination: Optional[EvmBalancePagination] = None
    _return_to: str = Command.START


@setting_paths("evm_balance", "send")
class SendUsdcSetting(_EvmBalanceSetting):
    """
    Settings for sending USDC in EVM balance context.
    """

    pagination: Optional[EvmSendPagination] = None
    destination_address: Optional[str] = None
    selected_item: Optional[EvmBalanceItemDto] = None
    amount: Optional[int] = None
