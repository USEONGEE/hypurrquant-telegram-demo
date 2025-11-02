from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api.hyperliquid import CopytradingService
from .states import (
    PnlStates,
    CopytradingStates,
)
from .copytrading_start import copytrading_start

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

logger = configure_logging(__name__)
copytrading_service = CopytradingService()


@force_coroutine_logging
async def copytrading_pnl_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    message = "Please enter the target PNL(%) to receive alerts."
    await update.callback_query.answer()

    await update.callback_query.edit_message_text(
        message,
    )

    return PnlStates.CHANGE


@force_coroutine_logging
async def copytrading_pnl_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    try:
        target_pnl = float(update.message.text)
    except:
        message = "Please enter a number."
        await update.message.reply_text(
            text=message,
        )
        return ConversationHandler.END

    await copytrading_service.update_target_pnl_percent_copytrading(
        context._user_id,
        target_pnl_percent=target_pnl,
    )

    message = f"Target PNL has been set to {target_pnl}%."

    await update.effective_chat.send_message(
        text=message,
    )
    await copytrading_start(update, context)
    return CopytradingStates.SELECT_ACTION


pnl_states = {
    PnlStates.CHANGE: [
        MessageHandler(filters=filters.TEXT, callback=copytrading_pnl_change),
    ],
}
