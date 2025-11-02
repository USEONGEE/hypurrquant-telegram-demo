from telegram import Update
from telegram.ext import (
    ContextTypes,
)
from hypurrquant.logging_config import force_coroutine_logging

from api.hyperliquid import HLAccountService
from hypurrquant.models.account import Account
from handler.command import Command
from handler.utils.utils import send_or_edit, answer
from handler.utils.cancel import main_menu
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager

hl_account_service = HLAccountService()


@force_coroutine_logging
async def authenticate_refresh_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await answer(update)

    # 1. approve 요청
    account_manager: AccountManager = await fetch_account_manager(context)
    account: Account = await account_manager.get_active_account()
    await hl_account_service.approve_builder_fee(context._user_id, account.nickname)

    # 2. 성공 후 갱신
    await account_manager.get_active_account(True)
    text = f"Success!\n\n"

    await send_or_edit(update, context, text, parse_mode="Markdown")
    return await main_menu(update, context, Command.START)
