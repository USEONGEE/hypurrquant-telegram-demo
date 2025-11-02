from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .models.orderable_spot_balance import (
    OrderableSpotbalance,
)
from handler.utils.pagenation import Pagenation
from hypurrquant.logging_config import configure_logging

from typing import List

logger = configure_logging(__name__)


class SellableOrderPagination(Pagenation):
    def __init__(self, data: List[OrderableSpotbalance], page_size=15):
        logger.debug(f"Data: {data}")
        sort_key_func = lambda x: x.PNL
        data = sorted(data, key=sort_key_func, reverse=True)
        # 상위 생성자 호출
        super().__init__(data=data, page_size=page_size)

    def generate_info_text(self) -> str:

        # 표 헤더
        message = (
            "Welcome to the sell-by-stock screen! \n\n"
            "Please select the stocks you want to sell from the list below. \n"
            "You can choose individual stocks to proceed with the sale. \n\n"
            "⚠️ Assets under $15 are not displayed.\n\n"
        )

        message += "📊 *Current Holdings & PnL Overview:*\n\n```\n"
        message += "+---------+-----------+----------+\n"
        message += "| Ticker  |    PNL    |  Select  |\n"
        message += "+---------+-----------+----------+\n"

        current_balance = self.get_current_page_data()
        for balance in current_balance:
            message += (
                f"| {balance.Name:<8}"  # 왼쪽 정렬, 폭 8
                f"| {balance.PNL:9.2f}$"  # 오른쪽 정렬, 폭 11, 소수점 5자리
                f"| {'   ✅   ' if balance.is_sell else '   ❌   '}|\n"  # 오른쪽 정렬, 폭 10, 소수점 2자리, 'K' 추가
            )

        message += "+---------+-----------+----------+\n"
        message += "```\n"

        return message

    def generate_buttons(self, callback_prefix="PAGE"):
        current_page_data = self.get_current_page_data()

        buttons = []
        row = []  # 한 행을 담는 임시 리스트

        for i, data in enumerate(current_page_data):
            display_name = f"✅ {data.Name}" if data.is_sell else data.Name
            row.append(
                InlineKeyboardButton(
                    display_name,
                    callback_data=f"{callback_prefix}_TOGGLE_{data.Name}",
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

        buttons.append([InlineKeyboardButton("Go Back", callback_data=f"sell_cancel")])

        return InlineKeyboardMarkup(buttons)
