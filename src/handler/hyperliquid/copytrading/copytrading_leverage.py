from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api.hyperliquid import CopytradingService
from .states import (
    LeverageStates,
    CopytradingStates,
)
from .copytrading_start import copytrading_start

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

logger = configure_logging(__name__)

copytrading_service = CopytradingService()


@force_coroutine_logging
async def copytrading_leverage_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    message = "Please enter the leveragee to be set (X1-X3)."
    await update.callback_query.answer()

    await update.callback_query.edit_message_text(
        message,
    )

    return LeverageStates.CHANGE


@force_coroutine_logging
async def copytrading_leverage_change(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    try:
        target_pnl = int(update.message.text)
    except:
        message = "Please enter a number. Try again."
        await update.message.reply_text(
            text=message,
        )
        return ConversationHandler.END

    if target_pnl < 1 or target_pnl > 3:
        message = "Leverage must be between X1 and X3. Try again."
        await update.message.reply_text(
            text=message,
        )
        return ConversationHandler.END

    await copytrading_service.update_leverage_copytrading(
        context._user_id,
        leverage=target_pnl,
    )

    message = f"leverage has been set to X{target_pnl}."

    await update.effective_chat.send_message(
        text=message,
    )
    await copytrading_start(update, context)
    return CopytradingStates.SELECT_ACTION


leverage_states = {
    LeverageStates.CHANGE: [
        MessageHandler(filters=filters.TEXT, callback=copytrading_leverage_change),
    ],
}
