from telegram import Update, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from .states import CreateState, WalletState
from .wallet_start import wallet_start
from .settings import CreateSetting
from handler.command import Command
from hypurrquant.models.account import Account
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from handler.utils.cancel import (
    initialize_handler,
    main_menu,
    create_cancel_inline_button,
)
from handler.utils.utils import answer, send_or_edit
from handler.utils.account_helpers import fetch_account_manager
from handler.constants import MAX_ACCOUNT_PER_USER
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)


import re
from typing import List
import asyncio

logger = configure_logging(__name__)


# ================================
# 지갑 변경 시작
# ================================
@force_coroutine_logging
@initialize_handler(setting_cls=CreateSetting)
async def wallet_create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    setting: CreateSetting = CreateSetting.get_setting(context)
    account_hodler: AccountManager = await fetch_account_manager(context)
    account_list: List[Account] = await account_hodler.get_all_accounts()

    if account_list and len(account_list) >= MAX_ACCOUNT_PER_USER:
        text = f"You can create up to {MAX_ACCOUNT_PER_USER} accounts only."
        await send_or_edit(update, context, text)
        await asyncio.sleep(1)
        return await main_menu(update, context, setting.return_to)

    text = "Create Wallet\n\nPlease provide a nickname for the account you want to create. \nNicknames must be unique and can only contain a combination of letters and numbers, with a maximum length of 8 characters."

    kb = [[create_cancel_inline_button(setting.return_to)]]
    await send_or_edit(update, context, text, reply_markup=InlineKeyboardMarkup(kb))
    return CreateState.SET_NICKNAME


# ================================
# 닉네임 설정
# ================================
@force_coroutine_logging
async def wallet_create_set_nickname(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    account_hodler: AccountManager = await fetch_account_manager(context)
    account_list: List[Account] = await account_hodler.get_all_accounts()
    setting = CreateSetting.get_setting(context)
    nickname = update.message.text

    # validation: 영문+숫자만 허용, 길이 제한
    if not re.match(r"^[a-zA-Z0-9]+$", nickname) or len(nickname) > 8:
        text = f"Nicknames must be unique and can only contain a combination of letters and numbers. Try again. /{Command.WALLET}"
        await send_or_edit(update, context, text)
        await asyncio.sleep(1)
        return await main_menu(update, context, setting.return_to)

    # validation: `닉네임 중복 확인
    if any(account.nickname == nickname for account in account_list):
        text = f"The nickname you entered already exists. Try again. /{Command.WALLET}"
        await send_or_edit(update, context, text)
        await asyncio.sleep(1)
        return await main_menu(update, context, setting.return_to)

    # 계정 생성
    new_account: Account = await account_hodler.create_wallet(nickname)
    text = (
        "Account creation complete!\n\n "
        f"Public key is `{new_account.public_key}`\n"
        "If you want to start using it immediately, please go to Wallet Change and update your active wallet."
    )

    await update.effective_message.reply_text(text, parse_mode="Markdown")
    await wallet_start(update, context)
    return WalletState.SELECT_ACTION


create_states = {
    CreateState.SET_NICKNAME: [
        MessageHandler(filters=filters.TEXT, callback=wallet_create_set_nickname)
    ],
}
