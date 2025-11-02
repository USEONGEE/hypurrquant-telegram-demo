from api.hyperliquid import TimeBaseDCADict
from hypurrquant.logging_config import configure_logging
from handler.utils.settings import SettingMixin, setting_paths
from handler.command import Command

from pydantic import BaseModel
from typing import Optional, List

logger = configure_logging(__name__)


class _DcaSetting(BaseModel, SettingMixin):
    _return_to: str = Command.DCA

    class Config:
        arbitrary_types_allowed = True  # 사용자 정의 타입 허용


@setting_paths("dca", "dca")
class DcaSetting(_DcaSetting):
    """
    Base class for DCA settings.
    This class can be extended for different types of DCA settings.
    """

    _return_to: str = Command.HYPERLIQUID_CORE_START

    dca_spot_list: List[TimeBaseDCADict] = []


@setting_paths("dca", "dca_timeslice_spot")
class DcaTimesliceSpotSetting(_DcaSetting):
    ticker: Optional[str] = None  # 거래 종목 심볼
    amount: Optional[float] = None  # 주문당 금액
    interval_seconds: Optional[int] = None  # 다음 주문까지 대기할 시간(초)
    remaining_count: Optional[int] = None  # 남은 주문 횟수
    is_buy: Optional[bool] = None  # 매수 여부
    type: str = "spot"  # 거래 타입, 기본값은 'spot'


@setting_paths("dca", "dca_delete_spot")
class DcaDeleteSpotSetting(_DcaSetting):
    """
    DCA Delete Spot Setting class to manage DCA deletion settings.
    """

    delete_index: Optional[int] = None  # Index of the DCA to delete
