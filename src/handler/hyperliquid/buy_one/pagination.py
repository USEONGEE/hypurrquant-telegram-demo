from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from hypurrquant.models.market_data import MarketData
from hypurrquant.logging_config import configure_logging
from handler.utils.pagenation import Pagenation
from handler.utils.cancel import create_cancel_inline_button
from handler.command import Command
from typing import List

logger = configure_logging(__name__)

MINIMUM_PER_ORDER = 20  # 최소 주문 금액 (USDC)


class MarketDataPagination(Pagenation):
    def __init__(
        self,
        market_data: List[MarketData],
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

        market_data = sorted(market_data, key=lambda x: x.dayNtlVlm, reverse=True)
        # 상위 생성자 호출
        super().__init__(market_data, page_size)

    def generate_info_text(self) -> str:
        current_list: List[MarketData] = self.get_current_page_data()

        response = f"The minimum average per stock is $20. \nIf you do not wish to buy or have insufficient balance, please adjust the number of stocks.\n\n"
        response += f"1️⃣ Your Balance: {self.current_balance}\n"

        response += f"Page [{self.current_page + 1} / {self.total_pages}]\n"
        response += "```"
        response += "+----------+------------+----------+\n"
        response += "|  Ticker  |    Price   |change_pct|\n"
        response += "+----------+------------+----------+\n"

        for stock in current_list:
            # midPx 값이 1 미만이면 소수점 10자리, 아니면 소수점 5자리
            mid_px_formatted = (
                f"{stock.midPx:.5f}" if stock.midPx < 1 else f"{stock.midPx:.2f}"
            )

            response += (
                f"| {stock.Tname:<9}"
                f"| {mid_px_formatted:>9}$ "  # 폭 11 유지 (길이에 따라 조정 가능)
                f"| {stock.change_24h_pct:>7.4}% |\n"
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
            display_name = data.Tname
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

        # 뒤로가기 버튼 추가
        navigation_buttons.append(
            create_cancel_inline_button(Command.HYPERLIQUID_CORE_START)
        )

        if navigation_buttons:
            buttons.append(navigation_buttons)

        return InlineKeyboardMarkup(buttons)
