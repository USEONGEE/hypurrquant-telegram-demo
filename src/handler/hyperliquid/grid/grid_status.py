from telegram import (
    Update,
)
from telegram.ext import (
    ContextTypes,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api.hyperliquid import HLAccountService, CancelOrderService
from .states import *
from handler.utils.utils import answer
from handler.utils.account_helpers import fetch_active_account

logger = configure_logging(__name__)

cancel_order_service = CancelOrderService()
hl_account_service = HLAccountService()


# ================================
# 지갑 변경
# ================================
@force_coroutine_logging
async def grid_status_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    account = await fetch_active_account(context)
    response = await hl_account_service.grid_status(account.public_key)
    if not response:
        await update.effective_chat.send_message(
            "No grid orders found for the current account.", parse_mode="Markdown"
        )

    return GridState.SELECT_ACTION
