from hypurrquant.logging_config import configure_logging

from api import DexInforesponse, LpvaultSettingsDict
from hypurrquant.models.account import Account
from handler.command import Command
from handler.utils.settings import SettingMixin, setting_paths
from handler.command import Command

from pydantic import BaseModel
from typing import Optional, List

logger = configure_logging(__name__)


class _LpVaultSetting(BaseModel, SettingMixin):
    _return_to: str = Command.LPVAULT_AUTO

    class Config:
        arbitrary_types_allowed = True


@setting_paths("lpvault", "lpvault")
class LpvaultSetting(_LpVaultSetting):
    """
    Base class for Lpvault settings.
    This class can be extended for different types of Lpvault settings.
    """

    _return_to: str = Command.START
    account: Optional[Account] = None


@setting_paths("lpvault", "register")
class LpvaultRegisterSetting(_LpVaultSetting):
    """
    Settings for Lpvault registration.
    """

    _all_dex_infos: Optional[List[DexInforesponse]]
    dex_info: Optional[DexInforesponse] = None
    all_pool_configs: Optional[List[dict]] = None
    config_index: Optional[int] = None
    upper_range_pct: Optional[float] = None
    lower_range_pct: Optional[float] = None
    aggregator: Optional[str] = None
    swap_target_token_ticker: Optional[str] = None
    swap_target_token_address: Optional[str] = None
    auto_claim: Optional[bool] = None

    # lpvault setting
    lpvault_settings: Optional[LpvaultSettingsDict] = None


@setting_paths("lpvault", "manual_mint")
class LpvaultManualMintSetting(LpvaultRegisterSetting): ...


@setting_paths("lpvault", "bridge_wrap")
class LpvaultBridgeWrapSetting(_LpVaultSetting):
    """
    Settings for Lpvault bridge wrap.
    """

    spot_usdc: Optional[float] = None
    perp_usdc: Optional[float] = None
    spot_hype: Optional[float] = None
    evm_hype: Optional[float] = None

    selected_ticker: Optional[str] = None


@setting_paths("lpvault", "bridge_unwrap")
class LpvaultBridgeUnwrapSetting(_LpVaultSetting):
    """
    Settings for Lpvault bridge unwrap.
    """

    whype: Optional[float] = None


@setting_paths("lpvault", "swap")
class LpvaultSwapSetting(_LpVaultSetting):
    tokens: dict = []
    amount_percentage: Optional[int] = None
    selected_in_token: Optional[str] = None
    selected_out_token: Optional[str] = None
    selected_aggregator: Optional[str] = None
    swap_routes: dict = {}


@setting_paths("lpvault", "settings")
class LpvaultSettingsSetting(_LpVaultSetting):
    setting: LpvaultSettingsDict = Optional[dict]
