from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes
from handler.models.perp_balance import PerpBalanceMapping
from .settings import CloseSetting
from .utils import (
    separate_position,
    generate_summary,
)
from .states import *
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from handler.command import Command
from handler.utils.cancel import create_cancel_inline_button
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from handler.utils.decorators import (
    require_builder_fee_approved,
)
from handler.utils.utils import answer, send_or_edit


from typing import List

logger = configure_logging(__name__)


@require_builder_fee_approved
@force_coroutine_logging
async def close_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    /매도 명령어 시작:
    1. 전체 매도
    2. 종목 선택 매도 (다중 선택 가능, 페이지네이션)
    """
    await answer(update)
    CloseSetting.clear_setting(context)
    close_setting: CloseSetting = CloseSetting.get_setting(context)

    # IMPORTANT 잔액 다시 가져오기
    account_hodler: AccountManager = await fetch_account_manager(context)
    await account_hodler.refresh_perp_balance(force=True)

    # balance 가져와서 및 설정값 저장
    perp_balance_mapping: PerpBalanceMapping = (
        await account_hodler.get_perp_balance_mapping()
    )

    sellable, unsellable = separate_position(perp_balance_mapping.position)
    close_setting.sellable_balance = sellable
    close_setting.unsellable_balance = unsellable

    # display
    message = "Here is an overview of your account. For detailed PNL by asset, please refer to /balance. \n\n"
    message += generate_summary(perp_balance_mapping)
    message += """
Please choose how you'd like to proceed with your assets.

1️⃣ Close All: Quickly sell all your assets at once.
2️⃣ Close One: Select individual asset to sell.

⚠️ Only assets priced above $15 are eligible for sale.
        """

    keyboard = [
        [InlineKeyboardButton("1️⃣ Close All", callback_data=CloseAllStates.START.value)],
        [
            InlineKeyboardButton(
                "2️⃣ Close One",
                callback_data=CloseOneStates.START.value,
            )
        ],
        [create_cancel_inline_button(Command.HYPERLIQUID_CORE_START)],
    ]

    await send_or_edit(
        update,
        context,
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return CloseStates.CLOSE
