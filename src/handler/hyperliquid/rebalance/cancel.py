from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram import Update, InlineKeyboardButton
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from .rebalance_start import rebalance_start

logger = configure_logging(__name__)


@force_coroutine_logging
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await update.callback_query.answer()
    return await rebalance_start(update, context)


cancel_handler = CallbackQueryHandler(cancel, pattern="^rebalance_cancel$")

cancel_keyboard_button = (
    [InlineKeyboardButton("Cancel", callback_data="rebalance_cancel")],
)
