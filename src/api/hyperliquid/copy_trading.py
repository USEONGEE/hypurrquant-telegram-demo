from hypurrquant.logging_config import configure_logging
from ..utils import BASE_URL, send_request
from hypurrquant.utils.singleton import Singleton
from ..models import BaseResponse
from .models import (
    OrderData,
    SubscribersCountResponse,
    ListSubscriptionsResponse,
)
from typing import List


_logger = configure_logging(__name__)


# ================================
# 구매 주문 서비스
# ================================
class CopytradingService(metaclass=Singleton):
    async def subscribe(self, public_key: str, target_public_key: str) -> OrderData:

        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/copytrading/subscription/subscribe",
            json={"subscriber": public_key, "target": target_public_key},
        )
        _logger.info(f"subscribe response: {response}")
        return response.data

    async def unsubscribe(self, public_key: str, target_public_key: str):

        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/copytrading/subscription/unsubscribe",
            json={"subscriber": public_key, "target": target_public_key},
        )
        return response.data

    async def get_subscribers_by_target(self, public_key: str) -> List[str]:
        """
        특정 타켓을 구독하는 구독자 목록 조회
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/copytrading/subscription/subscribers",
            params={"subscriber": public_key},
        )
        return response.data

    async def get_targets_by_subscriber(self, public_key: str) -> List[str]:
        """
        get_subscription_by_subscriber
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/copytrading/subscription/subscribe?public_key={public_key}",
        )
        return response.data

    async def count_subscription(self) -> SubscribersCountResponse:
        """
        구독자 목록 조회
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/copytrading/subscription/count",
        )
        return response.data

    async def page_subscription(
        self, page: int = 1, page_size: int = 15
    ) -> ListSubscriptionsResponse:
        """
        구독자 목록 조회
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/copytrading/subscription/list",
            params={"page": page, "page_size": page_size},
        )
        return response.data

    # ================================
    async def register_copytrading_account(self, telegram_id: str, nickname: str):
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/copytrading/register",
            json={"telegram_id": str(telegram_id), "nickname": nickname},
        )
        return response.data

    async def unregister_copytrading_account(self, telegram_id: str, nickname: str):
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/copytrading/unregister",
            json={"telegram_id": str(telegram_id), "nickname": nickname},
        )
        return response.data

    async def update_target_pnl_percent_copytrading(
        self, telegram_id: str, target_pnl_percent: float
    ):
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/copytrading/detail/target_pnl_percent",
            json={
                "telegram_id": str(telegram_id),
                "target_pnl_percent": target_pnl_percent,
            },
        )
        return response.data

    async def update_sell_type_copytrading(self, telegram_id: str, close_strategy: str):
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/copytrading/detail/sell_type",
            json={
                "telegram_id": str(telegram_id),
                "close_strategy": close_strategy,
            },
        )
        return response.data

    async def update_order_value_usdc_copytrading(
        self, telegram_id: str, order_value_usdc: float
    ):
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/copytrading/detail/order_value_usdc",
            json={
                "telegram_id": str(telegram_id),
                "order_value_usdc": order_value_usdc,
            },
        )
        return response.data

    async def update_leverage_copytrading(self, telegram_id: str, leverage: int):
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/copytrading/detail/leverage",
            json={
                "telegram_id": str(telegram_id),
                "leverage": int(leverage),
            },
        )
        return response.data
