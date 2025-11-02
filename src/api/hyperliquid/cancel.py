from ..utils import send_request, BASE_URL
from hypurrquant.logging_config import configure_logging
from hypurrquant.utils.singleton import Singleton

# ================================
# 설정 정보
# ================================
_logger = configure_logging(__name__)


# ================================
# 취소 주문 서비스
# ================================
class CancelOrderService(metaclass=Singleton):

    async def fetch_open_orders(self, telegram_id):
        """
        open_orders : 현재 주문 중인 주문을 조회하는 메서드

        Args:
            telegram_id (_type_): telegram_id

        Returns list:
            [
            {
                coin: str,
                limitPx: float string,
                oid: int,
                side: "A" | "B",
                sz: float string,
                timestamp: int
            }
        ]
        """
        return await send_request(
            "GET", f"{BASE_URL}/order/cancel/open_orders?telegram_id={telegram_id}"
        )

    async def cancle_open_order(self, telegram_id, oids: list):
        """
        cancle_open_orders : 주문 취소

        Args:
            telegram_id (_type_): telegram_id
            oids (list): [oid:int]

        Returns:
            _type_: _description_
        """

        return await send_request(
            "POST",
            f"{BASE_URL}/order/cancel/cancel_orders",
            json={"telegram_id": str(telegram_id), "oids": oids},
        )

    async def cancle_open_orders_all(self, telegram_id):
        """
        cancle_open_orders : open된 모든 spot 주문 취소

        Args:
            telegram_id (_type_): telegram_id
            oids (list): [oid:int]

        Returns:
            _type_: _description_
        """

        return await send_request(
            "POST",
            f"{BASE_URL}/order/cancel/cancel_all_orders",
            json={"telegram_id": str(telegram_id)},
        )
