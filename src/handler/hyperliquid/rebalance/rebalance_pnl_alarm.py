from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api import AccountService
from api.hyperliquid import RebalanceService
from .states import PnlStates, RebalanceStates
from .rebalance_start import rebalance_start

from telegram import (
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

logger = configure_logging(__name__)

account_service = AccountService()
rebalance_service = RebalanceService()


@force_coroutine_logging
async def rebalance_pnl_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    message = "Please enter the target PNL(%) to receive alerts."
    await update.callback_query.answer()

    await update.callback_query.edit_message_text(
        message,
    )

    return PnlStates.CHANGE


@force_coroutine_logging
async def rebalance_pnl_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    try:
        target_pnl = float(update.message.text)
    except:
        message = "Please enter a number."
        await update.message.reply_text(
            text=message,
        )
        return ConversationHandler.END

    await rebalance_service.update_target_pnl_percent_rebalancing(
        context._user_id,
        target_pnl_percent=target_pnl,
    )

    message = f"Target PNL has been set to {target_pnl}%."

    await update.effective_chat.send_message(
        text=message,
    )
    await rebalance_start(update, context)
    return RebalanceStates.SELECT_ACTION


pnl_states = {
    PnlStates.CHANGE: [
        MessageHandler(filters=filters.TEXT, callback=rebalance_pnl_change),
    ],
}
