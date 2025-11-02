from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
)

from api.hyperliquid import PerpOrderService
from handler.command import Command
from handler.models.perp_balance import PositionDetail
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from .states import *
from .utils import can_operation_close
from .pagination import ClosableOrderPagination
from .settings import (
    CloseSetting,
    CloseOneSetting,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)


logger = configure_logging(__name__)

perpOrderService = PerpOrderService()

CALLBACK_PREFIX = "CLOSE_ALL_SELECT_STOCK"


@force_coroutine_logging
async def close_one_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    구매량 선택
    """
    logger.debug("sell_all_start")
    query = update.callback_query
    await query.answer()

    if not can_operation_close(context):
        await query.message.reply_text(
            "There are no stocks to close. Please select stocks to sell first."
        )
        return ConversationHandler.END

    # 데이터 셋팅
    close_setting: CloseSetting = CloseSetting.get_setting(context)
    CloseOneSetting.clear_setting(context)
    close_all_setting: CloseOneSetting = CloseOneSetting.get_setting(context)
    close_all_setting.closable_order_pagination = ClosableOrderPagination(
        close_setting.sellable_balance
    )

    await show_current_page(update, context)
    return CloseOneStates.PAGE


# =============== #
# 2) 페이지 보여주기 #
# =============== #
@force_coroutine_logging
async def show_current_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    현재 페이지의 종목 목록(문구) + 버튼(이전, 다음, 토글, 확인)을 전송
    """
    close_all_setting: CloseOneSetting = CloseOneSetting.get_setting(context)
    pagination = close_all_setting.closable_order_pagination

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

    close_all_setting: CloseOneSetting = CloseOneSetting.get_setting(context)
    close_setting: CloseSetting = CloseSetting.get_setting(context)
    pagination = close_all_setting.closable_order_pagination

    if data.startswith(f"{CALLBACK_PREFIX}_TOGGLE_"):
        stock_name = data.split("_")[-1]
        close_all_setting.selected_stock = close_setting.sellable_balance.oneWay[
            stock_name
        ]

        message = "Are you sure you want to sell this stock?"
        keyboard_markup = [
            [
                InlineKeyboardButton(
                    "Yes",
                    callback_data=f"{CALLBACK_PREFIX}_CONFIRM",
                ),
                InlineKeyboardButton(
                    "No",
                    callback_data=f"{CALLBACK_PREFIX}_CANCEL",
                ),
            ]
        ]
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard_markup),
            parse_mode="Markdown",
        )
        return CloseOneStates.CONFIRM

    elif data == f"{CALLBACK_PREFIX}_NEXT":
        pagination.go_to_next_page()
        await show_current_page(update, context)
        return CloseOneStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_PREV":
        pagination.go_to_prev_page()
        await show_current_page(update, context)
        return CloseOneStates.PAGE

    else:
        await query.edit_message_text(
            "Oops, that's not valid. Please give it another try!"
        )
        return ConversationHandler.END


# =============== #
# 4) 판매 여부    #
# =============== #
@force_coroutine_logging
async def close_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    판매 여부 확인
    """
    query = update.callback_query
    await query.answer()

    close_all_setting: CloseOneSetting = CloseOneSetting.get_setting(context)

    data = query.data
    if data == f"{CALLBACK_PREFIX}_CONFIRM":
        # 판매 수행
        close_all_setting: CloseOneSetting = CloseOneSetting.get_setting(context)
        position_detail: PositionDetail = close_all_setting.selected_stock

        response = await perpOrderService.close(context._user_id, position_detail.name)

        # 잔고 갱신
        account_hodler: AccountManager = await fetch_account_manager(context)
        await account_hodler.refresh_perp_balance(force=True)

        if response:
            await update.callback_query.edit_message_text(
                f"Success! You can check your order history using /{Command.BALANCE}"
            )
            return ConversationHandler.END
        else:
            await update.callback_query.edit_message_text("Failed to close.")
            return ConversationHandler.END

    elif data == f"{CALLBACK_PREFIX}_CANCEL":
        await show_current_page(update, context)
        return CloseOneStates.PAGE

    else:
        await query.edit_message_text(
            "Oops, that's not valid. Please give it another try!"
        )
        return ConversationHandler.END


one_states = {
    CloseOneStates.PAGE: [
        CallbackQueryHandler(page_callback, pattern=f"^{CALLBACK_PREFIX}_")
    ],
    CloseOneStates.CONFIRM: [
        CallbackQueryHandler(close_confirm, pattern=f"^{CALLBACK_PREFIX}_")
    ],
}
