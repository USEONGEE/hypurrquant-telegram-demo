from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from hypurrquant.evm import Chain
from hypurrquant.logging_config import configure_logging
from api import EvmBalanceDto
from handler.utils.pagenation import Pagenation
from handler.utils.utils import format_buttons_grid
from tabulate import tabulate
from typing import List

logger = configure_logging(__name__)


class EvmBalancePagination(Pagenation):
    def __init__(self, evm_balance_dto: EvmBalanceDto, chain: Chain, page_size=9):
        # 상위 생성자 호출
        self.chain = chain
        if chain == Chain.HYPERLIQUID:
            self.coin_symbol = "HYPE"
        else:
            raise ValueError("No Such")
        self.raw_data = evm_balance_dto
        data = [
            item
            for item in evm_balance_dto["erc20"].values()
            # if item["raw_amount"] > 0
        ]
        super().__init__(data=data, page_size=page_size)

    def generate_info_text(self) -> str:
        message = "*Evm Balance*\n```\n"
        native_wrap_data = [
            [self.coin_symbol, f"{self.raw_data["native"]["decimal_amount"]:.4f}"],
            [
                f"W{self.coin_symbol}",
                f"{self.raw_data["wrapped"]["decimal_amount"]:.4f}",
            ],
        ]
        message += tabulate(
            native_wrap_data, headers=["symbol", "amount"], tablefmt="grid"
        )
        erc20_data = [[i["ticker"], f"{i['decimal_amount']:.2f}"] for i in self.data]
        message += "\n" + tabulate(erc20_data, tablefmt="grid") + "\n```"
        return message

    def generate_buttons(self, callback_prefix: str) -> List[InlineKeyboardMarkup]:
        navigation_buttons = []
        if self.has_prev_page():
            navigation_buttons.append(
                InlineKeyboardButton("◀️ Prev", callback_data=f"{callback_prefix}_PREV")
            )
        if self.has_next_page():
            navigation_buttons.append(
                InlineKeyboardButton("Next ▶️", callback_data=f"{callback_prefix}_NEXT")
            )

        return navigation_buttons


class EvmSendPagination(Pagenation):
    def __init__(self, evm_balance_dto: EvmBalanceDto, chain: Chain, page_size=9):
        # 상위 생성자 호출
        self.chain = chain
        if chain == Chain.HYPERLIQUID:
            self.coin_symbol = "HYPE"
        else:
            raise ValueError("No Such")
        self.raw_data = evm_balance_dto.copy()
        data = [evm_balance_dto["wrapped"]] + list(evm_balance_dto["erc20"].values())
        data = [item for item in data if item["raw_amount"] > 0]
        super().__init__(data=data, page_size=page_size)

    def generate_info_text(self) -> str:
        message = "*Evm Balance*\n```\n"
        erc20_data = [[i["ticker"], f"{i['decimal_amount']:.4f}"] for i in self.data]
        message += tabulate(erc20_data, tablefmt="grid") + "\n```"
        return message

    def generate_buttons(self, callback_prefix: str) -> List:

        buttons = [
            InlineKeyboardButton(
                text=item["ticker"],
                callback_data=f"{callback_prefix}|{item['address']}",
            )
            for item in self.get_current_page_data()
        ]
        buttons_grid = format_buttons_grid(buttons, columns=3)

        navigation_buttons = []
        if self.has_prev_page():
            navigation_buttons.append(
                InlineKeyboardButton("◀️ Prev", callback_data=f"{callback_prefix}_PREV")
            )
        if self.has_next_page():
            navigation_buttons.append(
                InlineKeyboardButton("Next ▶️", callback_data=f"{callback_prefix}_NEXT")
            )
        buttons_grid.append(navigation_buttons)
        return buttons_grid
