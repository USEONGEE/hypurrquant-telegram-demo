from telegram import (
    Update,
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
)

from api.hyperliquid import SellOrderService
from handler.command import Command
from handler.utils.cancel import main_menu
from handler.utils.utils import send_or_edit
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from .states import SpecificStates
from .utils import (
    can_operation_sell,
    create_sepcific_sell_request_body,
)
from .pagenation import SellableOrderPagination
from .models.orderable_spot_balance import (
    OrderableSpotbalance,
)
from .settings import (
    SellSetting,
    SellSepcificSetting,
)
from .exceptions import SELL_ALL_FAIL, NO_STOCK
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
import asyncio

logger = configure_logging(__name__)

sellOrderService = SellOrderService()

CALLBACK_PREFIX = "SELL_SELECT_STOCK"


@force_coroutine_logging
async def sell_sepecific_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    구매량 선택
    """
    logger.debug("sell_all_start")
    query = update.callback_query
    await query.answer()
    # 데이터 셋팅
    sell_setting: SellSetting = SellSetting.get_setting(context)
    SellSepcificSetting.clear_setting(context)
    specific_setting: SellSepcificSetting = SellSepcificSetting.get_setting(context)

    if not can_operation_sell(context):
        await send_or_edit(
            update,
            context,
            "There are no stocks to sell. Please select stocks to sell first.",
        )
        await asyncio.sleep(1.5)
        return await main_menu(update, context, specific_setting.return_to)

    specific_setting.sellable_order_pagination = SellableOrderPagination(
        [
            OrderableSpotbalance(**(d.model_dump()))
            for d in sell_setting.sellable_balance
        ]
    )

    await show_current_page(update, context)
    return SpecificStates.PAGE


# =============== #
# 2) 페이지 보여주기 #
# =============== #
@force_coroutine_logging
async def show_current_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    현재 페이지의 종목 목록(문구) + 버튼(이전, 다음, 토글, 확인)을 전송
    """
    specific_setting: SellSepcificSetting = SellSepcificSetting.get_setting(context)
    pagination = specific_setting.sellable_order_pagination

    # 메시지 텍스트
    info_text = pagination.generate_info_text()  # 각 종목 정보를 문자열로 만듦
    # 버튼
    keyboard_markup = pagination.generate_buttons(callback_prefix=CALLBACK_PREFIX)

    # 이미 콜백 쿼리(CallbackQuery)에서 호출되었다면 edit_message로 갱신
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=info_text, reply_markup=keyboard_markup, parse_mode="Markdown"
        )
    else:
        await update.effective_chat.send_message(
            text=info_text, reply_markup=keyboard_markup, parse_mode="Markdown"
        )


# =============== #
# 3) 콜백 처리    #
# =============== #
@force_coroutine_logging
async def page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    query = update.callback_query
    await query.answer()
    data = query.data  # ex) "STOCKS_TOGGLE_AAPL" or "STOCKS_PREV" etc.

    specific_setting: SellSepcificSetting = SellSepcificSetting.get_setting(context)
    pagination = specific_setting.sellable_order_pagination

    if data.startswith(f"{CALLBACK_PREFIX}_TOGGLE_"):
        # 종목 선택/해제 토글
        ticker = data.split(f"{CALLBACK_PREFIX}_TOGGLE_")[1]
        # 현재 페이지 내 데이터 탐색
        current_page_data = pagination.get_current_page_data()
        for item in current_page_data:
            if item.Name == ticker:
                item.is_sell = not item.is_sell
                break  # 찾으면 즉시 종료

        await show_current_page(update, context)
        return SpecificStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_NEXT":
        pagination.go_to_next_page()
        await show_current_page(update, context)
        return SpecificStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_PREV":
        pagination.go_to_prev_page()
        await show_current_page(update, context)
        return SpecificStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_CONFIRM":
        will_sell_balance = [d for d in pagination.data if d.is_sell]

        if len(will_sell_balance) <= 0:
            await query.edit_message_text(NO_STOCK)
            return ConversationHandler.END

        # 판매 주문 실행
        request_body = create_sepcific_sell_request_body(
            specific_setting.sellable_order_pagination.data
        )
        response = await sellOrderService.sell_order_market(
            context._user_id, request_body
        )

        # 잔고 갱신
        account_hodler: AccountManager = await fetch_account_manager(context)
        await account_hodler.refresh_spot_balance(force=True)
        if response:
            await query.edit_message_text(
                f"Success! You can check your order history using /{Command.BALANCE}"
            )
            return ConversationHandler.END
        else:
            await query.edit_message_text(SELL_ALL_FAIL)
            return ConversationHandler.END

    else:
        await query.edit_message_text(
            "Oops, that's not valid. Please give it another try!"
        )
        return ConversationHandler.END


specific_states = {
    SpecificStates.PAGE: [
        CallbackQueryHandler(page_callback, pattern=f"^{CALLBACK_PREFIX}_")
    ],
}
