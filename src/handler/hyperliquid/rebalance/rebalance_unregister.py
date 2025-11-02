from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler

from api import AccountService
from api.hyperliquid import RebalanceService
from hypurrquant.logging_config import force_coroutine_logging
from hypurrquant.models.account import Account
from .states import UnregisterStates
from .settings import RebalanceSetting

account_service = AccountService()
rebalance_service = RebalanceService()
PREFIX = "rebalance_unregister_account"


@force_coroutine_logging
async def rebalance_unregister_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    # 정말로 unregister 할 것인지 확인하는 메시지
    text = (
        "Are you sure you want to unregister the alarm account?\n\n"
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
                callback_data="rebalance_cancel",
            ),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return UnregisterStates.CONFIRM


@force_coroutine_logging
async def unregister_rebalance_account(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    account: Account = RebalanceSetting.get_setting(context).account

    await rebalance_service.unregister_rebalance_account(
        context._user_id, account.nickname
    )

    text = f"Success!\n\n"

    await query.edit_message_text(text, parse_mode="Markdown")
    return ConversationHandler.END


unregister_confirm = {
    UnregisterStates.CONFIRM: [
        CallbackQueryHandler(unregister_rebalance_account, pattern=f"^{PREFIX}")
    ],
}
