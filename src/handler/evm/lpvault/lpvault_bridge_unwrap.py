from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api import AccountService
from api.hyperliquid import HLAccountService
from handler.utils.utils import answer, send_or_edit
from handler.utils.decorators import require_builder_fee_approved
from .cancel import cancel_keyboard_button
from .states import LpvaultBridgeUnwrapState
from .settings import *
from .lpvault_start import lpvault_command
import asyncio

logger = configure_logging(__name__)

account_service = AccountService()
hl_account_service = HLAccountService()

MIN_HYPE = 0.2


@require_builder_fee_approved
@force_coroutine_logging
async def lpvault_bridge_unwrap_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info("bridge command triggered by user: %s", update.effective_user.id)
    await answer(update)
    await send_or_edit(
        update,
        context,
        "Loading 🔄",
        parse_mode="Markdown",
    )
    LpvaultBridgeUnwrapSetting.clear_setting(context)
    setting = LpvaultBridgeUnwrapSetting.get_setting(context)
    account = LpvaultSetting.get_setting(context).account
    setting.whype = await account_service.get_native_wrapped(account.public_key)

    if setting.whype < MIN_HYPE:
        text = f"You don't have enough WHYPE(min {MIN_HYPE}) to unwrap. Please deposit more WHYPE to your account."
        await send_or_edit(
            update,
            context,
            text,
        )
        await asyncio.sleep(3)
        return await lpvault_command(update, context)

    text = f"You have {setting.whype:.2f} WHYPE available for unwrapping. If you’d like to proceed, click the Confirm button."

    kb = [
        [
            InlineKeyboardButton(
                "Confirm",
                callback_data=f"{LpvaultBridgeUnwrapState.CONFIRM.value}",
            )
        ],
        cancel_keyboard_button,
    ]
    await send_or_edit(
        update,
        context,
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return LpvaultBridgeUnwrapState.CONFIRM


@force_coroutine_logging
async def lpvault_bridge_unwrap_confirm(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(
        "bridge confirm command triggered by user: %s", update.effective_user.id
    )
    await answer(update)
    await send_or_edit(
        update,
        context,
        "Unwrapping 🔄",
        parse_mode="Markdown",
    )

    setting = LpvaultBridgeUnwrapSetting.get_setting(context)
    account = LpvaultSetting.get_setting(context).account

    response = await hl_account_service.unwrap(
        str(context._user_id), account.nickname, setting.whype
    )

    if response:
        await send_or_edit(
            update,
            context,
            f"success",
        )
        await asyncio.sleep(1)

    else:
        await send_or_edit(
            update,
            context,
            "Something went wrong. Please try again later.",
        )
        await asyncio.sleep(1.5)

    return await lpvault_command(update, context)


lpvault_bridge_unwrap_states = {
    LpvaultBridgeUnwrapState.CONFIRM: [
        CallbackQueryHandler(
            lpvault_bridge_unwrap_confirm,
            pattern=f"^{LpvaultBridgeUnwrapState.CONFIRM.value}$",
        ),
    ]
}
