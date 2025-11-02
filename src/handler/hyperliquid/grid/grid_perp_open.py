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
from hypurrquant.services.bollinger_service import BollingerBandService
from api.hyperliquid import PerpOrderService
from .states import *
from .settings import GirdPerpOpenSetting
from .grid_start import grid_start
from handler.utils.utils import answer

logger = configure_logging(__name__)

perp_open_service = PerpOrderService()
bollinger_band_service = BollingerBandService()

# ======== UTILS ========
USAGE_MESSAGE = (
    "Please enter parameters in the format:\n"
    "TICKER START_PRICE END_PRICE TOTAL_VALUE SPLIT_COUNT\n"
    "Example: HYPE 30 33 120 6"
)

MIN_TOTAL_VALUE = 30.0


@force_coroutine_logging
async def grid_perp_open_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    GirdPerpOpenSetting.clear_setting(context)
    GirdPerpOpenSetting.get_setting(context)

    message = (
        "Grid Perp Open\n\n"
        "Please enter your grid perp-open parameters in one line, separated by spaces:\n\n"
        "`TICKER IS_LONG LEVERAGE START_PRICE END_PRICE TOTAL_VALUE COUNT`\n\n"
        "1. *TICKER*: trading symbol (e.g. `HYPE`)\n"
        "2. *DIRECTION*: `long` for long position, `short` for short\n"
        "3. *LEVERAGE*: leverage multiplier (e.g. `10`)\n"
        "4. *START_PRICE*: grid start price (e.g. `30`)\n"
        "5. *END_PRICE*: grid end price (e.g. `33`)\n"
        "6. *TOTAL_VALUE*: *margin* to allocate (≥ 30, e.g. `120`)\n"
        "7. *COUNT*: number of grid slices (orders), integer ≥ 2 (e.g. `6`)\n"
        "8. Each order `(TOTAL_VALUE ÷ COUNT)` must be ≥ `15` USDC (e.g. `120/6 = 20`).\n"
        "9. To cancel, type `X` or `x`.\n\n"
        "**Example:**\n"
        "`HYPE long 10 30 33 120 6`\n"
    )
    await update.callback_query.edit_message_text(message, parse_mode="Markdown")
    return GridPerpOpenState.TYPING


@force_coroutine_logging
async def grid_parsing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    text = update.message.text.strip()
    # 취소 처리
    if text.lower() == "x":
        GirdPerpOpenSetting.clear_setting(context)
        return await grid_start(update, context)

    setting = GirdPerpOpenSetting.get_setting(context)

    parse_grid_perp_open(context, text)

    ticker = setting.ticker
    start_price = setting.start_price
    end_price = setting.end_price
    total_value = setting.total_value
    count = setting.count

    logger.info(
        f"Parsed Grid Spot order: {ticker}, {total_value} USDC, {start_price} - {end_price}, {count} splits"
    )

    confirm_message = (
        f"Please confirm your grid spot buy order:\n\n"
        f"*Ticker:* `{ticker}`\n"
        f"*Direction:* `{'long' if setting.is_long else 'short'}`\n"
        f"*Leverage:* `{setting.leverage}`\n"
        f"*Start Price:* `{start_price}`\n"
        f"*End Price:* `{end_price}`\n"
        f"*Total Value:* `{total_value} USDC`\n"
        f"*Count:* `{count}`\n\n"
        "If everything looks correct, click Confirm. "
        "To cancel, click Cancel."
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "Confirm", callback_data=GridPerpOpenState.CONFIRM.value
            ),
            InlineKeyboardButton("Cancel", callback_data="grid_cancel"),
        ],
    ]
    await update.message.reply_text(
        confirm_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    return GridPerpOpenState.CONFIRM


@force_coroutine_logging
async def grid_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    await perp_open_service.open_grid(
        telegram_id=str(context._user_id),
        ticker=GirdPerpOpenSetting.get_setting(context).ticker,
        leverage=GirdPerpOpenSetting.get_setting(context).leverage,
        is_long=GirdPerpOpenSetting.get_setting(context).is_long,
        start_price=GirdPerpOpenSetting.get_setting(context).start_price,
        end_price=GirdPerpOpenSetting.get_setting(context).end_price,
        total_value=GirdPerpOpenSetting.get_setting(context).total_value,
        count=GirdPerpOpenSetting.get_setting(context).count,
    )
    await update.callback_query.edit_message_text(
        "Grid Spot Buy has been successfully set up.",
        parse_mode="Markdown",
    )
    GirdPerpOpenSetting.clear_setting(context)
    return await grid_start(update, context)


@force_coroutine_logging
def parse_grid_perp_open(context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    Parse a one-line grid perp-open command:
      TICKER IS_LONG IS_CROSS LEVERAGE START_PRICE END_PRICE TOTAL_VALUE COUNT

    Raises:
        ValueError: if the format is invalid or any validation rule fails.
    """
    parts = text.strip().split()
    if len(parts) != 7:
        raise ValueError(
            f"Invalid number of arguments. Expected 8 values: "
            f"TICKER IS_LONG IS_CROSS LEVERAGE START_PRICE END_PRICE TOTAL_VALUE COUNT"
        )

    (
        ticker,
        is_long_str,
        leverage_str,
        start_str,
        end_str,
        total_str,
        count_str,
    ) = parts

    # Convert types
    try:
        is_long = is_long_str.lower() in ("long")
        leverage = int(leverage_str)
        start_price = float(start_str)
        end_price = float(end_str)
        total_value = float(total_str)
        count = int(count_str)
    except Exception:
        raise ValueError("Could not parse one or more parameters. ")

    # Validation rules
    if leverage <= 0:
        raise ValueError("LEVERAGE must be a positive integer.")
    if start_price < 0:
        raise ValueError("START_PRICE must be ≥ 0.")
    if end_price <= start_price:
        raise ValueError("END_PRICE must be greater than START_PRICE.")
    if total_value < MIN_TOTAL_VALUE:
        raise ValueError(f"TOTAL_VALUE must be at least {MIN_TOTAL_VALUE} USDC.")
    if count < 2:
        raise ValueError("COUNT must be an integer ≥ 2.")

    # Populate settings
    settings = GirdPerpOpenSetting.get_setting(context)
    settings.ticker = ticker.upper()
    settings.is_long = is_long
    settings.leverage = leverage
    settings.start_price = start_price
    settings.end_price = end_price
    settings.total_value = total_value
    settings.count = count

    return settings


# ====================

grid_perp_open_states = {
    GridPerpOpenState.TYPING: [MessageHandler(filters.TEXT, grid_parsing)],
    GridPerpOpenState.CONFIRM: [
        CallbackQueryHandler(
            grid_confirm, pattern=f"^{GridPerpOpenState.CONFIRM.value}$"
        )
    ],
}
