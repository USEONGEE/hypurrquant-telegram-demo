from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api.hyperliquid import CopytradingService
from .states import (
    OrderValueStates,
    CopytradingStates,
)
from .copytrading_start import copytrading_start

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

logger = configure_logging(__name__)

copytrading_service = CopytradingService()


@force_coroutine_logging
async def copytrading_order_value_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    message = "Please enter order size."
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        message,
    )

    return OrderValueStates.CHANGE


@force_coroutine_logging
async def copytrading_order_value_change(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    try:
        order_value = float(update.message.text)
    except:
        message = "Please enter a number. Try again."
        await update.message.reply_text(
            text=message,
        )
        return ConversationHandler.END

    if order_value < 20:
        message = "Order value must be at least 20$. Try again."
        await update.message.reply_text(
            text=message,
        )
        return ConversationHandler.END

    await copytrading_service.update_order_value_usdc_copytrading(
        context._user_id,
        order_value_usdc=order_value,
    )

    message = f"Order size has been set to {order_value}$."

    await update.effective_chat.send_message(
        text=message,
    )
    await copytrading_start(update, context)
    return CopytradingStates.SELECT_ACTION


order_value_states = {
    OrderValueStates.CHANGE: [
        MessageHandler(filters=filters.TEXT, callback=copytrading_order_value_change),
    ],
}
