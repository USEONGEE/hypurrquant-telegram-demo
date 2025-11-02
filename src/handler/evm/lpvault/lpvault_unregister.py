from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import CallbackQueryHandler, ContextTypes
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api.exception import DecreaseLiquidityException
from api.account import AccountService
from api.lpvault import LpVaultService
from handler.utils.utils import answer, send_or_edit
from .states import LpvaultUnregisterState
from .settings import LpvaultSetting
from .cancel import cancel_keyboard_button
from .lpvault_start import lpvault_command

from typing import List
import asyncio

logger = configure_logging(__name__)


account_service = AccountService()
lp_vault_service = LpVaultService()


@force_coroutine_logging
async def lpvault_unregister_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await update.callback_query.answer()
    await answer(update)
    text = "Are you sure you want to unregister your auto lp manager?"

    kb = [
        [
            InlineKeyboardButton(
                "OK",
                callback_data=LpvaultUnregisterState.CONFIRM.value,
            ),
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

    return LpvaultUnregisterState.CONFIRM


@force_coroutine_logging
async def lpvault_wallet_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)

    setting = LpvaultSetting.get_setting(context)
    public_key = setting.account.public_key
    # lp_list = await lp_vault_service.lp_list(public_key)

    # positions도 정리할건지 물어보기
    text = "Do you want to decrease your positions as well?"

    await send_or_edit(
        update,
        context,
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Yes",
                        callback_data=f"{LpvaultUnregisterState.CONFIRM.value}|YES",
                    ),
                    InlineKeyboardButton(
                        "No",
                        callback_data=f"{LpvaultUnregisterState.CONFIRM.value}|NO",
                    ),
                ],
                cancel_keyboard_button,
            ]
        ),
        parse_mode="Markdown",
    )
    return LpvaultUnregisterState.CONFIRM2


async def lpvault_unregister_confirm(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)

    await send_or_edit(
        update,
        context,
        "Unregistering...",
        parse_mode="Markdown",
    )

    setting = LpvaultSetting.get_setting(context)
    public_key = setting.account.public_key
    lp_list = await lp_vault_service.lp_list(public_key)

    callback = update.callback_query.data
    remove_nft_positions = False
    if callback.endswith("|YES"):
        remove_nft_positions = True

    try:
        async with asyncio.TaskGroup() as tg:
            for lp in lp_list:
                tg.create_task(
                    lp_vault_service.unregister(
                        lp_vault_id=lp["_id"],
                        remove_nft_positions=remove_nft_positions,
                    )
                )
    except* DecreaseLiquidityException as e_group:
        logger.info(f"DecreaseLiquidityException", exc_info=e_group)
        await send_or_edit(
            update,
            context,
            "Your auto LP manager has been unregistered successfully, although not all liquidity could be decreased.",
            parse_mode="Markdown",
        )
        pass
    except* Exception as e:
        logger.error(f"Failed to unregister LPs: {e}", exc_info=e)
        await send_or_edit(
            update,
            context,
            "Something went wrong",
            parse_mode="Markdown",
        )

    else:
        await send_or_edit(
            update,
            context,
            "Your auto LP manager has been unregistered successfully.",
            parse_mode="Markdown",
        )

    await asyncio.sleep(2)
    return await lpvault_command(update, context)


unregister_states = {
    LpvaultUnregisterState.CONFIRM: [
        CallbackQueryHandler(
            lpvault_wallet_confirm, pattern=f"^{LpvaultUnregisterState.CONFIRM.value}"
        )
    ],
    LpvaultUnregisterState.CONFIRM2: [
        CallbackQueryHandler(
            lpvault_unregister_confirm,
            pattern=f"^{LpvaultUnregisterState.CONFIRM.value}|",
        )
    ],
}
