from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api.hyperliquid import CopytradingService
from api.exception import ApiException
from .states import (
    SubscribeStates,
    CopytradingStates,
)
from .copytrading_start import copytrading_start
from .settings import CopytradingSetting
from telegram import (
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

logger = configure_logging(__name__)

copytrading_service = CopytradingService()


@force_coroutine_logging
async def copytrading_subscribe_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    message = "Please enter eth address in hyperliquid for copy trading."
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        message,
    )

    return SubscribeStates.SUBSCRIBE


@force_coroutine_logging
async def copytrading_subscribe_change(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    eth_address = update.message.text
    copytrading_setting = CopytradingSetting.get_setting(context)
    account = copytrading_setting.account
    try:
        await copytrading_service.subscribe(
            account.public_key,
            eth_address,
        )
    except ApiException as e:
        logger.info(f"Copy traidng 구독 중 예외가 발생했습니다.", exc_info=True)
        await update.effective_chat.send_message(
            text=e.message,
        )
        return ConversationHandler.END
    except Exception as e:
        logger.exception(f"Copy trading 구독 중 예외가 발생했습니다.")

    message = f"success"

    await update.effective_chat.send_message(
        text=message,
    )
    await copytrading_start(update, context)
    return CopytradingStates.SELECT_ACTION


subscribe_states = {
    SubscribeStates.SUBSCRIBE: [
        MessageHandler(filters=filters.TEXT, callback=copytrading_subscribe_change),
    ],
}
