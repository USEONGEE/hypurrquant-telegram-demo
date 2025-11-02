from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
)

from api.hyperliquid import SellOrderService
from handler.command import Command
from handler.utils.cancel import main_menu
from handler.utils.utils import send_or_edit
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from .states import AllStates
from .settings import SellAllSetting
from .utils import can_operation_sell
from .exceptions import SELL_ALL_FAIL
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
import asyncio

logger = configure_logging(__name__)

sellOrderService = SellOrderService()

CALL_BACK_PREFIX = "SELL_ALL_OK"


@force_coroutine_logging
async def sell_all_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    구매량 선택
    """
    logger.debug("sell_all_start")
    query = update.callback_query
    await query.answer()

    SellAllSetting.clear_setting(context)
    all_setting: SellAllSetting = SellAllSetting.get_setting(context)

    if not can_operation_sell(context):
        await send_or_edit(
            update,
            context,
            "There are no stocks to sell. Please select stocks to sell first.",
        )
        await asyncio.sleep(1.5)
        return await main_menu(update, context, all_setting.return_to)

    message = (
        "You have selected to sell all. \n\n"
        "Are you sure you want to proceed? This action cannot be undone.\n"
    )

    keyboard = [
        [InlineKeyboardButton("OK", callback_data=CALL_BACK_PREFIX)],
        [InlineKeyboardButton("Cancel", callback_data="sell_cancel")],
    ]

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    return AllStates.SELL


@force_coroutine_logging
async def sell_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")

    logger.debug("sell_order")
    query = update.callback_query
    await query.answer()

    # 판매 주문 실행
    response = await sellOrderService.sell_order_market_all(context._user_id)

    # 잔고 갱신
    account_hodler: AccountManager = await fetch_account_manager(context)
    await account_hodler.refresh_spot_balance(force=True)

    if response:
        await update.callback_query.edit_message_text(
            f"Success! You can check your order history using /{Command.BALANCE}"
        )
        return ConversationHandler.END
    else:
        await update.callback_query.edit_message_text(SELL_ALL_FAIL)
        return ConversationHandler.END


all_states = {
    AllStates.SELL: [CallbackQueryHandler(sell_order, pattern=f"^{CALL_BACK_PREFIX}$")],
}
