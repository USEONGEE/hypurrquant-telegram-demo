from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from api.hyperliquid import ListSubscriptionsResponse, CopytradingService
from handler.utils.pagenation import Pagenation
from hypurrquant.logging_config import configure_logging

from typing import List
import math

logger = configure_logging(__name__)

copytrading_service = CopytradingService()


class SubscriptionPagination(Pagenation):
    def __init__(self, data: ListSubscriptionsResponse, page_size=15):
        self.original_data = data
        super().__init__(data=data["items"], page_size=page_size)
        self.current_page = 1
        self.total_pages = (data["total"] + data["page_size"] - 1) // data["page_size"]

    def __update(self, data: ListSubscriptionsResponse):
        self.original_data = data
        self.data = data["items"]
        self.total_pages = (data["total"] + data["page_size"] - 1) // data["page_size"]

    def generate_info_text(self) -> str:
        lines = ["🔗 *Subscribed Targets:*", ""]
        for i, item in enumerate(self.data):
            full_id = item["target_id"]
            display_id = full_id[:15] + "..."
            url = f"https://hypurrscan.io/address/{full_id}"
            lines.append(
                f"{i+1}. [{display_id} ({len(item['subscribers'])}/50)]({url})"
            )
        return "\n".join(lines)

    def generate_buttons(self, callback_prefix: str) -> InlineKeyboardMarkup:
        buttons, row = [], []
        for i, item in enumerate(self.data):
            row.append(
                InlineKeyboardButton(
                    str(i + 1),
                    callback_data=f"{callback_prefix}_TOGGLE_{item['target_id']}",
                )
            )
            if len(row) == 3:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        nav = []
        if self.has_prev_page():
            nav.append(
                InlineKeyboardButton("◀️ Prev", callback_data=f"{callback_prefix}_PREV")
            )
        if self.has_next_page():
            nav.append(
                InlineKeyboardButton("Next ▶️", callback_data=f"{callback_prefix}_NEXT")
            )
        nav.append(
            InlineKeyboardButton("Back", callback_data=f"{callback_prefix}_CONFIRM")
        )
        buttons.append(nav)
        return InlineKeyboardMarkup(buttons)

    def has_next_page(self) -> bool:
        return self.current_page < self.total_pages

    def has_prev_page(self) -> bool:
        return self.current_page > 1

    async def go_to_next_page(self):
        if self.has_next_page():
            self.current_page += 1
            data = await copytrading_service.page_subscription(
                self.current_page, self.page_size
            )
            self.__update(data)

    async def go_to_prev_page(self):
        if self.has_prev_page():
            self.current_page -= 1
            data = await copytrading_service.page_subscription(
                self.current_page, self.page_size
            )
            self.__update(data)
