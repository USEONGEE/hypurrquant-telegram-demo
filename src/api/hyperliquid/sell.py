from hyperliquid.info import Info

from ..utils import BASE_URL, DEFAULT_SLIPPAGE, send_request
from .models import OrderData
from ..models import BaseResponse
from hypurrquant.utils.singleton import Singleton


# ================================
# 판매 주문 서비스
# ================================
class SellOrderService(metaclass=Singleton):

    async def sell_order_limit(
        self,
        telegram_id,
        tickers: list,
        is_percent=True,
        *,
        charge_builder_fee: bool = True,
    ) -> OrderData:
        """
        sell_order_limit : Limit 주문을 넣는 메서드

        Args:
            telegram_id (str): telegram_id
            tickers (list of dict): 예시:
                [
                    {
                        "name": "HYPE",
                        "limit_px": 24.0,
                        "value": 50.0
                    },
                    {
                        "name": "COOL",
                        "limit_px": 10.0,
                        "value": 100.0
                    }
                ]
                - **name** (str): 티커 이름
                - **limit_px** (float): 제한 가격
                - **value** (float): 현재 보유 중인 자산에서 몇 퍼센트를 매도할지 명시
        Returns:
            orderRequest: 주문 결과
        """

        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/order/sell/limit",
            params={"charge_builder_fee": str(charge_builder_fee)},
            json={"telegram_id": str(telegram_id), "tickers": tickers},
        )
        return OrderData(**(response.data))

    async def sell_order_market(
        self,
        telegram_id,
        tickers: list,
        slippage: float = DEFAULT_SLIPPAGE,
        is_percent=True,
        *,
        charge_builder_fee: bool = True,
    ) -> OrderData:
        """
        Market sell 주문을 넣는 메서드

        Parameters:
            telegram_id (str): telegram_id
            tickers (list of dict): 예시:
                [
                    {
                        "name": "HYPE",
                        "value": 50.0
                    },
                    {
                        "name": "COOL",
                        "value": 100.0
                    }
                ]
                - **name** (str): 티커 이름
                - **value** (float): 현재 보유 중인 자산에서 몇 퍼센트를 매도할지 명시
                slippage(flaot) : 슬리피지 사이즈
        """

        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/order/sell/market",
            params={"charge_builder_fee": str(charge_builder_fee)},
            json={
                "telegram_id": str(telegram_id),
                "tickers": tickers,
                "slippage": slippage,
                "is_percent": is_percent,
            },
        )
        return OrderData(**(response.data))

    async def sell_order_market_all(
        self,
        telegram_id,
        slippage: float = DEFAULT_SLIPPAGE,
        *,
        charge_builder_fee: bool = True,
    ) -> OrderData:
        """
        잔고의 모든 SPOT 가상화폐를 판매하는 메서드

        Parameters:
            telegram_id (str): telegram_id
            slippage(flaot) : 슬리피지 사이즈
        """

        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/order/sell/market/all",
            params={"charge_builder_fee": str(charge_builder_fee)},
            json={"telegram_id": str(telegram_id), "slippage": slippage},
        )
        return OrderData(**(response.data))

    async def grid_spot_sell(
        self,
        telegram_id,
        ticker: str,
        start_price,
        end_price,
        *,
        charge_builder_fee: bool = True,
    ) -> OrderData:
        payload = {
            "telegram_id": str(telegram_id),
            "ticker": ticker.upper(),
            "start_price": start_price,
            "end_price": end_price,
        }
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/order/sell/grid",
            params={"charge_builder_fee": str(charge_builder_fee)},
            json=payload,
        )
        return OrderData(**(response.data))
