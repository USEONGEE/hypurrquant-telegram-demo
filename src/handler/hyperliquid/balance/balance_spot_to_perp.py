from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler

from handler.command import Command
from api.hyperliquid import HLAccountService
from .states import SpotToPerpStates
from .settings import SpotToPerpSetting
from handler.utils.utils import answer, send_or_edit
from handler.utils.cancel import (
    initialize_handler,
    main_menu,
    create_cancel_inline_button,
)
from handler.models.spot_balance import SpotBalanceMapping
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)


import re
import asyncio

hl_account_service = HLAccountService()

logger = configure_logging(__name__)


@force_coroutine_logging
@initialize_handler(setting_cls=SpotToPerpSetting)
async def balance_spot_to_perp_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(f"triggerred by user: {context._user_id}")
    # 데이터 가져오기
    await answer(update)
    account_manager: AccountManager = await fetch_account_manager(context)
    spot_balance_mapping: SpotBalanceMapping = (
        await account_manager.refresh_spot_balance(force=True)
    )

    # validaiton: 최소 주문 금액
    if spot_balance_mapping.usdc_balance < 1.0:
        text = "You don't have enough USDC to send. Please try again later."
        await send_or_edit(update, context, text)
        await asyncio.sleep(1)
        return await main_menu(
            update, context, SpotToPerpSetting.get_setting(context).return_to
        )

    text = f"How much USDC would you like to send? \nPlease specify an amount between the {1.0} and {spot_balance_mapping.usdc_balance} allowed limits.\n\nIf you want to send all your USDC, type 'all'"

    # cancle inline keyboard
    await send_or_edit(
        update,
        context,
        text,
        reply_markup=InlineKeyboardMarkup(
            [[create_cancel_inline_button(Command.BALANCE)]]
        ),
    )

    return SpotToPerpStates.SPOT_TO_PERP


@force_coroutine_logging
async def spot_to_perp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    # 금액 검증: 숫자만 허용

    account_manager: AccountManager = await fetch_account_manager(context)
    spot_balance_mapping: SpotBalanceMapping = (
        await account_manager.get_spot_balance_mapping()
    )

    amount = update.message.text

    # validaiton: 'all' 입력 처리
    if amount.lower() == "all":
        amount = spot_balance_mapping.usdc_balance
        if amount < 1.0:
            text = "You don't have enough USDC to send. Please try again later."
            await send_or_edit(update, context, text)
            await asyncio.sleep(1)
            return await main_menu(
                update, context, SpotToPerpSetting.get_setting(context).return_to
            )
    else:
        # validaiton: 정수 및 소수
        if not re.match(r"^\d+(\.\d+)?$", amount):
            text = f"Please enter a valid amount. Try again. /{Command.BALANCE}"
            await send_or_edit(update, context, text)
            return ConversationHandler.END

    # validaiton: 올바른 금액
    if float(amount) < 1.0 or float(amount) > spot_balance_mapping.usdc_balance:
        text = f"Please enter an amount between {1.0} and {spot_balance_mapping.usdc_balance}. Try again. /{Command.BALANCE}"
        await send_or_edit(update, context, text)
        return ConversationHandler.END

    response = await hl_account_service.spot_to_perp(context._user_id, amount)
    if response:
        await send_or_edit(update, context, "Success!")
        await account_manager.refresh_all(force=True)
    else:
        await send_or_edit(
            update,
            context,
            f"The spot to perp operation has failed. Try again. /{Command.BALANCE}",
        )

    return await main_menu(
        update, context, SpotToPerpSetting.get_setting(context).return_to
    )


spot_to_perp_states = {
    SpotToPerpStates.SPOT_TO_PERP: [
        MessageHandler(filters=filters.TEXT, callback=spot_to_perp)
    ]
}
