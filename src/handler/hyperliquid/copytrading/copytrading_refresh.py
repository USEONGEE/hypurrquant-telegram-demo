from telegram import Update
from telegram.ext import ContextTypes

from .copytrading_start import copytrading_start
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)

logger = configure_logging(__name__)


@force_coroutine_logging
async def copytrading_refresh_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    query = update.callback_query
    await query.answer()

    text = f"Success!\n\n"

    await query.edit_message_text(text, parse_mode="Markdown")
    return await copytrading_start(update, context)
