from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)

from api.hyperliquid import HLAccountService
from .states import SendUsdcStates
from .settings import SendUsdcSetting

from handler.models.perp_balance import PerpBalanceMapping
from handler.command import Command
from handler.utils.cancel import main_menu, initialize_handler
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from handler.utils.utils import send_or_edit, answer

import re
import asyncio


from handler.utils.cancel import create_cancel_inline_button

logger = configure_logging(__name__)
hl_account_service = HLAccountService()

CALLBACK_PREFIX = "BALANCE_SEND_USDC"


# ================================
# 1) 시작
# ================================
@force_coroutine_logging
@initialize_handler(setting_cls=SendUsdcSetting)
async def balance_send_usdc_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    setting: SendUsdcSetting = SendUsdcSetting.get_setting(context)

    # 데이터 셋팅
    account_manager: AccountManager = await fetch_account_manager(context)
    account_list, active_account = await asyncio.gather(
        account_manager.get_all_accounts(), account_manager.get_active_account()
    )

    message = "You can only send requests via the PERP account.\n\n"
    message += "Make sure the address is correct to avoid sending funds to the wrong account.\n"
    message += "Accounts not active in hyperliquid L1 incur a fee of 1 USDC for remittance. \n\n"
    message += "Please enter the public key of the destination account."

    kb = []

    for account in account_list:
        if account.nickname == active_account.nickname:
            continue
        kb.append(
            [
                InlineKeyboardButton(
                    text=f"{account.nickname}({account.public_key[:4]}...{account.public_key[-4:]})",
                    callback_data=f"ac_se|{account.public_key}",
                )
            ]
        )

    kb.append([create_cancel_inline_button(setting.return_to)])
    await send_or_edit(
        update,
        context,
        message,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )

    return SendUsdcStates.SELECT_ACCOUNT


# ================================
# 2) 도착 계좌 선택
# ================================
@force_coroutine_logging
async def select_destination_account(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(f"triggerred by user: {context._user_id}")
    account_manager: AccountManager = await fetch_account_manager(context)
    send_usdc_setting: SendUsdcSetting = SendUsdcSetting.get_setting(context)

    # 데이터 가져오기
    if update.message:
        destination_account = str(update.message.text)

    elif update.callback_query:
        query = update.callback_query
        await answer(update)
        destination_account = str(query.data.split("|")[1])
    else:
        await update.effective_message.reply_text(
            "Please enter a valid account public key."
        )
        return ConversationHandler.END
    logger.debug(f"destination_account: {destination_account}")
    send_usdc_setting.destination = destination_account

    # 잔액 확인
    balance = 0
    perp_balance_mapping: PerpBalanceMapping = (
        await account_manager.refresh_perp_balance(force=True)
    )

    balance = perp_balance_mapping.withdrawable
    message = f"Your balance is {balance}. Please enter an amount to send (must be at least $1.00 and no greater than your balance)."

    if update.message:
        await update.message.reply_text(message)
    else:
        await update.callback_query.edit_message_text(message, parse_mode="Markdown")

    return SendUsdcStates.SELECT_AMOUNT


# ================================
# 4) 가격 입력 완료 및 보내기
# ================================
@force_coroutine_logging
async def select_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")

    account_manager: AccountManager = await fetch_account_manager(context)
    send_usdc_setting: SendUsdcSetting = SendUsdcSetting.get_setting(context)
    perp_balance_mapping: PerpBalanceMapping = (
        await account_manager.refresh_perp_balance(force=True)
    )

    balance = perp_balance_mapping.withdrawable

    # 데이터 가져오기
    input = update.message.text

    # validation: 숫자만 허용
    if not re.fullmatch(r"^-?\d+(\.\d+)?$", input):
        await update.effective_message.reply_text(
            f"Please enter a valid number. Try again. /{Command.BALANCE}"
        )
        return ConversationHandler.END
    input = float(input)

    # validation: 1.0 이상, 잔액 이하
    logger.debug(f"input: {input}, balance: {balance}")
    if 1.0 > input or input > balance:
        await update.effective_message.reply_text(
            f"Please enter a positive number that is less than or equal to your balance. Try again. /{Command.BALANCE}"
        )
        return ConversationHandler.END

    # 보내기
    response = await hl_account_service.send_usdc(
        context._user_id, send_usdc_setting.destination, input
    )
    if response:
        message = f"{input} USDC has been sent to {send_usdc_setting.destination}"
        await update.effective_message.reply_text(message)

    else:
        await update.effective_message.reply_text("Failed to send USDC")

    return await main_menu(update, context, send_usdc_setting.return_to)


send_usdc_state = {
    SendUsdcStates.SELECT_ACCOUNT: [
        MessageHandler(filters=filters.TEXT, callback=select_destination_account),
        CallbackQueryHandler(
            callback=select_destination_account,
            pattern=f"^ac_se",
        ),
    ],
    SendUsdcStates.SELECT_AMOUNT: [
        MessageHandler(filters.TEXT, callback=select_amount)
    ],
}
