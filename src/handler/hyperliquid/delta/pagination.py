from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from hypurrquant.logging_config import configure_logging
from hypurrquant.utils.paired_symbols import (
    symbol_table,
)
from handler.utils.pagenation import Pagenation
from api.hyperliquid import PerpMarketDataCache

from typing import List

logger = configure_logging(__name__)

MINIMUM_PER_ORDER = 20  # 최소 주문 금액 (USDC)

perp_market_data_cache = PerpMarketDataCache()


class DeltaSymbolPagination(Pagenation):
    def __init__(
        self,
        current_balance: float,
        symbol_keys: List[str] = list(symbol_table.keys()),
        page_size=15,
    ):
        """
        MarketDataPagination 초기화.

        Args:
            market_data (list): Market Data 리스트.
            page_size (int): 한 페이지에 표시할 데이터 개수. 기본값은 4.
        """
        self.current_balance = current_balance
        super().__init__(symbol_keys, page_size)

    async def generate_info_text(self) -> str:
        """
        Generates an informational message for the Delta Neutral strategy screen.
        """
        current_list: List[str] = self.get_current_page_data()

        # Header with strategy details
        response = (
            "💡 **Delta Neutral Strategy Overview** 💡\n"
            "- Minimum order amount: $40 (split evenly: 1x spot, 1x short on perpetual)\n"
            "- Hyperliquid pays funding every hour\n"
            "- Upcoming UNIT airdrop! ✈️✨\n"
            "  Grow trading volume safely with the Delta Neutral strategy! 🚀\n\n"
            "**❌ No performance Fee**\n"
            "**❌ No Deposit Fee**\n"
            "**❌ No Withdrawal Fee**\n\n"
        )

        # Current balance and pagination
        response += f"Total USDC: `{self.current_balance}`\n"

        # Table header
        response += "```\n"
        response += "+----------+------------+----------+\n"
        response += "|  Ticker  |    Price   |    APY   |\n"
        response += "+----------+------------+----------+\n"

        # Table rows with data
        for stock in current_list:
            price = perp_market_data_cache.market_datas[stock].midPx
            apy = (
                pow(1 + perp_market_data_cache.market_datas[stock].funding, 24 * 365)
                - 1
            ) * 100
            response += (
                f"| {stock:<9}"  # left-align width 9
                f"| {price:>11.3f}"  # right-align width 11, 3 decimals
                f"| {apy:>7.2f}% |\n"  # right-align width 8, 4 decimals
            )

        # Table footer
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
            display_name = f"{data}"
            row.append(
                InlineKeyboardButton(
                    display_name,
                    callback_data=f"{callback_prefix}_TOGGLE_{data}",
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
                "Cancel",
                callback_data=f"delta_cancel",
            )
        )

        if navigation_buttons:
            buttons.append(navigation_buttons)

        return InlineKeyboardMarkup(buttons)


class DeltaClosePagination(Pagenation):
    def __init__(
        self,
        current_balance: float,
        paired: set,
        page_size=15,
    ):
        """
        MarketDataPagination 초기화.

        Args:
            market_data (list): Market Data 리스트.
            page_size (int): 한 페이지에 표시할 데이터 개수. 기본값은 4.
        """
        self.current_balance = current_balance
        super().__init__(paired, page_size)

    async def generate_info_text(self) -> str:
        """
        Generates an informational message for the Delta Neutral strategy screen.
        """
        current_list: List = self.get_current_page_data()

        # Header with strategy details
        response = "💡 **Your Delta Neutral Position** 💡\n"

        # Table header
        response += "```\n"
        response += "+----------+------------+\n"
        response += "|  Ticker  |  Position  |\n"
        response += "+----------+------------+\n"

        # Table rows with data
        for stock, spot_balance, perp_position in current_list:
            total = spot_balance.Value + perp_position.marginUsed
            logger.debug(
                f"DeltaClosePagination: {stock} - Spot: {spot_balance.Value}, Perp Position Value: {perp_position.marginUsed}, Total: {total}"
            )
            response += (
                f"| {stock:<9}"  # left-align width 9
                f"| {total:>10.2f} |\n"  # right-align width 10, 2 decimals
            )

        # Table footer
        response += "+----------+------------+\n"
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

        for i, (data, _, _) in enumerate(current_page_data):
            display_name = f"{data}"
            row.append(
                InlineKeyboardButton(
                    display_name,
                    callback_data=f"{callback_prefix}_TOGGLE_{data}",
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
                "Cancel",
                callback_data=f"delta_cancel",
            )
        )

        if navigation_buttons:
            buttons.append(navigation_buttons)

        return InlineKeyboardMarkup(buttons)
