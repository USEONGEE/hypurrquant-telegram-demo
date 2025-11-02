from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api.hyperliquid import CancelOrderService
from .cancel import cancel_keyboard_button
from .states import *
from .grid_start import grid_start
from handler.utils.utils import answer, send_or_edit

logger = configure_logging(__name__)

cancel_order_service = CancelOrderService()


# ================================
# 지갑 변경
# ================================


@force_coroutine_logging
async def grid_cancel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    logger.debug(f"cancel keyboard type = {type(cancel_keyboard_button)}")
    keyboard = [
        [InlineKeyboardButton("OK", callback_data=GridCancelState.CONFIRM.value)],
        cancel_keyboard_button,
    ]

    await send_or_edit(
        update,
        context,
        "Are you sure you want to cancel all orders?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    return GridCancelState.CONFIRM


@force_coroutine_logging
async def grid_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    query = update.callback_query
    await answer(update)
    response = await cancel_order_service.cancle_open_orders_all(str(context._user_id))
    logger.debug(f"cancel response = {response}")

    message = f"Success"
    await query.edit_message_text(
        message,
        parse_mode="Markdown",
    )
    return await grid_start(update, context)


grid_cancel_states = {
    GridCancelState.CONFIRM: [
        CallbackQueryHandler(grid_cancel, pattern=f"^{GridCancelState.CONFIRM.value}$")
    ],
}
