from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api import AccountService
from api.hyperliquid import DcaService
from .cancel import cancel_keyboard_button
from .states import *
from .settings import DcaTimesliceSpotSetting
from .dca_start import dca_start
from handler.utils.utils import answer, send_or_edit
from handler.utils.account_helpers import fetch_account_manager
import re

logger = configure_logging(__name__)

dca_service = DcaService()


@force_coroutine_logging
async def dca_spot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    DcaTimesliceSpotSetting.clear_setting(context)
    dca_timeslice_spot_setting = DcaTimesliceSpotSetting.get_setting(context)

    # _로 스플릿 후 마지막 값 가져오기
    # callback의 버튼 텍스트는 "dca_timeslice_spot|buy" 또는 "dca_timeslice_spot|sell" 형식
    if "|" not in update.callback_query.data:
        raise ValueError("Something went wrong. Please contact support.")
    # 마지막 부분을 소문자로 변환하여 접미사 확인
    suffix = update.callback_query.data.split("|")[-1].lower()
    if suffix == "buy":
        dca_timeslice_spot_setting.is_buy = True
    elif suffix == "sell":
        dca_timeslice_spot_setting.is_buy = False
    else:
        raise ValueError(
            f"Invalid suffix '{suffix}' in command. Expected 'buy' or 'sell'."
        )

    kb = [cancel_keyboard_button]

    message = (
        f"Create Spot {'Buy' if suffix == 'buy' else 'Sell'} DCA Order\n\n"
        "Please enter your DCA spot-order parameters in one line, separated by spaces:\n\n"
        "`TICKER AMOUNT_PER_ORDER INTERVAL SPLIT_COUNT`\n\n"
        "1. *TICKER*: trading symbol (e.g. `HYPE`)\n"
        f"2. *AMOUNT_PER_ORDER*: USDC per order, must be > `20` (e.g. `100.5`)\n"
        "3. *INTERVAL*: wait time until next order; combine any of\n"
        "   - `d` (days)\n"
        "   - `h` (hours)\n"
        "   - `m` (minutes)\n"
        "   e.g. `1h`, `2d30m`, `1d1h1m`  \n"
        "4. *SPLIT_COUNT*: how many total slices (orders), integer ≥ 2 (e.g. `5`)\n"
        "5. You can create a DCA Spot order with a maximum of 5 splits.\n\n"
        "**Example:**  \n"
        "`HYPE 50 1h30m 10`(tap to copy)\n"
    )
    await send_or_edit(
        update,
        context,
        message,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )
    return DcaTimeSliceSpotStates.TYPING


@force_coroutine_logging
async def dca_parsing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    text = update.message.text.strip()
    # 취소 처리
    if text.lower() == "x":
        DcaTimesliceSpotSetting.clear_setting(context)
        await update.message.reply_text("DCA setup cancelled.")
        return ConversationHandler.END

    setting = DcaTimesliceSpotSetting.get_setting(context)

    ticker, amount, interval, split_count = parse_spot_dca_input(text)

    setting.ticker = ticker
    setting.amount = amount
    setting.interval_seconds = interval
    setting.remaining_count = split_count

    logger.info(
        f"Parsed DCA Spot order: {ticker}, {amount} USDC, {interval} seconds, {split_count} splits"
    )
    # confirm message
    confirm_message = (
        f"*DCA Spot \[{"buy" if setting.is_buy else "sell"}] Order Parameters:*\n\n"
        f"*Ticker:* `{ticker}`\n"
        f"*Amount per Order:* `{amount}` USDC\n"
        f"*Interval:* `{text.split(" ")[2]}`\n"
        f"*Split Count:* `{split_count}`\n\n"
        "Is this correct?"
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "Confirm", callback_data=DcaTimeSliceSpotStates.CONFIRM.value
            ),
            InlineKeyboardButton("Cancel", callback_data="dca_cancel"),
        ],
    ]
    await update.message.reply_text(
        confirm_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    return DcaTimeSliceSpotStates.CONFIRM


@force_coroutine_logging
async def dca_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")

    def validate():
        setting = DcaTimesliceSpotSetting.get_setting(context)
        if not setting.ticker:
            raise ValueError("Ticker is not set.")
        if setting.amount < 20:
            raise ValueError("Amount per order must be greater than 20 USDC.")
        if setting.interval_seconds < 60:
            raise ValueError("Interval must be greater than 60 seconds.")
        if setting.remaining_count < 2:
            raise ValueError("Split count must be at least 2.")

    await answer(update)
    validate()
    account_manager = await fetch_account_manager(context)
    account = await account_manager.get_active_account()
    await dca_service.register_timeslice_spot(
        public_key=account.public_key,
        ticker=DcaTimesliceSpotSetting.get_setting(context).ticker,
        amount=DcaTimesliceSpotSetting.get_setting(context).amount,
        interval_seconds=DcaTimesliceSpotSetting.get_setting(context).interval_seconds,
        remaining_count=DcaTimesliceSpotSetting.get_setting(context).remaining_count,
        is_buy=DcaTimesliceSpotSetting.get_setting(context).is_buy,
    )
    await update.callback_query.edit_message_text(
        "DCA Spot order has been successfully created.",
        parse_mode="Markdown",
    )
    DcaTimesliceSpotSetting.clear_setting(context)
    return await dca_start(update, context)


# ======== UTILS ========
DURATION_RE = re.compile(r"(\d+)([dhm])")


def parse_duration_to_seconds(text: str) -> int:
    total = 0
    for amt, unit in DURATION_RE.findall(text):
        n = int(amt)
        if unit == "d":
            total += n * 86400
        elif unit == "h":
            total += n * 3600
        elif unit == "m":
            total += n * 60
    if total <= 0:
        raise ValueError(f"INTERVAL must be > 0 seconds, got '{text}'")
    return total


def parse_spot_dca_input(text: str) -> tuple[str, float, int, int]:
    parts = text.strip().split()
    if len(parts) != 4:
        raise ValueError(
            "Please send exactly 4 values:\n"
            "`TICKER AMOUNT_PER_ORDER INTERVAL SPLIT_COUNT`"
        )
    ticker, amt_str, interval_str, count_str = parts

    # parse amount
    try:
        amount = float(amt_str)
    except ValueError:
        raise ValueError(f"`AMOUNT_PER_ORDER` must be a number, got '{amt_str}'")

    # parse interval
    interval = parse_duration_to_seconds(interval_str)

    # parse split count
    try:
        split_count = int(count_str)
    except ValueError:
        raise ValueError(f"`SPLIT_COUNT` must be an integer, got '{count_str}'")
    if split_count < 2:
        raise ValueError("`SPLIT_COUNT` must be at least 2")

    return (ticker, amount, interval, split_count)


# ====================

dca_timeslice_spot_states = {
    DcaTimeSliceSpotStates.TYPING: [MessageHandler(filters.TEXT, dca_parsing)],
    DcaTimeSliceSpotStates.CONFIRM: [
        CallbackQueryHandler(
            dca_confirm, pattern=f"^{DcaTimeSliceSpotStates.CONFIRM.value}$"
        )
    ],
}
