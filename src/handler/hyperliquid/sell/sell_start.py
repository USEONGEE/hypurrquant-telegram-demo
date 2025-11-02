from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
)
from .settings import SellSetting
from .utils import separate_spot_balance
from .states import *
from .utils import generate_summary
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from handler.command import Command
from handler.models.spot_balance import (
    SpotBalance,
    SpotBalanceMapping,
)
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager

from handler.utils.decorators import require_builder_fee_approved
from handler.utils.utils import answer, send_or_edit
from handler.utils.cancel import create_cancel_inline_button

from typing import List

logger = configure_logging(__name__)


@require_builder_fee_approved
@force_coroutine_logging
async def sell_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    /매도 명령어 시작:
    1. 전체 매도
    2. 종목 선택 매도 (다중 선택 가능, 페이지네이션)
    """
    await answer(update)
    logger.debug("sell command 시작")
    SellSetting.clear_setting(context)
    sell_setting: SellSetting = SellSetting.get_setting(context)

    # IMPORTANT 잔액 다시 가져오기
    account_hodler: AccountManager = await fetch_account_manager(context)
    await account_hodler.refresh_spot_balance(force=True)

    # balance 가져와서 및 설정값 저장
    spot_balance_mapping: SpotBalanceMapping = (
        await account_hodler.get_spot_balance_mapping()
    )
    portfolio: List[SpotBalance] = list(spot_balance_mapping.balances.values())

    sellable, unsellable = separate_spot_balance(portfolio)
    sell_setting.sellable_balance = sellable
    sell_setting.unsellable_balance = unsellable

    # display
    message = "Here is an overview of your account. For detailed PNL by asset, please refer to /balance. \n\n"
    message += generate_summary(spot_balance_mapping)
    message += """
Please choose how you'd like to proceed with your assets.

1️⃣ Sell All: Quickly sell all your assets at once.
2️⃣ Select Stock: Pick specific stocks to sell.

⚠️ Only assets priced above $15 are eligible for sale.
        """

    keyboard = [
        [InlineKeyboardButton("1️⃣ Sell All", callback_data=AllStates.START.value)],
        [
            InlineKeyboardButton(
                "2️⃣ Select Stock",
                callback_data=SpecificStates.START.value,
            )
        ],
        [create_cancel_inline_button(sell_setting.return_to)],
    ]
    await send_or_edit(
        update,
        context,
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return SellStates.SELL
