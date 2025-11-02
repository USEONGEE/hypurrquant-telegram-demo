from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler

from handler.command import Command
from api.hyperliquid import HLAccountService
from .states import PerpToSpotStates
from handler.models.perp_balance import PerpBalanceMapping
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.utils import answer, send_or_edit
from handler.utils.cancel import (
    create_cancel_inline_button,
    main_menu,
    initialize_handler,
)
from handler.utils.account_manager import AccountManager
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from .settings import PerpToSpotSetting
import re
import asyncio

hl_account_service = HLAccountService()
logger = configure_logging(__name__)


@force_coroutine_logging
@initialize_handler(setting_cls=PerpToSpotSetting)
async def balance_perp_to_spot_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    # 데이터 가져오기
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    setting: PerpToSpotSetting = PerpToSpotSetting.get_setting(context)
    account_manager: AccountManager = await fetch_account_manager(context)
    perp_balance_mapping: PerpBalanceMapping = (
        await account_manager.refresh_perp_balance(force=True)
    )

    # validaiton: 최소 주문 금액
    if perp_balance_mapping.withdrawable < 1.0:
        text = "You don't have enough USDC to send. Please try again later."
        await send_or_edit(update, context, text)
        await asyncio.sleep(1)
        return await main_menu(update, context, setting.return_to)

    text = f"How much USDC would you like to send? \nPlease specify an amount between the {1.0} and {perp_balance_mapping.withdrawable} allowed limits.\n\nIf you want to send all your USDC, type 'all'"

    # cancle inline keyboard
    await send_or_edit(
        update,
        context,
        text,
        reply_markup=InlineKeyboardMarkup(
            [[create_cancel_inline_button(Command.BALANCE)]]
        ),
        parse_mode="Markdown",
    )

    return PerpToSpotStates.PERP_TO_SPOT


@force_coroutine_logging
async def perp_to_spot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    setting: PerpToSpotSetting = PerpToSpotSetting.get_setting(context)

    account_manager: AccountManager = await fetch_account_manager(context)
    perp_balance_mapping: PerpBalanceMapping = (
        await account_manager.get_perp_balance_mapping()
    )

    amount = update.message.text
    # validaiton: 정수 및 소수
    if amount.lower() == "all":
        amount = perp_balance_mapping.withdrawable
    else:
        if not re.match(r"^\d+(\.\d+)?$", amount):  # 정수 또는 소수 허용
            text = "Please enter a valid amount. Try again."
            await update.effective_message.reply_text(text)
            return ConversationHandler.END

    # validaiton: 올바른 금액
    if float(amount) < 1.0 or float(amount) > perp_balance_mapping.withdrawable:
        text = f"Please enter an amount between {1.0} and {perp_balance_mapping.withdrawable}. Try again. /{Command.BALANCE}"
        await update.effective_message.reply_text(text)
        return ConversationHandler.END

    response = await hl_account_service.perp_to_spot(context._user_id, amount)
    if response:
        await update.effective_message.reply_text("Success!")
        await account_manager.refresh_all(force=True)
    else:
        await update.effective_message.reply_text(
            f"The perp to spot operation has failed. Try again. /{Command.BALANCE}"
        )

    return await main_menu(update, context, setting.return_to)


perp_to_spot_states = {
    PerpToSpotStates.PERP_TO_SPOT: [
        MessageHandler(filters=filters.TEXT, callback=perp_to_spot)
    ]
}
