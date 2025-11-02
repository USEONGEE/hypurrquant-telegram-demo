from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes, ConversationHandler
from hypurrquant.evm import Chain
from api import AccountService, LpVaultService
from .settings import EvmBalanceSetting
from .states import *
from .pagination import EvmBalancePagination
from hypurrquant.models.account import Account
from handler.command import Command
from handler.utils.account_helpers import fetch_active_account
from handler.utils.cancel import create_cancel_inline_button, initialize_handler
from handler.evm.lpvault.states import LpvaultSwapState
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from handler.utils.utils import answer, send_or_edit

from typing import List

logger = configure_logging(__name__)


account_service = AccountService()
lpvault_service = LpVaultService()

CHAIN = Chain.HYPERLIQUID

CALLBACK_PREFIX = "EVM_BALANCE"


# ================================
# 시작 - 원하는 전략의 카테고리를 선택함.
# ================================
@force_coroutine_logging
@initialize_handler(setting_cls=EvmBalanceSetting)
async def balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)

    balance_setting: EvmBalanceSetting = EvmBalanceSetting.get_setting(context)
    account: Account = await fetch_active_account(context)
    addresses = await account_service.get_evm_managed_token(CHAIN)
    balance_dto = await account_service.get_evm_balance_for_ui(
        account.public_key, addresses
    )
    balance_setting.pagination = EvmBalancePagination(balance_dto, CHAIN)
    await show_current_page(update, context)
    return EvmBalanceState.SELECT_ACTION


@force_coroutine_logging
async def show_current_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    현재 페이지의 종목 목록(문구) + 버튼(이전, 다음, 토글, 확인)을 전송
    """

    balance_setting: EvmBalanceSetting = EvmBalanceSetting.get_setting(context)

    keyboard = [
        [
            InlineKeyboardButton("Send", callback_data=SendState.START.value),
            InlineKeyboardButton(
                "Swap",
                callback_data=f"{LpvaultSwapState.START.value}?rt={Command.EVM_BALANCE}",
            ),
        ],
    ]

    message = balance_setting.pagination.generate_info_text()
    buttons: List[InlineKeyboardButton] = balance_setting.pagination.generate_buttons(
        CALLBACK_PREFIX
    )
    buttons.append(create_cancel_inline_button(balance_setting.return_to))
    keyboard.append(buttons)

    await send_or_edit(
        update,
        context,
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )
    return EvmBalanceState.SELECT_ACTION


@force_coroutine_logging
async def page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")

    await answer(update)
    data = update.callback_query.data  # ex) "STOCKS_TOGGLE_AAPL" or "STOCKS_PREV" etc.

    pagination = EvmBalanceSetting.get_setting(context).pagination

    if data == f"{CALLBACK_PREFIX}_NEXT":
        pagination.go_to_next_page()
        await show_current_page(update, context)
        return EvmBalanceState.SELECT_ACTION

    elif data == f"{CALLBACK_PREFIX}_PREV":
        pagination.go_to_prev_page()
        await show_current_page(update, context)
        return EvmBalanceState.SELECT_ACTION

    else:
        await send_or_edit(update, context, "Invalid callback data")
        return ConversationHandler.END
