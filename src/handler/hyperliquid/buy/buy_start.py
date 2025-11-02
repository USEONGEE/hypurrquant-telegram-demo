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
from api.hyperliquid import BuyOrderService, MarketDataCache
from .settings import BuySetting
from .states import (
    StrategyStates,
    MarketStrategyState,
)
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.cancel import create_cancel_inline_button
from handler.command import Command
from handler.utils.account_manager import AccountManager
from handler.utils.decorators import require_builder_fee_approved
from handler.utils.utils import answer, send_or_edit

logger = configure_logging(__name__)

MINIMUM_AMOUNT = 20  # 최소 매수 금액

fetcher = MarketDataCache()
accountService = AccountService()
buyOrderService = BuyOrderService()


# ================================
# 시작 - 원하는 전략의 카테고리를 선택함.
# ================================
@require_builder_fee_approved
@force_coroutine_logging
async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    buy_setting: BuySetting = BuySetting.get_setting(context)

    # IMPORTANT 잔액 다시 가져오기
    account_hodler: AccountManager = await fetch_account_manager(context)
    # account_hodler: AccountManager = await fetch_account_manager(context)
    await account_hodler.refresh_spot_balance()

    reply_text = (
        "Welcome! Let's select the type of strategy you'd like to execute.\n\n"
        "```\n"
        "1️⃣ Uptrend: Ideal for identifying rising market trends.\n\n"
        "2️⃣ Sideways: Suitable for stable or range-bound markets.\n\n"
        "3️⃣ Downtrend: Perfect for navigating declining market trends.\n\n"
        "```"
        "Please pick one of the strategies above by clicking the corresponding button."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📈 Uptrend", callback_data=MarketStrategyState.UPTREND.value
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 Sideways", callback_data=MarketStrategyState.SIDEWAYS.value
            ),
        ],
        [
            InlineKeyboardButton(
                "📉 Downtrend", callback_data=MarketStrategyState.DOWNTREND.value
            ),
        ],
        [create_cancel_inline_button(Command.BUY)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit(
        update,
        context,
        text=reply_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return StrategyStates.START
