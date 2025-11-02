from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram import Update, InlineKeyboardButton
from hypurrquant.logging_config import (
    force_coroutine_logging,
)
from hypurrquant.logging_config import configure_logging
from .lpvault_start import lpvault_command

logger = configure_logging(__name__)


@force_coroutine_logging
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await update.callback_query.answer()
    return await lpvault_command(update, context)


cancel_handler = CallbackQueryHandler(cancel, pattern="^lpvault_cancel$")

cancel_keyboard_button = [
    InlineKeyboardButton("Cancel", callback_data="lpvault_cancel")
]
