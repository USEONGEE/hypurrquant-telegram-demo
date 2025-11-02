from hypurrquant.utils.singleton import Singleton
from ..utils import send_request, BASE_URL, DEFAULT_SLIPPAGE
from ..models import BaseResponse
from .models import OrderData
from hypurrquant.logging_config import configure_logging


logger = configure_logging(__name__)


# ================================
# 구매 주문 서비스
# ================================
class BuyOrderService(metaclass=Singleton):

    async def buy_order_market_usdc(
        self,
        telegram_id: str,
        tickers: list,
        slippage: float = DEFAULT_SLIPPAGE,
        *,
        charge_builder_fee: bool = True,
    ) -> OrderData:
        """
        Market 주문을 넣는 메서드

        Parameters:
            telegram_id (str): telegram_id
            tickers (list of dict): 예시:
                [
                    {
                        "name": "HYPE",
                        "value": 50.0 -> USDC
                    },
                    {
                        "name": "COOL",
                        "value": 100.0 -> USDC
                    }
                ]
                - **name** (str): 티커 이름
                - **value** (float): 주문 금액(USDC)
            slippage(flaot) : 슬리피지 사이즈
        """

        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/order/buy/market",
            params={"charge_builder_fee": str(charge_builder_fee)},
            json={
                "telegram_id": str(telegram_id),
                "tickers": tickers,
                "slippage": slippage,
            },
        )
        return OrderData(**(response.data))

    async def buy_order_limit_usdc(
        self,
        telegram_id,
        tickers: list,
        *,
        charge_builder_fee: bool = True,
    ):
        """
        buy_order_limit_usdc : Limit 주문을 넣는 메서드

        Args:
            telegram_id (_type_): telegram_id
            tickers (list of dict): 예시:
                [
                    {
                        "name": "HYPE",
                        "limit_px": 24.0
                        "value": 50.0, -> USDC
                    },
                    {
                        "name": "COOL",
                        "limit_px": 24.0
                        "value": 100.0 -> USDC
                    }
                ]
                - **name** (str): 티커 이름
                - **limit_px** (float): 제한 가격
                - **value** (float): 주문 금액(USDC)
        Returns:
            _type_: _description_
        """

        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/order/buy/limit",
            params={"charge_builder_fee": str(charge_builder_fee)},
            json={"telegram_id": str(telegram_id), "tickers": tickers},
        )
        return OrderData(**(response.data))

    async def grid_spot_buy(
        self,
        telegram_id: str,
        ticker: str,
        start_price: float,
        end_price: float,
        total_value: float,
        count: int,
        *,
        charge_builder_fee: bool = True,
    ) -> None:
        """
        Grid Spot Buy 실행 API 호출

        Args:
            telegram_id (str): 텔레그램 사용자 ID
            ticker (str): 거래 자산 심볼 (예: "HYPE")
            start_price (float): 그리드 시작 가격
            end_price (float): 그리드 종료 가격
            total_value (float): 총 매수할 USDC 금액
            count (int): 그리드 분할 개수

        Returns:
            OrderData: API에서 반환하는 주문 데이터
        """
        # 1) 요청 페이로드 조립
        payload = {
            "telegram_id": telegram_id,
            "ticker": ticker,
            "start_price": start_price,
            "end_price": end_price,
            "total_value": total_value,
            "count": count,
        }
        # 2) POST 호출
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/order/buy/grid",
            params={"charge_builder_fee": str(charge_builder_fee)},
            json=payload,
        )

        # 3) 응답 데이터 파싱
        return OrderData(**response.data)
