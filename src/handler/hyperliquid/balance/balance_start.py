from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes
from api import AccountService
from .settings import BalanceSetting
from .utils import generate_summary
from .states import *
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from handler.utils.cancel import create_cancel_inline_button
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from handler.utils.decorators import require_builder_fee_approved
from handler.utils.utils import answer, send_or_edit
from handler.command import Command

logger = configure_logging(__name__)


accountService = AccountService()


# ================================
# 시작 - 원하는 전략의 카테고리를 선택함.
# ================================
@require_builder_fee_approved
@force_coroutine_logging
async def balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    balance_setting: BalanceSetting = BalanceSetting.get_setting(context)
    await answer(update)

    # IMPORTANT 잔액 다시 가져오기
    account_hodler: AccountManager = await fetch_account_manager(context)
    spot_balance_mapping, perp_balance_mapping = await account_hodler.refresh_all(
        force=True
    )

    reply_text = generate_summary(spot_balance_mapping, perp_balance_mapping)

    keyboard = [
        [
            InlineKeyboardButton(
                "Perp to Spot", callback_data=PerpToSpotStates.START.value
            ),
            InlineKeyboardButton(
                "Spot to Perp", callback_data=SpotToPerpStates.START.value
            ),
        ],
        [
            InlineKeyboardButton(
                "Spot Detail", callback_data=SpotDetailStates.START.value
            ),
            InlineKeyboardButton(
                "Perp Detail", callback_data=PerpDetailStates.START.value
            ),
        ],
        [
            InlineKeyboardButton(
                "Send USDC",
                callback_data=f"{SendUsdcStates.START.value}|{Command.BALANCE}",
            ),
            InlineKeyboardButton("Refresh", callback_data=RefreshStates.START.value),
        ],
        [create_cancel_inline_button(balance_setting.return_to)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_or_edit(
        update,
        context,
        text=reply_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )
    return BalanceStates.SELECT_ACTION
