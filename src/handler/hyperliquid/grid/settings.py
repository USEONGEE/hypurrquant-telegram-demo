from hypurrquant.logging_config import configure_logging
from handler.utils.settings import SettingMixin, setting_paths
from handler.command import Command

from pydantic import BaseModel
from typing import Optional

logger = configure_logging(__name__)


class _GridSetting(BaseModel, SettingMixin):
    _return_to: str = Command.GRID

    class Config:
        arbitrary_types_allowed = True  # 사용자 정의 타입 허용


@setting_paths("grid", "grid")
class GridSetting(_GridSetting):
    """
    Base class for grid settings.
    This class can be extended for different types of grid settings.
    """

    _return_to: str = Command.HYPERLIQUID_CORE_START


@setting_paths("grid", "spot_buy")
class GridSpotBuySetting(_GridSetting):
    ticker: Optional[str] = None
    start_price: Optional[float] = None
    end_price: Optional[float] = None
    total_value: Optional[float] = None
    count: Optional[int] = None


@setting_paths("grid", "spot_sell")
class GridSpotSellSetting(_GridSetting):
    ticker: Optional[str] = None
    start_price: Optional[float] = None
    end_price: Optional[float] = None


@setting_paths("grid", "perp_open")
class GirdPerpOpenSetting(_GridSetting):
    ticker: Optional[str] = None
    start_price: Optional[float] = None
    end_price: Optional[float] = None
    total_value: Optional[float] = None  # 총 매수 금액 (USDC)
    count: Optional[int] = None  # 그리드 개수
    is_long: Optional[bool] = None  # 매수 여부
    leverage: Optional[int] = None  # 레버리지


@setting_paths("grid", "perp_close")
class GridPerpCloseSetting(_GridSetting):
    ticker: Optional[str] = None
    start_price: Optional[float] = None
    end_price: Optional[float] = None
