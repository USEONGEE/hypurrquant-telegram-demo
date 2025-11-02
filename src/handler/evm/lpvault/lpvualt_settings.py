from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api import (
    AccountService,
    LpVaultSettingsService,
    LpvaultSettingsDict,
    LpVaultService,
)
from handler.utils.utils import answer, send_or_edit
from handler.utils.account_helpers import fetch_active_account
from handler.utils.cancel import initialize_handler, create_cancel_inline_button
from handler.wallet.states import ChangeState
from handler.evm.balance.states import EvmBalanceState
from handler.command import Command
from .settings import LpvaultSettingsSetting
from .states import *
from .utils import build_pair_table
from tabulate import tabulate
from typing import List, Dict, Any
import asyncio
from tabulate import tabulate

logger = configure_logging(__name__)

account_service = AccountService()
lpvault_settings_service = LpVaultSettingsService()
lpvault_service = LpVaultService()

CHAIN = "HYPERLIQUID"  # TODO 추후엔 LpVaultSetting으로 넘어가야함.

AUTO_AGGREGATOR = "Best Route"


@force_coroutine_logging
@initialize_handler(setting_cls=LpvaultSettingsSetting)
async def lpvault_settings_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    account = await fetch_active_account(context)

    # 1. 현재 셋팅값 가져오기, 보여주기
    setting: LpvaultSettingsDict = await lpvault_settings_service.get_settings(
        account.public_key, CHAIN
    )
    lpvault_settings: LpvaultSettingsSetting = LpvaultSettingsSetting.get_setting(
        context
    )
    lpvault_settings.setting = setting

    msg = (
        f"*Lpvault Settings Menu*\({CHAIN}\)\n"
        f"👤 *{account.nickname}* \| `{account.public_key}`\n\n"
        "**> *Fields Info*\n"
        "> \n"
        ">_*Aggregator*_\n"
        ">Aggregator used for the LP vault\n"
        "> \n"
        ">_*Auto Claim*_\n"
        ">Whether to automatically claim farming rewards||\n\n"
    )
    msg += "```"
    msg += tabulate(
        [
            ["Aggregator", setting["aggregator"]],
            ["Auto Claim", "Enabled" if setting["auto_claim"] else "Disabled"],
        ],
        tablefmt="grid",
    )
    msg += "```"

    # 2. 각 세팅값을 변경하는 button 생성하기
    btns = [
        [
            InlineKeyboardButton(
                f"Change Aggregator",
                callback_data=f"{LpvaultSettingsState.SELECT_AGGREGATOR.value}",
            ),
        ],
        [
            InlineKeyboardButton(
                f"Auto Claim: {'ON' if not setting['auto_claim'] else 'OFF'}",
                callback_data=f"{LpvaultSettingsState.AUTO_CLAIM.value}",
            ),
        ],
        [create_cancel_inline_button(lpvault_settings.return_to)],
    ]

    await send_or_edit(
        update,
        context,
        msg,
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode="MarkdownV2",
    )
    return LpvaultSettingsState.SELECT_ACTION


async def lpvault_settings_select_aggregator(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await answer(update)

    agg_list: list = await lpvault_service.aggregator_list(CHAIN)

    if len(agg_list) > 1:
        agg_list = [AUTO_AGGREGATOR] + agg_list

    kb = [
        [
            InlineKeyboardButton(
                agg,
                callback_data=f"{LpvaultSettingsState.SELECT_AGGREGATOR.value}|{agg}",
            )
        ]
        for agg in agg_list
    ]
    kb.append([InlineKeyboardButton("Cancel", callback_data="lpvault_cancel")])

    await send_or_edit(
        update,
        context,
        (
            "Select the DEX Aggregator to use for position rebalancing.\n"
            "Slippage and price impact are limited to 1%.\n\n"
            "👉 Best Route: automatically finds the most optimal option across all aggregators."
        ),
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return LpvaultSettingsState.SELECT_AGGREGATOR


async def lpvualt_settings_confirm_aggregator(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await answer(update)
    agg = update.callback_query.data.split("|")[-1]
    if agg == AUTO_AGGREGATOR:
        agg = "__auto__"

    account = await fetch_active_account(context)

    await lpvault_settings_service.change_aggregator(
        public_key=account.public_key, chain=CHAIN, aggregator=agg
    )

    return await lpvault_settings_start(update, context)


async def change_auto_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await answer(update)
    await send_or_edit(update, context, "update settings...")
    callback_data = update.callback_query.data
    lpvault_settings: LpvaultSettingsSetting = LpvaultSettingsSetting.get_setting(
        context
    )
    if callback_data == LpvaultSettingsState.AUTO_CLAIM.value:
        value = {"auto_claim": not lpvault_settings.setting["auto_claim"]}
    else:
        await answer(update, "Unknown toggle field.")
        return
    account = await fetch_active_account(context)

    await lpvault_settings_service.update_auto_toggle(account.public_key, CHAIN, value)
    return await lpvault_settings_start(update, context)


settings_states = {
    LpvaultSettingsState.SELECT_ACTION: [
        CallbackQueryHandler(
            lpvault_settings_select_aggregator,
            pattern=f"^{LpvaultSettingsState.SELECT_AGGREGATOR.value}",
        ),
        CallbackQueryHandler(
            change_auto_toggle,
            pattern=rf"^{LpvaultSettingsState.AUTO_FARM.value}$|^{LpvaultSettingsState.AUTO_SWAP.value}$|^{LpvaultSettingsState.AUTO_CLAIM.value}$",
        ),
    ],
    LpvaultSettingsState.SELECT_AGGREGATOR: [
        CallbackQueryHandler(
            lpvualt_settings_confirm_aggregator,
            pattern=f"^{LpvaultSettingsState.SELECT_AGGREGATOR.value}",
        ),
    ],
}
