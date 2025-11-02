from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
)

from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from hypurrquant.models.account import Account
from .states import DeleteState, WalletState
from .settings import DeleteSetting
from .wallet_start import wallet_start
from handler.utils.cancel import create_cancel_inline_button
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from handler.command import Command

from typing import List

logger = configure_logging(__name__)


@force_coroutine_logging
async def wallet_delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    query = update.callback_query
    await query.answer()
    # 지갑 리스트들을 가져와서 선택할 수 있게 만들어주기
    DeleteSetting.clear_setting(context)
    DeleteSetting.get_setting(context)
    account_manager: AccountManager = await fetch_account_manager(context)
    account_list: List[Account] = await account_manager.get_all_accounts()

    # 닉네임으로 버튼 생성
    text = (
        "Delete Wallet\n\n"
        "Please select one of the wallets listed below.\n"
        "If you don’t wish to proceed, click the `Cancel` button."
    )
    buttons = [
        [
            InlineKeyboardButton(
                account.nickname if not account.is_active else f"✅ {account.nickname}",
                callback_data=(f"delete_wallet|{account.nickname}"),
            )
        ]
        for account in account_list
    ]
    buttons.append([create_cancel_inline_button(Command.WALLET)])
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return DeleteState.SELECT


# ================================
# 지갑 변경
# ================================
@force_coroutine_logging
async def wallet_delete_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    logger.debug("wallet_delete_select")
    query = update.callback_query
    await query.answer()
    delete_setting: DeleteSetting = DeleteSetting.get_setting(context)

    nickname = str(update.callback_query.data.split("|")[1])
    delete_setting.nickname = nickname

    keyboard = [
        [InlineKeyboardButton("OK", callback_data="DELETE_WALLET_OK")],
        [create_cancel_inline_button(Command.WALLET)],
    ]

    await query.edit_message_text(
        "Are you sure you want to delete the wallet?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return DeleteState.DELETE


@force_coroutine_logging
async def wallet_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    logger.debug("wallet_delete")
    query = update.callback_query
    await query.answer()
    delete_setting: DeleteSetting = DeleteSetting.get_setting(context)

    account_manager: AccountManager = await fetch_account_manager(context)
    await account_manager.delete_wallet(delete_setting.nickname)

    message = f"`{delete_setting.nickname}` is deleted."
    await query.edit_message_text(
        message,
        parse_mode="Markdown",
    )
    await wallet_start(update, context)
    return WalletState.SELECT_ACTION


delete_state = {
    DeleteState.SELECT: [
        CallbackQueryHandler(wallet_delete_select, pattern="^delete_wallet\|"),
    ],
    DeleteState.DELETE: [
        CallbackQueryHandler(wallet_delete, pattern="^DELETE_WALLET_OK$"),
    ],
}
