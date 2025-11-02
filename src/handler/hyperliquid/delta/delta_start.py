from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from hypurrquant.utils.paired_symbols import symbol_table, MarketType
from api.hyperliquid import DeltaOrderService, HLAccountService
from .pagination import DeltaSymbolPagination
from .states import *
from .settings import *
from handler.utils.utils import answer, send_or_edit
from handler.utils.cancel import create_cancel_inline_button
from handler.command import Command
from handler.utils.account_helpers import (
    fetch_active_account,
    fetch_account_manager,
)
from handler.utils.account_manager import AccountManager
from handler.command import Command
from hypurrquant.models.account import Account
from handler.utils.decorators import (
    require_builder_fee_approved,
)
import asyncio

logger = configure_logging(__name__)

hl_account_service = HLAccountService()
delta_order_service = DeltaOrderService()


@require_builder_fee_approved
@force_coroutine_logging
async def delta_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    logger.info("delta command triggered by user: %s", update.effective_user.id)
    await answer(update)
    DeltaSetting.clear_setting(context)
    # 1. 데이터 패치
    setting: DeltaSetting = DeltaSetting.get_setting(context)
    account: Account = await fetch_active_account(context)
    account_hodler: AccountManager = await fetch_account_manager(context)

    # 2. 잔액 조회
    response, (spot_balance_mapping, perp_balance_mapping) = await asyncio.gather(
        hl_account_service.get_usdc_balance_by_nickname(
            context._user_id, account.nickname
        ),
        account_hodler.refresh_all(force=True),
    )

    # 3. 페이지네이션 설정
    setting.total_usdc = response["spot_usdc"] + response["withdrawable"]
    paired = [
        (
            key,
            spot_balance_mapping.balances[cfg.internal[MarketType.SPOT]],
            perp_balance_mapping.position.oneWay[cfg.internal[MarketType.PERP]],
        )
        for key, cfg in symbol_table.items()
        if cfg.internal[MarketType.SPOT] in spot_balance_mapping.balances
        and spot_balance_mapping.balances[cfg.internal[MarketType.SPOT]].Value > 10
        and cfg.internal[MarketType.PERP] in perp_balance_mapping.position.oneWay
        and perp_balance_mapping.position.oneWay[
            cfg.internal[MarketType.PERP]
        ].positionValue
        + perp_balance_mapping.position.oneWay[
            cfg.internal[MarketType.PERP]
        ].unrealizedPnl
        > 10
    ]

    setting: DeltaSetting = DeltaSetting.get_setting(context)
    setting.pagination = DeltaSymbolPagination(setting.total_usdc)
    setting.close_pagination = DeltaClosePagination(setting.total_usdc, paired)

    return await show_current_page(update, context)


# =============== #
# 2) 페이지 보여주기 #
# =============== #
@force_coroutine_logging
async def show_current_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    현재 페이지의 종목 목록(문구) + 버튼(이전, 다음, 토글, 확인)을 전송
    """
    select_setting: DeltaSetting = DeltaSetting.get_setting(context)
    pagination: DeltaSymbolPagination = select_setting.pagination

    info_text = await pagination.generate_info_text()
    if len(select_setting.close_pagination.data) > 0:
        close_info_text = await select_setting.close_pagination.generate_info_text()
        info_text += close_info_text
    kb = [
        [
            InlineKeyboardButton(
                "Create ",
                callback_data=DeltaOpenState.START.value,
            ),
            InlineKeyboardButton(
                "Close",
                callback_data=DeltaCloseState.START.value,
            ),
        ],
        [create_cancel_inline_button(Command.HYPERLIQUID_CORE_START)],
    ]

    await send_or_edit(
        update,
        context,
        text=info_text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return DeltaState.SELECT_ACTION
