from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from handler.models.spot_balance import SpotBalance, SpotBalanceMapping
from handler.models.perp_balance import PositionDetail, PerpBalanceMapping
from handler.utils.pagenation import Pagenation
from hypurrquant.logging_config import configure_logging

from typing import List

logger = configure_logging(__name__)


class SpotDetailPagination(Pagenation):
    def __init__(self, data: SpotBalanceMapping, page_size=15):

        # 상위 생성자 호출
        data: List[SpotBalance] = list(data.balances.values())
        sort_key_func = lambda x: x.Value
        data = sorted(data, key=sort_key_func, reverse=True)
        super().__init__(data=data, page_size=page_size)

    def generate_info_text(self) -> str:

        # 표 헤더

        message = "📊 *Current Holdings & PnL Overview:*\n\n```\n"
        message += "+---------+-----------+-----------+\n"
        message += "| Ticker  | Invested  |    PNL    |\n"
        message += "+---------+-----------+-----------+\n"

        current_balance = self.get_current_page_data()

        for balance in current_balance:
            message += (
                f"| {balance.Name:<8}"  # 왼쪽 정렬, 폭 8
                f"| {balance.Value:9.2f}$"  # 오른쪽 정렬, 폭 11, 소수점 5자리
                f"| {balance.PNL:9.2f}$|\n"  # 오른쪽 정렬, 폭 10, 소수점 2자리, 'K' 추가
            )

        message += "+---------+-----------+-----------+\n"
        message += "```\n"

        return message

    def generate_buttons(self, callback_prefix: str) -> InlineKeyboardMarkup:
        current_page_data = self.get_current_page_data()

        buttons = []
        row = []  # 한 행을 담는 임시 리스트

        for i, data in enumerate(current_page_data):
            row.append(
                InlineKeyboardButton(
                    data.Name,
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
            InlineKeyboardButton("Back", callback_data=f"{callback_prefix}_CONFIRM")
        )

        if navigation_buttons:
            buttons.append(navigation_buttons)

        return InlineKeyboardMarkup(buttons)


class PerpDetailPagination(Pagenation):
    def __init__(self, data: PerpBalanceMapping, page_size=15):

        # 상위 생성자 호출
        data: List[PositionDetail] = list(data.position.oneWay.values())
        sort_key_func = lambda x: x.returnOnEquity
        data = sorted(data, key=sort_key_func, reverse=True)
        super().__init__(data=data, page_size=page_size)

    def generate_info_text(self) -> str:

        # 표 헤더

        message = "📊 *Current Holdings & PnL Overview:*\n\n```\n"
        message += "+---------+-----------+-----------+\n"
        message += "| Ticker  | Invested  |    PNL    |\n"
        message += "+---------+-----------+-----------+\n"

        current_balance = self.get_current_page_data()

        for balance in current_balance:
            message += (
                f"| {balance.name:<8}"  # 왼쪽 정렬, 폭 8
                f"| {balance.positionValue:9.2f}$"  # 오른쪽 정렬, 폭 11, 소수점 5자리
                f"| {balance.unrealizedPnl:9.2f}$|\n"  # 오른쪽 정렬, 폭 10, 소수점 2자리, 'K' 추가
            )

        message += "+---------+-----------+-----------+\n"
        message += "```\n"

        return message

    def generate_buttons(self, callback_prefix: str) -> InlineKeyboardMarkup:
        current_page_data = self.get_current_page_data()

        buttons = []
        row = []  # 한 행을 담는 임시 리스트

        for i, data in enumerate(current_page_data):
            row.append(
                InlineKeyboardButton(
                    data.name,
                    callback_data=f"{callback_prefix}_TOGGLE_{data.name}",
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
            InlineKeyboardButton("Back", callback_data=f"{callback_prefix}_CONFIRM")
        )

        if navigation_buttons:
            buttons.append(navigation_buttons)

        return InlineKeyboardMarkup(buttons)
