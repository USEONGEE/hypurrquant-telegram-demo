from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes, MessageHandler, filters, CallbackQueryHandler
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api import AccountService
from api.hyperliquid import DcaService
from handler.utils.utils import answer, send_or_edit
from .states import *
from .cancel import cancel_keyboard_button
from .settings import (
    DcaSetting,
    DcaDeleteSpotSetting,
)
from .dca_start import dca_start
from .utils import format_dca_spot_list
import asyncio

logger = configure_logging(__name__)

account_service = AccountService()
dca_service = DcaService()


@force_coroutine_logging
async def dca_delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    dca_setting = DcaSetting.get_setting(context)
    DcaDeleteSpotSetting.clear_setting(context)
    logger.debug(f"DCA setting: {dca_setting}")

    if len(dca_setting.dca_spot_list) == 0:
        await send_or_edit(
            update,
            context,
            "No DCA orders found. Please create a DCA order first.",
            parse_mode="Markdown",
        )
        await asyncio.sleep(1.5)
        return await dca_start(update, context)

    message = format_dca_spot_list(dca_setting.dca_spot_list)
    # 삭제할 번호를 입력하라는 메시지
    message += "\n\n*Enter the number of the DCA record you want to delete:* if you want to cancel, type `X` or `x`.\n\n"

    # 3개씩 짤라서 kb 만들기
    kb = []
    for index, dca in enumerate(dca_setting.dca_spot_list, start=1):
        kb.append(
            [
                InlineKeyboardButton(
                    index,
                    callback_data=f"{DcaDeleteStates.SELECT.value}|{index}",
                )
            ]
        )

    kb.append(cancel_keyboard_button)

    await send_or_edit(
        update,
        context,
        message,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )
    # 번호 입력을 기다리는 상태로 전환
    return DcaDeleteStates.SELECT


@force_coroutine_logging
async def dca_delete_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    dca_setting = DcaSetting.get_setting(context)

    # 사용자가 입력한 번호
    user_input = update.callback_query.data.split("|")[1].strip()
    try:
        index = int(user_input) - 1  # Convert to zero-based index
        logger.debug(f"User input index: {index}")
        if index < 0 or index >= len(dca_setting.dca_spot_list):
            raise ValueError("Invalid number.")
        DcaDeleteSpotSetting.get_setting(context).delete_index = index
        dca_to_delete = dca_setting.dca_spot_list[index]
        kb = [
            [
                InlineKeyboardButton(
                    "Confirm",
                    callback_data=f"{DcaDeleteStates.CONFIRM.value}",
                ),
            ],
            cancel_keyboard_button,
        ]
        text = f"Are you sure you want to delete the DCA record for {dca_to_delete['symbol']}?"
        await send_or_edit(
            update,
            context,
            text,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown",
        )

        # Confirm deletion
        return DcaDeleteStates.CONFIRM
    except ValueError as e:
        await update.effective_chat.send_message(
            f"Error: {str(e)}. Please enter a valid number."
        )
        return await dca_start(update, context)


@force_coroutine_logging
async def dca_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    dca_setting = DcaSetting.get_setting(context)

    # 사용자가 입력한 번호
    index = DcaDeleteSpotSetting.get_setting(context).delete_index

    dca_to_delete = dca_setting.dca_spot_list[index]
    await dca_service.delete_timeslice_spot(dca_to_delete["id"])
    text = f"DCA record for {dca_to_delete['symbol']} deleted successfully."
    await send_or_edit(
        update,
        context,
        text,
        parse_mode="Markdown",
    )
    await asyncio.sleep(1)
    return await dca_start(update, context)


delete_states = {
    DcaDeleteStates.SELECT: [
        CallbackQueryHandler(
            dca_delete_select, pattern=f"^{DcaDeleteStates.SELECT.value}"
        ),
    ],
    DcaDeleteStates.CONFIRM: [
        CallbackQueryHandler(
            dca_delete_confirm, pattern=f"^{DcaDeleteStates.CONFIRM.value}$"
        ),
    ],
}
