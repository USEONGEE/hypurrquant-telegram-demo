from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from hypurrquant.models.market_data import MarketData
from hypurrquant.logging_config import configure_logging
from api import ReferralDetailDict
from handler.utils.pagenation import Pagenation

from typing import List

logger = configure_logging(__name__)

MINIMUM_PER_ORDER = 20  # 최소 주문 금액 (USDC)


class ReferralDetailPagination(Pagenation):
    def __init__(
        self,
        data: List[ReferralDetailDict],
        page_size=9,
    ):
        """
        ReferaalPagination 초기화.

        Args:
            market_data (list): Market Data 리스트.
            page_size (int): 한 페이지에 표시할 데이터 개수. 기본값은 4.
        """
        data = sorted(data, key=lambda x: x["total_earned"], reverse=True)
        # 상위 생성자 호출
        super().__init__(data, page_size)

    def generate_info_text(self) -> str:
        current_list: List[MarketData] = self.get_current_page_data()

        response = f"👥 *Referral Details*  Page [{self.current_page+1}/{self.total_pages}]\n\n"

        # 각 referee 항목 출력
        for d in current_list:
            pk = d["public_key"]
            # pk = f"{pk[:6]}...{pk[-4:]}"  # 예: 0x3e18...6c0a

            response += f"• `{pk}`\n" f"    • Earned: `{d['total_earned']:.6f}` USDC\n"

        return response

    def generate_buttons(self, callback_prefix):
        """
        현재 페이지 데이터를 기반으로 InlineKeyboardMarkup 생성.

        Args:
            callback_prefix (str): 버튼 콜백 데이터에 사용할 prefix.

        Returns:
            InlineKeyboardMarkup: Telegram용 InlineKeyboard 버튼 레이아웃.
        """

        # 페이지네이션 버튼 추가
        navigation_buttons = []
        if self.has_prev_page():
            navigation_buttons.append(
                [
                    InlineKeyboardButton(
                        "◀️ Prev", callback_data=f"{callback_prefix}_PREV"
                    )
                ]
            )
        if self.has_next_page():
            navigation_buttons.append(
                [
                    InlineKeyboardButton(
                        "Next ▶️", callback_data=f"{callback_prefix}_NEXT"
                    )
                ]
            )

        # 선택 완료 버튼 추가
        navigation_buttons.append(
            [
                InlineKeyboardButton(
                    "GO BACK", callback_data=f"{callback_prefix}_GO_BACK"
                )
            ]
        )

        return InlineKeyboardMarkup(navigation_buttons)
