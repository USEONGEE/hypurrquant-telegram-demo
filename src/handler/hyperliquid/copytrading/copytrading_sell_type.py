from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from hypurrquant.models.account import Account
from .states import (
    CopytradingStates,
    SellTypeStates,
)
from .copytrading_start import copytrading_start
from api.hyperliquid import CopytradingService

from typing import List

logger = configure_logging(__name__)
copytrading_service = CopytradingService()
PREFIX = "copytrading_sell_type_wallet"


@force_coroutine_logging
async def copytrading_sell_type_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await update.callback_query.answer()
    account_hodler: AccountManager = await fetch_account_manager(context)
    account_list: List[Account] = await account_hodler.get_all_accounts()

    text = (
        "*Sell Type for Copy Trading*\n\n"
        "Sell type defines the strategy for executing sell orders within the copy trading system. It determines how and when sell orders are placed, based on manual decisions, preset conditions, or by mirroring the sell actions of a trader you are following.\n"
        "Available Sell Types:\n\n"
        "- `Self`: Manually execute the sale by yourself, meaning you make all selling decisions independently.\n"
        "- `Auto Trading`: Automatically execute a sell order when your target PNL (%) is reached, based on predefined conditions.\n"
        "- `Copy`: Mirror the sell decisions of the trader you are copying, ensuring that your account follows their actions.\n\n"
        "Even if the tracked wallet places some reduce orders, all positions will be closed."
    )
    buttons = [
        [
            InlineKeyboardButton(
                "Self",
                callback_data=(f"{PREFIX}|{'self'}"),
            )
        ],
        [
            InlineKeyboardButton(
                "Auto Trading",
                callback_data=(f"{PREFIX}|{'auto_trading'}"),
            )
        ],
        [
            InlineKeyboardButton(
                "Copy",
                callback_data=(f"{PREFIX}|{'copy'}"),
            )
        ],
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                "Cancel",
                callback_data="copytrading_cancel",
            )
        ]
    )
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return SellTypeStates.CHANGE


# ================================
# 지갑 변경
# ================================
@force_coroutine_logging
async def copytrading_sell_type_change(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    strategy = str(update.callback_query.data.split("|")[1])
    await copytrading_service.update_sell_type_copytrading(context._user_id, strategy)

    message = f"strategy has been set to {strategy}."
    message = message.replace("_", " ")
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
    )
    await copytrading_start(update, context)
    return CopytradingStates.SELECT_ACTION


sell_type_states = {
    SellTypeStates.CHANGE: [
        CallbackQueryHandler(copytrading_sell_type_change, pattern=f"^{PREFIX}")
    ],
}
