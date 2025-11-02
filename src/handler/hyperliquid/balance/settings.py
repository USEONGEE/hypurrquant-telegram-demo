from telegram.ext import (
    ContextTypes,
)


from .pagination import (
    SpotDetailPagination,
    PerpDetailPagination,
)
from hypurrquant.logging_config import configure_logging
from handler.command import Command
from handler.utils.settings import SettingMixin, setting_paths

from pydantic import BaseModel
from typing import Optional

logger = configure_logging(__name__)


class _BalanceSetting(BaseModel, SettingMixin):
    _return_to: str = Command.BALANCE

    class Config:
        arbitrary_types_allowed = True  # 사용자 정의 타입 허용


@setting_paths("balance", "balance")
class BalanceSetting(_BalanceSetting):
    """
    하위 Market Cap 종목을 선택하고 관련 정보를 저장하는 Pydantic 모델 클래스.
    """

    _return_to: str = Command.HYPERLIQUID_CORE_START


@setting_paths("balance", "spot_detail")
class SpotDetailSetting(_BalanceSetting):
    """
    Spot Detail 설정을 저장하는 Pydantic 모델 클래스.
    """

    spot_detail_pagination: Optional[SpotDetailPagination] = None


@setting_paths("balance", "perp_detail")
class PerpDetailSetting(_BalanceSetting):
    """
    Perp Detail 설정을 저장하는 Pydantic 모델 클래스.
    """

    perp_detail_pagination: Optional[PerpDetailPagination] = None


@setting_paths("balance", "send_usdc")
class SendUsdcSetting(_BalanceSetting):
    wallet_type: Optional[str] = None  # "perp | spot"
    destination: Optional[str] = None


@setting_paths("balance", "perp_to_spot")
class PerpToSpotSetting(_BalanceSetting):
    pass


@setting_paths("balance", "spot_to_perp")
class SpotToPerpSetting(_BalanceSetting):
    pass


@setting_paths("balance", "refresh")
class RefreshSetting(_BalanceSetting):
    pass
