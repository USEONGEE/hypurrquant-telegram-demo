from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api.hyperliquid import SellOrderService
from .states import *
from .settings import (
    GridSpotSellSetting,
)
from .grid_start import grid_start
from handler.utils.utils import answer

logger = configure_logging(__name__)

sell_order_service = SellOrderService()

# ======== UTILS ========
USAGE_MESSAGE = (
    "Please enter parameters in the format:\n"
    "TICKER START_PRICE END_PRICE TOTAL_QTY_ASSET SPLIT_COUNT\n"
    "Example: HYPE 30 33 5 6"
)

MAX_SPLIT_COUNT = 30


@force_coroutine_logging
async def grid_spot_sell_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    GridSpotSellSetting.clear_setting(context)
    GridSpotSellSetting.get_setting(context)

    message = (
        "Grid Spot Sell\n\n"
        "Please enter your grid spot-sell parameters in one line, separated by spaces:\n\n"
        "`TICKER START_PRICE END_PRICE`\n\n"
        "1. *TICKER*: asset symbol (e.g. `HYPE`)\n"
        "2. *START_PRICE*: grid start (lowest) price (e.g. `40`)\n"
        "3. *END_PRICE*: grid end (highest) price (e.g. `45`)\n"
        "4. Your total order quantity is evenly distributed at optimized price points throughout the range, based on your current balance.\n"
        "5. To cancel, type `X` or `x`.\n\n"
        "**Example:**\n"
        "`HYPE 40 45`\n"
    )
    await update.callback_query.edit_message_text(message, parse_mode="Markdown")
    return GridSpotSellState.TYPING


@force_coroutine_logging
async def grid_spot_sell_parsing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    text = update.message.text.strip()
    if text.lower() == "x":
        GridSpotSellSetting.clear_setting(context)
        await update.message.reply_text("Grid sell setup cancelled.")
        return await grid_start(update, context)

    setting = GridSpotSellSetting.get_setting(context)
    parse_grid_spot_sell(context, text)

    ticker = setting.ticker
    start_price = setting.start_price
    end_price = setting.end_price

    logger.info(f"Parsed Grid Spot sell: {ticker}, {start_price}-{end_price}, ")

    confirm_message = (
        f"*Confirm Grid Spot Sell*\n\n"
        f"Ticker: `{ticker}`\n"
        f"Start Price: `{start_price}`\n"
        f"End Price: `{end_price}`\n"
        "Do you want to proceed?"
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "Confirm", callback_data=GridSpotSellState.CONFIRM.value
            ),
            InlineKeyboardButton("Cancel", callback_data="grid_cancel"),
        ]
    ]
    await update.message.reply_text(
        confirm_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    return GridSpotSellState.CONFIRM


@force_coroutine_logging
async def grid_spot_sell_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")

    def validate():
        setting = GridSpotSellSetting.get_setting(context)
        if setting.start_price <= 0:
            raise ValueError("START_PRICE must be greater than 0.")
        if setting.end_price <= setting.start_price:
            raise ValueError("END_PRICE must be more than START_PRICE.")

    await answer(update)
    validate()
    await sell_order_service.grid_spot_sell(
        telegram_id=str(update.effective_user.id),
        ticker=GridSpotSellSetting.get_setting(context).ticker,
        start_price=GridSpotSellSetting.get_setting(context).start_price,
        end_price=GridSpotSellSetting.get_setting(context).end_price,
    )
    await update.callback_query.edit_message_text(
        "Grid Spot Sell has been successfully set up.",
        parse_mode="Markdown",
    )
    GridSpotSellSetting.clear_setting(context)
    return await grid_start(update, context)


def parse_grid_spot_sell(context: ContextTypes.DEFAULT_TYPE, text: str):
    parts = text.split()
    if len(parts) != 3:
        raise ValueError(f"Invalid args. {USAGE_MESSAGE}")
    ticker, start_str, end_str = parts
    try:
        start_price = float(start_str)
        end_price = float(end_str)
    except ValueError:
        raise ValueError(f"Could not parse numbers. {USAGE_MESSAGE}")
    if start_price <= 0:
        raise ValueError("START_PRICE must be > 0.")
    if end_price <= start_price:
        raise ValueError("END_PRICE must be < START_PRICE.")

    setting = GridSpotSellSetting.get_setting(context)
    setting.ticker = ticker.upper()
    setting.start_price = start_price
    setting.end_price = end_price


# Conversation states mapping
grid_spot_sell_states = {
    GridSpotSellState.TYPING: [MessageHandler(filters.TEXT, grid_spot_sell_parsing)],
    GridSpotSellState.CONFIRM: [
        CallbackQueryHandler(
            grid_spot_sell_confirm, pattern=f"^{GridSpotSellState.CONFIRM.value}$"
        )
    ],
}
