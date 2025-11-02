from hypurrquant.utils.singleton import singleton
from ..utils import send_request, BASE_URL
from .models import RebalanceDetailDto
from ..models import BaseResponse
from hypurrquant.logging_config import configure_logging


# ================================
# 설정 정보
# ================================
_logger = configure_logging(__name__)


# ================================
# 계좌 정보 서비스
# ================================
@singleton
class RebalanceService:
    async def register_rebalance_account(self, telegram_id, nickname):
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/rebalance/register",
            json={"telegram_id": str(telegram_id), "nickname": nickname},
        )
        return response.data

    async def unregister_rebalance_account(self, telegram_id, nickname):
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/rebalance/unregister",
            json={"telegram_id": str(telegram_id), "nickname": nickname},
        )
        return response.data

    async def get_rebalance_detail(self, telegram_id):
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/rebalance/detail?telegram_id={telegram_id}",
        )
        return RebalanceDetailDto(**(response.data))

    async def update_target_pnl_percent_rebalancing(
        self, telegram_id: str, target_pnl_percent: float
    ):
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/rebalance/detail/target_pnl_percent",
            json={
                "telegram_id": str(telegram_id),
                "target_pnl_percent": target_pnl_percent,
            },
        )
        return response.data

    async def update_pnl_alarm_toggle_rebalancing(self, telegram_id: str):
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/rebalance/detail/pnl_alarm_toggle",
            json={"telegram_id": str(telegram_id)},
        )
        return response.data

    async def update_auto_trading_toggle_rebalancing(self, telegram_id: str):
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/rebalance/detail/auto_trading_toggle",
            json={"telegram_id": str(telegram_id)},
        )
        return response.data
