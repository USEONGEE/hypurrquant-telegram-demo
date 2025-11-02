from ..utils import BASE_URL, send_request
from hypurrquant.utils.singleton import Singleton
from hypurrquant.logging_config import configure_logging


_logger = configure_logging(__name__)


# ================================
# 구매 주문 서비스
# ================================
class DeltaOrderService(metaclass=Singleton):

    async def market_open(
        self,
        telegram_id: str,
        nickname: list,
        ticker: str,
        total_usdc: float,
    ) -> bool:
        await send_request(
            "POST",
            f"{BASE_URL}/order/delta-neutral/open/market",
            json={
                "telegram_id": str(telegram_id),
                "nickname": nickname,
                "ticker": ticker,
                "total_usdc": total_usdc,
            },
        )
        return True

    async def market_close(self, telegram_id: str, nickname: str, ticker: str) -> bool:
        await send_request(
            "POST",
            f"{BASE_URL}/order/delta-neutral/close/market",
            json={
                "telegram_id": str(telegram_id),
                "nickname": nickname,
                "ticker": ticker,
            },
        )
        return True
