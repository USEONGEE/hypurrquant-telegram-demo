from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram import Update, InlineKeyboardButton
from .close_start import close_start
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)

logger = configure_logging(__name__)


@force_coroutine_logging
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await update.callback_query.answer()
    return await close_start(update, context)


close_cancel = CallbackQueryHandler(cancel, pattern="^close_cancel$")
