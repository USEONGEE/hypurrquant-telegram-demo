from ..utils import BASE_URL, DEFAULT_SLIPPAGE, send_request
from ..models import BaseResponse
from .models import OrderData
from hypurrquant.logging_config import configure_logging
from hypurrquant.utils.singleton import Singleton

_logger = configure_logging(__name__)


# ================================
# 구매 주문 서비스
# ================================
class PerpOrderService(metaclass=Singleton):

    async def open_market(
        self, telegram_id: str, tickers: list, slippage: float = DEFAULT_SLIPPAGE
    ) -> OrderData:
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/order/perp/open/market",
            json={
                "telegram_id": str(telegram_id),
                "tickers": tickers,
                "slippage": slippage,
            },
        )
        return OrderData(**(response.data))

    async def open_grid(
        self,
        telegram_id: str,
        ticker: str,
        start_price: float,
        end_price: float,
        total_value,
        count: int,
        is_long: bool,
        leverage: int,
    ) -> OrderData:
        """
        선물 거래 그리드 주문을 실행합니다.

        Parameters:
            telegram_id (str): 텔레그램 사용자 ID.
            ticker (str): 상품 심볼.
            grid_prices (list): 그리드 가격 리스트.
            is_long (bool): 매수/매도 여부.
            is_cross (bool): 크로스/아이솔레이트 여부.
            leverage (int): 레버리지.

        Returns:
            OrderData: 주문 결과 데이터.
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/order/perp/open/grid",
            json={
                "telegram_id": str(telegram_id),
                "ticker": ticker,
                "is_long": is_long,
                "leverage": leverage,
                "start_price": start_price,
                "end_price": end_price,
                "total_value": total_value,
                "count": count,
            },
        )
        return OrderData(**(response.data))

    # close
    async def close(self, telegram_id: str, ticker_name: str) -> OrderData:
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/order/perp/close",
            json={
                "telegram_id": str(telegram_id),
                "name": ticker_name,
            },
        )
        return OrderData(**(response.data))

    # close all3
    async def close_all(self, telegram_id: str) -> OrderData:
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/order/perp/close/all",
            json={
                "telegram_id": str(telegram_id),
            },
        )
        return OrderData(**(response.data))

    async def close_grid(
        self,
        telegram_id: str,
        ticker: str,
        start_price: float,
        end_price: float,
    ) -> OrderData:
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/order/perp/close/grid",
            json={
                "telegram_id": str(telegram_id),
                "ticker": ticker,
                "start_price": start_price,
                "end_price": end_price,
            },
        )
        return OrderData(**(response.data))
