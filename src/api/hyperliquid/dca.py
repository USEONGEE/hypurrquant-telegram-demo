from ..utils import BASE_URL, send_request
from hypurrquant.utils.singleton import Singleton

from ..models import BaseResponse
from .models import TimeBaseDCADict
from hypurrquant.logging_config import configure_logging
from typing import List


_logger = configure_logging(__name__)


# ================================
# 구매 주문 서비스
# ================================
class DcaService(metaclass=Singleton):

    async def register_timeslice_spot(
        self,
        public_key: str,
        ticker,
        amount: float,
        interval_seconds: int,
        remaining_count: int,
        is_buy: bool,
    ) -> bool:
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/dca/time-slice/spot",
            json={
                "public_key": public_key,
                "ticker": ticker,
                "amount": amount,
                "interval_seconds": interval_seconds,
                "remaining_count": remaining_count,
                "is_buy": is_buy,
            },
        )
        return response.data

    async def get_timeslice_spot_list(self, public_key: str) -> List[TimeBaseDCADict]:
        response: BaseResponse = await send_request(
            "GET", f"{BASE_URL}/dca/time-slice/spot?public_key={public_key}"
        )
        return response.data

    async def delete_timeslice_spot(self, dca_id: str) -> bool:
        response: BaseResponse = await send_request(
            "DELETE", f"{BASE_URL}/dca/time-slice/spot?id={dca_id}"
        )
        return response.data
