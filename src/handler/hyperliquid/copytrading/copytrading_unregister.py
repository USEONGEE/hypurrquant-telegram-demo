from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler

from api.hyperliquid import CopytradingService
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from hypurrquant.models.account import Account
from .states import UnregisterStates
from .settings import CopytradingSetting

copytrading_service = CopytradingService()

PREFIX = "copytrading_unregister_account"
logger = configure_logging(__name__)


@force_coroutine_logging
async def copytrading_unregister_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(f"triggerred by user: {context._user_id}")
    query = update.callback_query
    await query.answer()

    # 정말로 unregister 할 것인지 확인하는 메시지
    text = (
        "Are you sure you want to unregister the copy trading account?\n\n"
        "This action cannot be undone."
    )
    buttons = [
        [
            InlineKeyboardButton(
                "Yes",
                callback_data=PREFIX,
            ),
            InlineKeyboardButton(
                "No",
                callback_data="copytrading_cancel",
            ),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return UnregisterStates.CONFIRM


@force_coroutine_logging
async def unregister_copytrading_account(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(f"triggerred by user: {context._user_id}")
    query = update.callback_query
    await query.answer()

    account: Account = CopytradingSetting.get_setting(context).account

    await copytrading_service.unregister_copytrading_account(
        context._user_id, account.nickname
    )

    text = f"Success!\n\n"

    await query.edit_message_text(text, parse_mode="Markdown")
    return ConversationHandler.END


unregister_confirm = {
    UnregisterStates.CONFIRM: [
        CallbackQueryHandler(unregister_copytrading_account, pattern=f"^{PREFIX}")
    ],
}
