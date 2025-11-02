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
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from .utils import can_operation_close
from .states import *
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)


logger = configure_logging(__name__)

perpOrderService = PerpOrderService()

CALL_BACK_PREFIX = "CLOSE_ALL_OK"


@force_coroutine_logging
async def close_all_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    query = update.callback_query
    await query.answer()

    if not can_operation_close(context):
        await query.message.reply_text(
            "There are no stocks to close. Please select stocks to close first."
        )
        return ConversationHandler.END

    message = (
        "You have selected to close all. \n\n"
        "Are you sure you want to proceed? This action cannot be undone.\n"
    )

    keyboard = [
        [InlineKeyboardButton("OK", callback_data=CALL_BACK_PREFIX)],
        [InlineKeyboardButton("Cancel", callback_data="close_cancel")],
    ]

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    return CloseAllStates.CLOSE


@force_coroutine_logging
async def close_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")

    logger.debug("close_order")
    query = update.callback_query
    await query.answer()

    # 판매 주문 실행
    response = await perpOrderService.close_all(context._user_id)

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


all_states = {
    CloseAllStates.CLOSE: [
        CallbackQueryHandler(close_order, pattern=f"^{CALL_BACK_PREFIX}$")
    ],
}
