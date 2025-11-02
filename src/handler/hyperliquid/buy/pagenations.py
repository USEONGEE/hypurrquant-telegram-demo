from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .model.orderable_market_data import OrderableMarketData
from .utils import (
    get_needed_balance,
    is_sufficient_balance,
)
from handler.utils.pagenation import Pagenation
from hypurrquant.logging_config import configure_logging

from typing import List

logger = configure_logging(__name__)

MINIMUM_PER_ORDER = 20  # 최소 주문 금액 (USDC)


class MarketDataPagination(Pagenation):
    def __init__(
        self,
        market_data: List[OrderableMarketData],
        current_balance: float,
        page_size=15,
    ):
        """
        MarketDataPagination 초기화.

        Args:
            market_data (list): Market Data 리스트.
            page_size (int): 한 페이지에 표시할 데이터 개수. 기본값은 4.
        """
        self.current_balance = current_balance
        # 상위 생성자 호출
        super().__init__(market_data, page_size)

    async def generate_info_text(self) -> str:

        current_list: List[OrderableMarketData] = self.get_current_page_data()
        needed_balance: float = get_needed_balance(self.data)
        is_sufficient: bool = is_sufficient_balance(self.data, self.current_balance)
        logger.debug(f"if_sufficient: {is_sufficient}")

        response = f"The minimum average per stock is $20. \nIf you do not wish to buy or have insufficient balance, please adjust the number of stocks.\n\n"
        response += f"1️⃣ Current Balance: {self.current_balance}\n"
        response += f"2️⃣ Needed Balance: {needed_balance}\n"
        response += "3️⃣ Is it sufficient?  "
        response += f"{'✅' if is_sufficient else '❌'}\n\n"

        response += f"Page [{self.current_page + 1} / {self.total_pages}]"
        response += "```"
        response += "+----------+------------+----------+\n"
        response += "|  Ticker  |    Price   |  Select  |\n"
        response += "+----------+------------+----------+\n"

        for stock in current_list:
            response += (
                f"| {stock.Tname:<9}"  # 왼쪽 정렬, 폭 9
                f"| {stock.midPx:>11.5f}"  # 오른쪽 정렬, 폭 11, 소수점 5자리
                f"| {'   ✅   ' if stock.is_buy else '   ❌   '} |\n"  # 오른쪽 정렬, 폭 10, 소수점 2자리, 'K' 추가
            )
        response += "+----------+------------+----------+\n"
        response += "```\n"

        return response

    def generate_buttons(self, callback_prefix):
        """
        현재 페이지 데이터를 기반으로 InlineKeyboardMarkup 생성.

        Args:
            callback_prefix (str): 버튼 콜백 데이터에 사용할 prefix.

        Returns:
            InlineKeyboardMarkup: Telegram용 InlineKeyboard 버튼 레이아웃.
        """
        current_page_data = self.get_current_page_data()

        buttons = []
        row = []  # 한 행을 담는 임시 리스트

        for i, data in enumerate(current_page_data):
            display_name = f"✅ {data.Tname}" if data.is_buy else data.Tname
            row.append(
                InlineKeyboardButton(
                    display_name,
                    callback_data=f"{callback_prefix}_TOGGLE_{data.Tname}",
                )
            )

            # 3개가 쌓이면 새로운 행 추가
            if len(row) == 3:
                buttons.append(row)
                row = []

        # 남은 버튼 추가 (3개 미만인 경우)
        if row:
            buttons.append(row)

        # 페이지네이션 버튼 추가
        navigation_buttons = []
        if self.has_prev_page():
            navigation_buttons.append(
                InlineKeyboardButton("◀️ Prev", callback_data=f"{callback_prefix}_PREV")
            )
        if self.has_next_page():
            navigation_buttons.append(
                InlineKeyboardButton("Next ▶️", callback_data=f"{callback_prefix}_NEXT")
            )

        # 선택 완료 버튼 추가
        navigation_buttons.append(
            InlineKeyboardButton(
                "✅ Confirm", callback_data=f"{callback_prefix}_CONFIRM"
            )
        )

        if navigation_buttons:
            buttons.append(navigation_buttons)

        return InlineKeyboardMarkup(buttons)


class ConfirmPagination(Pagenation):
    def __init__(self, market_data: List[OrderableMarketData], page_size=15):
        """
        MarketDataPagination 초기화.

        Args:
            market_data (list): Market Data 리스트.
            page_size (int): 한 페이지에 표시할 데이터 개수. 기본값은 4.
        """
        # 상위 생성자 호출
        super().__init__(market_data, page_size)

    def generate_info_text(self) -> str:

        current_list: List[OrderableMarketData] = self.get_current_page_data()

        response = f"This is the final confirmation before placing your order. \nPlease review the stocks again.\n"
        response += f"Page [{self.current_page + 1} / {self.total_pages}]"
        response += "```"
        response += "+----------+------------+----------+\n"
        response += "|  Ticker  |    Price   |  Select  |\n"
        response += "+----------+------------+----------+\n"

        for stock in current_list:
            response += (
                f"| {stock.Tname:<9}"  # 왼쪽 정렬, 폭 9
                f"| {stock.midPx:>11.5f}"  # 오른쪽 정렬, 폭 11, 소수점 5자리
                f"| {'   ✅    |' }\n"  # 오른쪽 정렬, 폭 10, 소수점 2자리, 'K' 추가
            )
        response += "+----------+------------+----------+\n"
        response += "```\n"

        return response

    def generate_buttons(self, callback_prefix):
        # 페이지네이션 버튼 추가
        buttons = []
        navigation_buttons = []
        if self.has_prev_page():
            navigation_buttons.append(
                InlineKeyboardButton("◀️ Prev", callback_data=f"{callback_prefix}_PREV")
            )
        if self.has_next_page():
            navigation_buttons.append(
                InlineKeyboardButton("Next ▶️", callback_data=f"{callback_prefix}_NEXT")
            )

        # 선택 완료 버튼 추가
        navigation_buttons.append(
            InlineKeyboardButton(
                "✅ Confirm", callback_data=f"{callback_prefix}_CONFIRM"
            )
        )

        if navigation_buttons:
            buttons.append(navigation_buttons)

        return InlineKeyboardMarkup(buttons)
