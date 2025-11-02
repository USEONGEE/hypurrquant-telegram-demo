from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from handler.models.perp_balance import Position
from handler.utils.pagenation import Pagenation
from hypurrquant.logging_config import configure_logging

logger = configure_logging(__name__)


class ClosableOrderPagination(Pagenation):
    def __init__(self, data: Position, page_size=15):
        self.position = data
        super().__init__(data=list(data.oneWay.values()), page_size=page_size)

    def generate_info_text(self) -> str:
        # 표 헤더
        message = (
            "Welcome to the close screen! \n\n"
            "Please select the stocks you want to close from the list below. \n"
            "You can choose individual stocks to proceed with the sale. \n\n"
            "⚠️ Assets under $15 are not displayed.\n\n"
        )

        message += "📊 *Current Holdings & PnL Overview:*\n\n```\n"
        message += "+---------+-----------+\n"
        message += "| Ticker  |    PNL    |\n"
        message += "+---------+-----------+\n"

        current_balance = self.get_current_page_data()
        for balance in current_balance:
            message += (
                f"| {balance.name:<8}"  # 왼쪽 정렬, 폭 8
                f"| {balance.unrealizedPnl:8.2f}$ |\n"  # 오른쪽 정렬, 폭 11, 소수점 5자리
            )

        message += "+---------+-----------+\n"
        message += "```\n"

        return message

    def generate_buttons(self, callback_prefix="PAGE"):
        current_page_data = self.get_current_page_data()

        buttons = []
        row = []  # 한 행을 담는 임시 리스트

        for i, data in enumerate(current_page_data):
            display_name = data.name
            row.append(
                InlineKeyboardButton(
                    display_name,
                    callback_data=f"{callback_prefix}_TOGGLE_{display_name}",
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

        if navigation_buttons:
            buttons.append(navigation_buttons)

        buttons.append(
            [
                InlineKeyboardButton("Go Back", callback_data="close_cancel"),
            ]
        )

        return InlineKeyboardMarkup(buttons)
