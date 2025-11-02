from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api import AccountService
from .states import *
from .settings import GridSetting
from handler.utils.utils import answer, send_or_edit
from handler.utils.decorators import require_builder_fee_approved
from handler.utils.cancel import create_cancel_inline_button
from handler.command import Command

logger = configure_logging(__name__)

account_service = AccountService()


@require_builder_fee_approved
@force_coroutine_logging
async def grid_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    logger.info("grid command triggered by user: %s", update.effective_user.id)
    await answer(update)
    GridSetting.clear_setting(context)

    message = (
        "*Grid Trade*\n\n"
        "The Grid Trade feature is a service that automatically runs grid\-based trading on your account in both spot and perpetual markets\. It repeatedly places incremental buy and sell orders at fixed intervals within a specified price range, and lets you easily cancel all active grid orders or check your current grid status at any time\.\n\n"
        "*NOTE* Show Grid Status – View current grid order status \(only for BTC, ETH, SOL in spot\. test version, may not work\)"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "Grid Spot Buy",
                callback_data=f"{GridSpotBuyState.START.value}",
            ),
            InlineKeyboardButton(
                "Grid Spot Sell",
                callback_data=f"{GridSpotSellState.START.value}",
            ),
        ],
        [
            InlineKeyboardButton(
                "Grid Perp Open",
                callback_data=f"{GridPerpOpenState.START.value}",
            ),
            InlineKeyboardButton(
                "Grid Perp Close",
                callback_data=f"{GridPerpCloseState.START.value}",
            ),
        ],
        [
            InlineKeyboardButton(
                "Cancel All Orders",
                callback_data=f"{GridCancelState.START.value}",
            ),
        ],
        [
            InlineKeyboardButton(
                "Show Grid Status",
                callback_data=f"{GridStatusState.START.value}",
            ),
        ],
        [create_cancel_inline_button(Command.HYPERLIQUID_CORE_START)],
    ]

    await send_or_edit(
        update,
        context,
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2",
    )
    return GridState.SELECT_ACTION
