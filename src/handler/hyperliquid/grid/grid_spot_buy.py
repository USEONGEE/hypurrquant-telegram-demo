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
from api.hyperliquid import BuyOrderService
from .states import *
from .settings import GridSpotBuySetting
from .grid_start import grid_start
from handler.utils.utils import answer

logger = configure_logging(__name__)

buy_order_service = BuyOrderService()

# ======== UTILS ========
USAGE_MESSAGE = (
    "Please enter parameters in the format:\n"
    "TICKER START_PRICE END_PRICE TOTAL_VALUE SPLIT_COUNT\n"
    "Example: HYPE 30 33 120 6"
)

MIN_TOTAL_VALUE = 30.0


@force_coroutine_logging
async def grid_spot_buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    GridSpotBuySetting.clear_setting(context)
    GridSpotBuySetting.get_setting(context)

    message = (
        "Grid Spot Buy\n\n"
        "Please enter your grid spot-buy parameters in one line, separated by spaces:\n\n"
        "`TICKER START_PRICE END_PRICE TOTAL_VALUE SPLIT_COUNT`\n\n"
        "1. *TICKER*: trading symbol (e.g. `HYPE`)\n"
        "2. *START_PRICE*: grid start price (e.g. `30`)\n"
        "3. *END_PRICE*: grid end price (e.g. `33`)\n"
        "4. *TOTAL_VALUE*: total USDC to spend (e.g. `120`)\n"
        "5. *SPLIT_COUNT*: number of grid slices (orders), integer ≥ 2 and ≤ 30 (e.g. `6`)\n"
        "6. Each order `(TOTAL_VALUE ÷ SPLIT_COUNT)` must be ≥ `15` USDC. (e.g. `120/6 = 20`)\n"
        "7. To cancel, type `X` or `x`.\n\n"
        "**Example:**\n"
        "`HYPE 30 33 120 6`\n"
    )
    await update.callback_query.edit_message_text(message, parse_mode="Markdown")
    return GridSpotBuyState.TYPING


@force_coroutine_logging
async def grid_parsing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    text = update.message.text.strip()
    # 취소 처리
    if text.lower() == "x":
        GridSpotBuySetting.clear_setting(context)
        return await grid_start(update, context)

    setting = GridSpotBuySetting.get_setting(context)

    parse_grid_spot_buy(context, text)

    ticker = setting.ticker
    start_price = setting.start_price
    end_price = setting.end_price
    total_value = setting.total_value
    count = setting.count

    logger.info(
        f"Parsed Grid Spot order: {ticker}, {total_value} USDC, {start_price} - {end_price}, {count} splits"
    )

    confirm_message = (
        f"*Confirm grid Spot Buy*\n\n"
        f"Ticker: `{ticker}`\n"
        f"Start Price: `{start_price}`\n"
        f"End Price: `{end_price}`\n"
        f"Total Value: `{total_value} USDC`\n"
        f"Split Count: `{count}`\n\n"
        "Do you want to proceed?"
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "Confirm", callback_data=GridSpotBuyState.CONFIRM.value
            ),
            InlineKeyboardButton("Cancel", callback_data="grid_cancel"),
        ],
    ]
    await update.message.reply_text(
        confirm_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    return GridSpotBuyState.CONFIRM


@force_coroutine_logging
async def grid_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")

    def validate():
        setting = GridSpotBuySetting.get_setting(context)
        start_price = setting.start_price
        end_price = setting.end_price
        total_value = setting.total_value
        count = setting.count
        if start_price <= 0:
            raise ValueError("START_PRICE must be greater than 0.")
        if end_price <= start_price:
            raise ValueError("END_PRICE must be greater than START_PRICE.")
        if total_value < MIN_TOTAL_VALUE:
            raise ValueError("TOTAL_VALUE must be at least 30 USDC.")
        if count < 2 or count > 30:
            raise ValueError("SPLIT_COUNT must be an integer between 2 and 30.")

    await answer(update)
    validate()
    await buy_order_service.grid_spot_buy(
        telegram_id=str(context._user_id),
        ticker=GridSpotBuySetting.get_setting(context).ticker,
        start_price=GridSpotBuySetting.get_setting(context).start_price,
        end_price=GridSpotBuySetting.get_setting(context).end_price,
        total_value=GridSpotBuySetting.get_setting(context).total_value,
        count=GridSpotBuySetting.get_setting(context).count,
    )
    await update.callback_query.edit_message_text(
        "Grid Spot Buy has been successfully set up.",
        parse_mode="Markdown",
    )
    GridSpotBuySetting.clear_setting(context)
    return await grid_start(update, context)


def parse_grid_spot_buy(context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    Parse a one-line grid spot-buy command:
      TICKER START_PRICE END_PRICE TOTAL_VALUE SPLIT_COUNT

    Raises:
        ValueError: if the format is invalid or any validation rule fails.
    """
    parts = text.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid number of arguments. {USAGE_MESSAGE}")

    ticker, start_str, end_str, total_str, count_str = parts

    # Convert types
    try:
        start_price = float(start_str)
        end_price = float(end_str)
        total_value = float(total_str)
        split_count = int(count_str)
    except ValueError:
        raise ValueError(f"Could not parse numbers. {USAGE_MESSAGE}")

    # Validation rules
    if start_price <= 0:
        raise ValueError("START_PRICE must be greater than 0.")
    if end_price <= start_price:
        raise ValueError("END_PRICE must be greater than START_PRICE.")
    if total_value < MIN_TOTAL_VALUE:
        raise ValueError(f"TOTAL_VALUE must be at least {int(MIN_TOTAL_VALUE)} USDC.")
    if split_count < 2 or split_count > 30:
        raise ValueError("SPLIT_COUNT must be an integer between 2 and 30.")

    settings = GridSpotBuySetting.get_setting(context)
    settings.ticker = ticker.upper()
    settings.start_price = start_price
    settings.end_price = end_price
    settings.total_value = total_value
    settings.count = split_count


# ====================

grid_spot_buy_states = {
    GridSpotBuyState.TYPING: [MessageHandler(filters.TEXT, grid_parsing)],
    GridSpotBuyState.CONFIRM: [
        CallbackQueryHandler(
            grid_confirm, pattern=f"^{GridSpotBuyState.CONFIRM.value}$"
        )
    ],
}
