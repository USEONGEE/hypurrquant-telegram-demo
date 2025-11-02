from telegram.ext import (
    ContextTypes,
)


from api import ReferralSummaryDict
from handler.referral.pagination import ReferralDetailPagination
from handler.command import Command
from handler.utils.settings import SettingMixin, setting_paths
from hypurrquant.logging_config import configure_logging

from pydantic import BaseModel
from typing import Optional

logger = configure_logging(__name__)


class _ReferralSetting(BaseModel, SettingMixin):
    _return_to: str = Command.REFERRAL

    class Config:
        arbitrary_types_allowed = True  # 사용자 정의 타입 허용


@setting_paths("referral", "referral")
class ReferralSetting(_ReferralSetting):
    """
    ReferralDetailSetting은 사용자의 ReferralDetail 설정을 관리하는 클래스입니다.
    """

    _return_to: str = Command.START
    summary: Optional[ReferralSummaryDict] = None


@setting_paths("referral", "detail")
class ReferralDetailSetting(_ReferralSetting):
    """
    하위 Market Cap 종목을 선택하고 관련 정보를 저장하는 Pydantic 모델 클래스.
    """

    pagination: Optional[ReferralDetailPagination] = None
