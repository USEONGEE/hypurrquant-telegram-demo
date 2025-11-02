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
from api.hyperliquid import DcaService
from hypurrquant.models.account import Account
from handler.utils.account_helpers import fetch_active_account
from handler.utils.utils import answer, send_or_edit
from handler.utils.cancel import create_cancel_inline_button
from handler.command import Command
from .states import *
from .utils import format_dca_spot_list
from .settings import DcaSetting

logger = configure_logging(__name__)

account_service = AccountService()
dca_service = DcaService()


@force_coroutine_logging
async def dca_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    logger.info("DCA command triggered by user: %s", update.effective_user.id)
    await answer(update)
    DcaSetting.clear_setting(context)
    dca_setting = DcaSetting.get_setting(context)
    account: Account = await fetch_active_account(context)
    dca_spot_list = await dca_service.get_timeslice_spot_list(account.public_key)
    dca_setting.dca_spot_list = dca_spot_list

    message = "*DCA (Dollar-Cost Averaging)*\nAutomate periodic buys and sells to smooth your average entry price over time.\n\n"

    message += format_dca_spot_list(dca_spot_list)

    keyboard = [
        [
            InlineKeyboardButton(
                "⬆️ Spot Buy DCA",
                callback_data=f"{DcaTimeSliceSpotStates.START.value}|buy",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬇️ Spot Sell DCA",
                callback_data=f"{DcaTimeSliceSpotStates.START.value}|sell",
            ),
        ],
        [
            InlineKeyboardButton(
                "🗑️ Delete DCA Order",
                callback_data=f"{DcaDeleteStates.START.value}",
            ),
        ],
        [create_cancel_inline_button(Command.HYPERLIQUID_CORE_START)],
    ]

    await send_or_edit(
        update,
        context,
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )
    return DcaStates.SELECT_ACTION
