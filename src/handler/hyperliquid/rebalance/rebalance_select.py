from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import CallbackQueryHandler, ContextTypes, ConversationHandler
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api.exception import ShouldBeTradingAcocuntException
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from hypurrquant.models.account import Account
from .states import (
    RebalanceStates,
    SelectStates,
)
from .rebalance_start import rebalance_start

from typing import List

logger = configure_logging(__name__)

PREFIX = "rebalance_select_wallet"


@force_coroutine_logging
async def rebalance_select_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await update.callback_query.answer()
    account_hodler: AccountManager = await fetch_account_manager(context)
    account_list: List[Account] = await account_hodler.get_all_accounts()

    text = (
        "Select Wallet\n\n"
        "Please select the account to be used for auto trading. Only one account can be used per Telegram account.\n\n"
        "If no authenticated accounts exist, nothing may be displayed. In that case, please run /wallet to activate the account you want to use, deposit USDC into it, and then complete authentication"
    )
    buttons = [
        [
            InlineKeyboardButton(
                account.nickname,
                callback_data=(f"{PREFIX}|{account.nickname}"),
            )
        ]
        for account in account_list
        if account.is_approved_builder_fee
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                "Cancel",
                callback_data="rebalance_cancel",
            ),
        ]
    )
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return SelectStates.CHANGE


# ================================
# 지갑 변경
# ================================
@force_coroutine_logging
async def rebalance_wallet_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    query = update.callback_query
    await query.answer()
    account_manager: AccountManager = await fetch_account_manager(context)

    nickname = str(update.callback_query.data.split("|")[1])
    try:
        await account_manager.change_rebalance_account(nickname)
    except ShouldBeTradingAcocuntException as e:
        message = (
            "This account is already registered in /alarm.\n\n"
            "Please try registering with another account or unregister the account in /alarm. and try again."
        )
        await update.callback_query.edit_message_text(
            message,
            parse_mode="Markdown",
        )
        return ConversationHandler.END
    rebalance_account: Account = await account_manager.get_rebalance_account()

    message = f"`{rebalance_account.nickname}` is activated."
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
    )
    await rebalance_start(update, context)
    return RebalanceStates.SELECT_ACTION


select_states = {
    SelectStates.CHANGE: [
        CallbackQueryHandler(rebalance_wallet_change, pattern=f"^{PREFIX}")
    ],
}
