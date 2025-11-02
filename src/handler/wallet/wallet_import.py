from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

from .states import ImportState
from .settings import ImportSetting
from handler.command import Command
from hypurrquant.models.account import Account
from handler.utils.cancel import (
    initialize_handler,
    main_menu,
    create_cancel_inline_button,
)
from handler.utils.utils import answer, send_or_edit
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)


import re
from typing import List
import asyncio

logger = configure_logging(__name__)


# ================================
# Wallet Import Start
# ================================
@force_coroutine_logging
@initialize_handler(ImportSetting)
async def wallet_import_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    setting = ImportSetting.get_setting(context)

    text = "Import Wallet\n\nPlease enter the secret key of the wallet to import."
    kb = [[create_cancel_inline_button(setting.return_to)]]
    await send_or_edit(update, context, text, reply_markup=InlineKeyboardMarkup(kb))
    return ImportState.IMPORT_KEY


# ================================
# Private Key Import
# ================================
@force_coroutine_logging
async def wallet_import_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")

    import_setting: ImportSetting = ImportSetting.get_setting(context)
    private_key = update.message.text
    import_setting.private_key = private_key

    text = "Please provide a nickname for the account you want to import. \nNicknames must be unique and can only contain a combination of letters and numbers, with a maximum length of 8 characters."
    kb = [[create_cancel_inline_button(import_setting.return_to)]]
    await send_or_edit(update, context, text, reply_markup=InlineKeyboardMarkup(kb))

    return ImportState.SET_NICKNAME


# ================================
# nickname 입력받기
# ================================
@force_coroutine_logging
async def set_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    account_hodler: AccountManager = await fetch_account_manager(context)
    import_setting: ImportSetting = ImportSetting.get_setting(context)
    account_list: List[Account] = await account_hodler.get_all_accounts()

    nickname = update.message.text

    # validation: 영문+숫자만 허용, 길이 제한
    if not re.match(r"^[a-zA-Z0-9]+$", nickname) or len(nickname) > 8:
        text = f"Nicknames must be unique and can only contain a combination of letters and numbers. Try again. /{Command.WALLET}"
        await send_or_edit(update, context, text)
        await asyncio.sleep(1)
        return await main_menu(update, context, import_setting.return_to)

    # validation: 닉네임 중복 확인
    if any(account.nickname == nickname for account in account_list):
        text = f"The nickname you entered already exists. Try again. /{Command.WALLET}"
        await send_or_edit(update, context, text)
        await asyncio.sleep(1)
        return await main_menu(update, context, import_setting.return_to)

    # 계정 생성
    new_account: Account = await account_hodler.import_wallet(
        import_setting.private_key, nickname
    )
    text = (
        "Account import complete!\n\n "
        f"Public key is `{new_account.public_key}`\n"
        "If you want to start using it immediately, please go to Wallet Change and update your active wallet."
    )
    await send_or_edit(update, context, text)
    await asyncio.sleep(1)
    return await main_menu(update, context, import_setting.return_to)


import_state = {
    ImportState.IMPORT_KEY: [
        MessageHandler(filters=filters.TEXT, callback=wallet_import_key),
    ],
    ImportState.SET_NICKNAME: [
        MessageHandler(filters=filters.TEXT, callback=set_nickname)
    ],
}
