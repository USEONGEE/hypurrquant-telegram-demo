from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Any


class Pagenation:
    def __init__(self, data: List[Any], page_size=15):
        """
        MarketDataPagination 초기화.

        Args:
            data (list): Market Data 리스트.
            page_size (int): 한 페이지에 표시할 데이터 개수. 기본값은 4.
        """
        if page_size < 1:
            raise ValueError("page_size must be greater than 0.")

        self.data: List[Any] = data
        self.page_size: int = page_size  # 페이지당 데이터 개수
        self.current_page: int = 0  # 초기 페이지 설정
        self.total_pages: int = (len(data) - 1) // page_size + 1

    def get_current_page_data(self) -> List[Any]:
        """
        현재 페이지의 데이터를 반환.

        Returns:
            list: 현재 페이지에 해당하는 Market Data.
        """
        start = self.current_page * self.page_size
        end = start + self.page_size
        return self.data[start:end]

    def has_next_page(self) -> bool:
        """
        다음 페이지 존재 여부 확인.

        Returns:
            bool: 다음 페이지가 있으면 True, 없으면 False.
        """
        return (self.current_page + 1) * self.page_size < len(self.data)

    def has_prev_page(self) -> bool:
        """
        이전 페이지 존재 여부 확인.

        Returns:
            bool: 이전 페이지가 있으면 True, 없으면 False.
        """
        return self.current_page > 0

    def go_to_next_page(self):
        """
        다음 페이지로 이동.
        """
        if self.has_next_page():
            self.current_page += 1

    def go_to_prev_page(self):
        """
        이전 페이지로 이동.
        """
        if self.has_prev_page():
            self.current_page -= 1

    def generate_info_text(self) -> str:
        pass

    def generate_buttons(self, callback_prefix="PAGE") -> InlineKeyboardMarkup:
        pass
