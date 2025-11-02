from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)

from api.hyperliquid import DeltaOrderService
from .pagination import DeltaClosePagination
from .states import *
from .settings import (
    DeltaSetting,
    DeltaCloseSetting,
)
from api import AccountService
from handler.utils.utils import answer, send_or_edit
from handler.utils.account_helpers import (
    fetch_active_account,
)
from handler.command import Command
from hypurrquant.models.account import Account

logger = configure_logging(__name__)

account_service = AccountService()
delta_order_service = DeltaOrderService()

CALLBACK_PREFIX = "DELTA_CLOSE"


@force_coroutine_logging
async def delta_close_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    logger.info("delta close command triggered by user: %s", update.effective_user.id)
    await answer(update)
    DeltaCloseSetting.clear_setting(context)

    return await show_current_page(update, context)


# =============== #
# 2) 페이지 보여주기 #
# =============== #
@force_coroutine_logging
async def show_current_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    현재 페이지의 종목 목록(문구) + 버튼(이전, 다음, 토글, 확인)을 전송
    """
    setting = DeltaSetting.get_setting(context)
    close_pagination: DeltaClosePagination = setting.close_pagination

    info_text = await close_pagination.generate_info_text()
    keyboard_markup = close_pagination.generate_buttons(callback_prefix=CALLBACK_PREFIX)

    await send_or_edit(
        update,
        context,
        text=info_text,
        reply_markup=keyboard_markup,
        parse_mode="Markdown",
    )
    return DeltaCloseState.PAGE


# =============== #
# 3) 콜백 처리     #
# =============== #
@force_coroutine_logging
async def page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")

    query = update.callback_query
    await query.answer()
    data = query.data

    close_setting: DeltaCloseSetting = DeltaCloseSetting.get_setting(context)
    setting = DeltaSetting.get_setting(context)
    close_pagination = setting.close_pagination

    if data.startswith(f"{CALLBACK_PREFIX}_TOGGLE_"):
        # 종목 선택/해제 토글
        close_setting.ticker = data.split(f"{CALLBACK_PREFIX}_TOGGLE_")[1]
        msg = f"To close delta neutral, press the OK button.\n\nTicker: {close_setting.ticker}\n"
        await update.callback_query.edit_message_text(
            text=msg,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("OK", callback_data=f"OK")],
                    [InlineKeyboardButton("Cancel", callback_data=f"delta_cancel")],
                ],
            ),
        )
        return DeltaCloseState.CONFIRMATION

    elif data == f"{CALLBACK_PREFIX}_NEXT":
        close_pagination.go_to_next_page()
        return await show_current_page(update, context)

    elif data == f"{CALLBACK_PREFIX}_PREV":
        close_pagination.go_to_prev_page()
        return await show_current_page(update, context)
    else:
        raise ValueError(f"Unknown operation")


# =============== #
# 4) 주문 금액 입력    #
# =============== #
@force_coroutine_logging
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    구매량 선택
    """
    logger.debug("purchase_amount_selection")
    await answer(update)
    account: Account = await fetch_active_account(context)

    close_setting: DeltaCloseSetting = DeltaCloseSetting.get_setting(context)
    ticker = close_setting.ticker

    await delta_order_service.market_close(
        str(context._user_id),
        account.nickname,
        ticker,
    )

    await update.callback_query.edit_message_text(
        f"Success! You can check your order history using /{Command.DELTA}"
    )
    return ConversationHandler.END


delta_close_states = {
    DeltaCloseState.PAGE: [
        CallbackQueryHandler(page_callback, pattern=f"^{CALLBACK_PREFIX}_")
    ],
    DeltaCloseState.CONFIRMATION: [CallbackQueryHandler(confirm, pattern="^OK$")],
}
