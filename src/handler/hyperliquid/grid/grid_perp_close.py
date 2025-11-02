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
from api.hyperliquid import PerpOrderService
from .states import *
from .settings import (
    GridPerpCloseSetting,
)
from .grid_start import grid_start
from handler.utils.utils import answer


logger = configure_logging(__name__)

perp_order_service = PerpOrderService()


@force_coroutine_logging
async def grid_perp_close_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    Ask user for grid close parameters: ticker, start, end, count
    """
    await answer(update)
    GridPerpCloseSetting.clear_setting(context)
    GridPerpCloseSetting.get_setting(context)
    message = (
        "Grid Perp Close\n\n"
        "Please enter your grid perp-close parameters in one line, separated by spaces:\n\n"
        "`TICKER START_PRICE END_PRICE`\n\n"
        "1. *TICKER*: trading symbol (e.g. `BTC/USDC`)\n"
        "2. *START_PRICE*: grid start price (e.g. `40`)\n"
        "3. *END_PRICE*: grid end price (e.g. `45`)\n"
        "4. Your total order quantity is evenly distributed at optimized price points throughout the range, based on your current balance.\n"
        "5. To cancel, type `X` or `x`.\n\n"
        "**Example:**\n"
        "`HYPE 40 45`"
    )
    await update.callback_query.edit_message_text(message, parse_mode="Markdown")
    return GridPerpCloseState.TYPING


@force_coroutine_logging
async def parse_grid_perp_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    Step 2: 파싱 및 컨펌 (Perp Close)
    """
    text = update.message.text.strip()
    if text.lower() == "x":
        return await grid_start(update, context)

    parts = text.split()
    if len(parts) != 3:
        return await update.message.reply_text(
            "Invalid input. Use: TICKER START_PRICE END_PRICE COUNT"
        )
    ticker, s_str, e_str = parts
    try:
        start_price = float(s_str)
        end_price = float(e_str)
    except ValueError:
        return await update.message.reply_text("Could not parse numbers. Please retry.")

    # 저장
    setting = GridPerpCloseSetting.get_setting(context)
    setting.ticker = ticker
    setting.start_price = start_price
    setting.end_price = end_price

    # 확인 메시지
    confirm_msg = (
        f"Please confirm your grid perp-close order:\n\n"
        f"*Ticker:* `{ticker}`\n"
        f"*Start Price:* `{start_price}`\n"
        f"*End Price:* `{end_price}`\n"
        "Click Confirm or Cancel."
    )
    kb = [
        [
            InlineKeyboardButton(
                "Confirm", callback_data=GridPerpCloseState.CONFIRM.value
            ),
            InlineKeyboardButton("Cancel", callback_data="grid_cancel"),
        ]
    ]
    await update.message.reply_text(
        confirm_msg,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return GridPerpCloseState.CONFIRM


@force_coroutine_logging
async def grid_close_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    Step 3: 수행 (Perp Close Confirm)
    """
    await answer(update)
    setting = GridPerpCloseSetting.get_setting(context)
    await perp_order_service.close_grid(
        telegram_id=update.effective_user.id,
        ticker=setting.ticker,
        start_price=setting.start_price,
        end_price=setting.end_price,
    )
    await update.callback_query.edit_message_text(
        "Grid Perp Close has been successfully set up.",
        parse_mode="Markdown",
    )
    GridPerpCloseSetting.clear_setting(context)
    return await grid_start(update, context)


grid_perp_close_states = {
    GridPerpCloseState.TYPING: [
        MessageHandler(filters.TEXT & ~filters.COMMAND, parse_grid_perp_close),
    ],
    GridPerpCloseState.CONFIRM: [
        CallbackQueryHandler(
            grid_close_confirm,
            pattern=f"^{GridPerpCloseState.CONFIRM.value}$",
        ),
    ],
}
