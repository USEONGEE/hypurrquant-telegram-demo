from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
)

from .states import ChangeState
from .settings import ChangeSetting
from hypurrquant.models.account import Account
from handler.utils.utils import answer, format_buttons_grid, send_or_edit
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from handler.utils.cancel import (
    create_cancel_inline_button,
    main_menu,
    initialize_handler,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)


from typing import List

logger = configure_logging(__name__)


# ================================
# 지갑 변경 시작
# ================================
@force_coroutine_logging
@initialize_handler(setting_cls=ChangeSetting)
async def wallet_change_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    setting: ChangeSetting = ChangeSetting.get_setting(context)
    account_hodler: AccountManager = await fetch_account_manager(context)
    account_list: List[Account] = await account_hodler.get_all_accounts()

    # 닉네임으로 버튼 생성
    text = (
        "Change Wallet\n\n"
        "Please select one of the wallets listed below.\n\n"
        "• Active wallet: ✅ indicates the currently selected account\n"
        "• Requires approval: ⚠️ indicates this account needs builder‐fee approval and has limited access to features\n"
    )

    buttons = []

    for account in account_list:
        nickname = account.nickname
        if account.is_active:
            nickname = f"✅ {nickname}"
        if not account.is_approved_builder_fee:
            nickname += " ⚠️"
        buttons.append(
            InlineKeyboardButton(
                nickname,
                callback_data=(f"change_wallet|{account.nickname}"),
            )
        )

    buttons = format_buttons_grid(buttons, 3)

    buttons.append([create_cancel_inline_button(setting.return_to)])

    reply_markup = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return ChangeState.CHANGE


# ================================
# 지갑 변경
# ================================
@force_coroutine_logging
async def wallet_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    account_hodler: AccountManager = await fetch_account_manager(context)

    nickname = str(update.callback_query.data.split("|")[1])
    await account_hodler.change_wallet(nickname)
    active_account: Account = await account_hodler.get_active_account()
    logger.debug(f"Active account: {active_account.model_dump()}")

    message = f"`{active_account.nickname}` is activated."
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
    )

    return await main_menu(
        update, context, command=ChangeSetting.get_setting(context).return_to
    )


change_state = {
    ChangeState.CHANGE: [
        CallbackQueryHandler(wallet_change, pattern="^change_wallet\|"),
        # CallbackQueryHandler(cancel, pattern="^common_cancel"),
    ]
}
