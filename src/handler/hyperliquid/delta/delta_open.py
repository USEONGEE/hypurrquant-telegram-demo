from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)

from api.hyperliquid import DeltaOrderService
from .pagination import DeltaSymbolPagination
from .states import *
from .settings import (
    DeltaSetting,
    DeltaOpenSetting,
)
from api import AccountService
from handler.utils.utils import answer, send_or_edit
from handler.utils.account_helpers import (
    fetch_active_account,
    fetch_account_manager,
)
from handler.utils.account_manager import AccountManager
from handler.command import Command
from hypurrquant.models.account import Account

logger = configure_logging(__name__)

account_service = AccountService()
delta_order_service = DeltaOrderService()

CALLBACK_PREFIX = "DELTA_OPEN"


@force_coroutine_logging
async def delta_open_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    logger.info("delta command triggered by user: %s", update.effective_user.id)
    await answer(update)
    DeltaOpenSetting.clear_setting(context)

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
    setting: DeltaSetting = DeltaSetting.get_setting(context)
    pagination: DeltaSymbolPagination = setting.pagination

    info_text = await pagination.generate_info_text()
    keyboard_markup = pagination.generate_buttons(callback_prefix=CALLBACK_PREFIX)

    await send_or_edit(
        update,
        context,
        text=info_text,
        reply_markup=keyboard_markup,
        parse_mode="Markdown",
    )
    return DeltaOpenState.PAGE


# =============== #
# 3) 콜백 처리     #
# =============== #
@force_coroutine_logging
async def page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")

    query = update.callback_query
    await query.answer()
    data = query.data

    setting: DeltaSetting = DeltaSetting.get_setting(context)
    open_setting: DeltaOpenSetting = DeltaOpenSetting.get_setting(context)
    pagination = setting.pagination

    if data.startswith(f"{CALLBACK_PREFIX}_TOGGLE_"):
        # 종목 선택/해제 토글
        open_setting.ticker = data.split(f"{CALLBACK_PREFIX}_TOGGLE_")[1]
        msg = f"How much would you like to buy? Ticker: {open_setting.ticker} Min: 40, Max: {pagination.current_balance}"

        await update.callback_query.edit_message_text(
            text=msg,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Cancel", callback_data=f"delta_cancel")],
                ]
            ),
        )
        return DeltaOpenState.AMOUNT_INPUT

    elif data == f"{CALLBACK_PREFIX}_NEXT":
        pagination.go_to_next_page()
        return await show_current_page(update, context)

    elif data == f"{CALLBACK_PREFIX}_PREV":
        pagination.go_to_prev_page()
        return await show_current_page(update, context)
    else:
        raise ValueError(f"Unknown operation")


# =============== #
# 4) 주문 금액 입력    #
# =============== #
@force_coroutine_logging
async def purchase_amount_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    구매량 선택
    """
    logger.debug("purchase_amount_selection")
    message = update.message
    account: Account = await fetch_active_account(context)

    # validaiton: 숫자만 허용
    try:
        value = float(message.text)
    except ValueError:
        await message.reply_text(f"Please enter a number. Try again. /{Command.DELTA}")
        return ConversationHandler.END
    setting: DeltaSetting = DeltaSetting.get_setting(context)
    open_setting: DeltaOpenSetting = DeltaOpenSetting.get_setting(context)
    if not open_setting.ticker:
        await message.reply_text(
            f"Please select a ticker first. Try again. /{Command.DELTA}"
        )
        return ConversationHandler.END

    if value < 40 or value > setting.pagination.current_balance:
        await message.reply_text(
            f"Purchase amount must be between $40 and ${setting.pagination.current_balance}. Try again. /{Command.DELTA}"
        )
        return ConversationHandler.END

    await delta_order_service.market_open(
        context._user_id, account.nickname, open_setting.ticker, value
    )

    account_hodler: AccountManager = await fetch_account_manager(context)
    await account_hodler.refresh_spot_balance(force=True)
    await message.reply_text(
        f"Success! You can check your order history using /{Command.DELTA}"
    )
    return ConversationHandler.END


delta_open_states = {
    DeltaOpenState.PAGE: [
        CallbackQueryHandler(page_callback, pattern=f"^{CALLBACK_PREFIX}_")
    ],
    DeltaOpenState.AMOUNT_INPUT: [
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            purchase_amount_selection,
        )
    ],
}
