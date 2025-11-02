from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from hypurrquant.evm import Chain
from api import AccountService, LpVaultService, DexInforesponse, LpVaultSettingsService
from api.exception import AccountTypeNotFoundException
from handler.utils.utils import answer, send_or_edit, format_buttons_grid
from handler.utils.account_helpers import fetch_active_account
from .cancel import cancel_keyboard_button
from .settings import LpvaultManualMintSetting, LpvaultSetting
from .states import *
from .lpvault_start import lpvault_command
from .utils import create_register_confirm_message
from handler.utils.utils import format_buttons_grid
from tabulate import tabulate
from typing import List
import asyncio

logger = configure_logging(__name__)

account_service = AccountService()
lpvault_service = LpVaultService()
lpvault_settings_service = LpVaultSettingsService()

CHAIN = Chain.HYPERLIQUID

AUTO_AGGREGATOR = "Best Route"


@force_coroutine_logging
async def lpvault_manual_mint_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    LpvaultManualMintSetting.clear_setting(context)
    mint_setting: LpvaultManualMintSetting = LpvaultManualMintSetting.get_setting(
        context
    )
    account = await fetch_active_account(context)
    dex_list, settings = await asyncio.gather(
        lpvault_service.dex_list(CHAIN),
        lpvault_settings_service.get_settings(
            public_key=account.public_key, chain=CHAIN
        ),
    )
    mint_setting.lpvault_settings = settings
    mint_setting._all_dex_infos = dex_list
    logger.debug(f"dex_list: {dex_list}")

    kb = []
    for dex in dex_list:
        kb.append(
            InlineKeyboardButton(
                dex["name"],
                callback_data=LpvaultManualMintState.SELECT_DEX.value
                + f"_{dex['name']}",
            )
        )

    kb = format_buttons_grid(kb, columns=2)

    kb.append(
        [InlineKeyboardButton("Cancel", callback_data="lpvault_cancel")],
    )
    await send_or_edit(
        update,
        context,
        "Please select a DEX to register your LP.",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return LpvaultManualMintState.SELECT_DEX


@force_coroutine_logging
async def lpvault_manual_mint_select_dex(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(
        "lpvault_register_select_dex triggered by user: %s", update.effective_user.id
    )
    await answer(update)

    # 1. 사용자가 선택한 dex info 추출
    dex_type = update.callback_query.data.split("_")[-1]
    mint_setting: LpvaultManualMintSetting = LpvaultManualMintSetting.get_setting(
        context
    )

    for info in mint_setting._all_dex_infos:
        logger.debug(f"dex_info: {info}")
        if info["name"] == dex_type:
            mint_setting.dex_info = info
            break
    else:
        raise ValueError(f"Unsupported dex: {dex_type}")

    logger.debug(f"Selected dex_type: {mint_setting.dex_info}")

    pool_config_list = await lpvault_service.pool_list(
        CHAIN, mint_setting.dex_info["name"]
    )
    mint_setting.all_pool_configs = pool_config_list
    logger.debug(f"pool_list for {dex_type}: {pool_config_list}")

    tmp = []
    for i, config in enumerate(pool_config_list):
        tmp.append(
            InlineKeyboardButton(
                config["pool_name"],
                callback_data=LpvaultManualMintState.SELECT_POOL.value + f"_{i}",
            )
        )
    columns = 2
    kb = format_buttons_grid(tmp, columns=columns)

    kb.append([InlineKeyboardButton("Cancel", callback_data="lpvault_cancel")])

    text = f"Please select a pool in the DEX: {dex_type}\n\n"

    for i, pool_config in enumerate(pool_config_list):
        text += f"{i + 1}. *{pool_config['pool_name']}* (fee: {(pool_config['fee'] or 0 )/ 10000} %)\n"

    await send_or_edit(
        update,
        context,
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return LpvaultManualMintState.SELECT_POOL


@force_coroutine_logging
async def lpvault_manual_mint_select_pool(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(
        "lpvault_register_select_pool triggered by user: %s", update.effective_user.id
    )
    await answer(update)

    pool_index = int(update.callback_query.data.split("_")[-1])
    pool_config_list = await lpvault_service.pool_list(
        CHAIN, LpvaultManualMintSetting.get_setting(context).dex_info["name"]
    )

    if pool_index < 0 or pool_index >= len(pool_config_list):
        await send_or_edit(
            update,
            context,
            "Invalid pool selection. Please try again.",
            parse_mode="Markdown",
        )
        return LpvaultManualMintState.SELECT_POOL

    LpvaultManualMintSetting.get_setting(context).config_index = pool_index

    text = f"You have selected the pool: {pool_config_list[pool_index]['pool_name']}({pool_config_list[pool_index]['dex_type']})\n\n"
    text += (
        "Please set the range percentage for the LP Vault. \n\nThere are three options.\n"
        "- Tap a preset button (e.g., ±1%, ±5%).\n"
        "- Enter a single number (e.g., `5`) → ±5% range.\n"
        "- Enter two numbers with a space (e.g., `-5 3`) → -5% ~ 3% \n"
        "Note: If the value is too low, minting may be restricted."
    )

    pcts = pool_config_list[pool_index]["pcts"]

    kb = []
    for pct in pcts:
        kb.append(
            InlineKeyboardButton(
                f"±{pct}%",
                callback_data=f"{LpvaultManualMintState.RANGE_PERCENTAGE.value}_{pct}",
            )
        )

    kb = format_buttons_grid(kb, columns=3)

    kb.append(cancel_keyboard_button)

    await send_or_edit(
        update,
        context,
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return LpvaultManualMintState.RANGE_PERCENTAGE


@force_coroutine_logging
async def lpvault_manual_mint_range_percentage(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(
        "lpvault_register_confirm triggered by user: %s", update.effective_user.id
    )
    await answer(update)
    setting: LpvaultManualMintSetting = LpvaultManualMintSetting.get_setting(context)

    if update.message:
        range_percentage = update.message.text
        # 1. custom range를 작성한 경우
        if " " in update.message.text:
            try:
                lower, upper = map(float, update.message.text.split())
                if lower >= upper:
                    raise ValueError("Lower range must be less than upper range.")
            except Exception as e:
                await send_or_edit(
                    update,
                    context,
                    f"Invalid input. Please enter two positive numbers separated by a space.",
                    parse_mode="Markdown",
                )
                return ConversationHandler.END
            setting: LpvaultManualMintSetting = LpvaultManualMintSetting.get_setting(
                context
            )
            setting.upper_range_pct = upper
            setting.lower_range_pct = lower

        # 2. 단일 숫자를 작성한 경우
        else:
            try:
                range_percentage = abs(float(update.message.text))
                setting.upper_range_pct = range_percentage
                setting.lower_range_pct = -range_percentage
            except ValueError as e:
                raise ValueError("Invalid range percentage. Must be a number.")
    # 3. 버튼을 클릭한 경우
    elif update.callback_query:
        try:
            range_percentage = abs(float(update.callback_query.data.split("_")[-1]))
            setting.upper_range_pct = range_percentage
            setting.lower_range_pct = -range_percentage
        except ValueError as e:
            raise ValueError("Invalid range percentage. Must be a number.")

    # 4. 그 외의 경우
    else:
        await send_or_edit(
            update,
            context,
            "Invalid input. Please try again. /start",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    # 5. 다음 단계로 이동
    mint_setting: LpvaultManualMintSetting = LpvaultManualMintSetting.get_setting(
        context
    )
    lpvault_setting = mint_setting.lpvault_settings
    msg = (
        "You have the following settings: \n"
        f"```{tabulate(
            [
                ["Aggregator", lpvault_setting["aggregator"]],
                ["Auto Claim", "Enabled" if lpvault_setting["auto_claim"] else "Disabled"],
            ],
            tablefmt="grid",
        )}```\n"
        "Do you want to proceed with these settings?\n\n"
    )

    kb = [
        [
            InlineKeyboardButton(
                "Yes",
                callback_data=f"{LpvaultManualMintState.USE_EXISTING_SETTINGS.value}_Yes",
            )
        ],
        [
            InlineKeyboardButton(
                "No",
                callback_data=f"{LpvaultManualMintState.USE_EXISTING_SETTINGS.value}_No",
            )
        ],
        [InlineKeyboardButton("Cancel", callback_data=setting.return_to)],
    ]

    await send_or_edit(
        update,
        context,
        msg,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )

    return LpvaultManualMintState.USE_EXISTING_SETTINGS


async def lpvault_use_settings_from_existing(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(
        "lpvault_use_settings_from_existing triggered by user: %s",
        update.effective_user.id,
    )
    await answer(update)

    choice = update.callback_query.data.split("_")[-1]
    # 1. 기존 설정을 사용하는 경우
    if choice == "Yes":
        mint_setting: LpvaultManualMintSetting = LpvaultManualMintSetting.get_setting(
            context
        )
        mint_setting.aggregator = mint_setting.lpvault_settings["aggregator"]
        mint_setting.auto_claim = mint_setting.lpvault_settings["auto_claim"]

        message = create_register_confirm_message(mint_setting)

        kb = [
            [
                InlineKeyboardButton(
                    "Confirm", callback_data=LpvaultManualMintState.CONFIRM.value
                )
            ],
            [InlineKeyboardButton("Cancel", callback_data="lpvault_cancel")],
        ]

        await send_or_edit(
            update,
            context,
            message,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown",
        )
        return LpvaultManualMintState.CONFIRM

    # 2. 새로운 설정을 선택하는 경우
    else:
        agg_list: list = await lpvault_service.aggregator_list(CHAIN)

        if len(agg_list) > 1:
            agg_list = [AUTO_AGGREGATOR] + agg_list

        kb = [
            [
                InlineKeyboardButton(
                    agg,
                    callback_data=f"{LpvaultManualMintState.SELECT_AGGREGATOR.value}_{agg}",
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
        return LpvaultManualMintState.SELECT_AGGREGATOR


@force_coroutine_logging
async def lpvault_manual_mint_aggregator(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)

    agg = update.callback_query.data.split("_")[-1]

    mint_setting = LpvaultManualMintSetting.get_setting(context)
    mint_setting.aggregator = agg

    kb = [
        [
            InlineKeyboardButton(
                "Confirm", callback_data=LpvaultManualMintState.CONFIRM.value
            )
        ],
        [InlineKeyboardButton("Cancel", callback_data="lpvault_cancel")],
    ]
    message = create_register_confirm_message(mint_setting)

    await send_or_edit(
        update,
        context,
        message,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return LpvaultManualMintState.CONFIRM


@force_coroutine_logging
async def lpvault_manual_mint_confirm(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    setting: LpvaultSetting = LpvaultSetting.get_setting(context)
    mint_setting: LpvaultManualMintSetting = LpvaultManualMintSetting.get_setting(
        context
    )

    logger.debug(f"{mint_setting.dex_info['name']=}")
    dex_type = mint_setting.dex_info["name"]
    config_index = mint_setting.config_index
    pool_config = mint_setting.all_pool_configs[config_index]
    try:
        await send_or_edit(
            update,
            context,
            "Registering LP vault... This may take a while. Please wait...",
            parse_mode="Markdown",
        )
        response = await lpvault_service.manual_mint(
            public_key=setting.account.public_key,
            chain=CHAIN,
            dex_type=dex_type,
            token0=pool_config["token0"],
            token1=pool_config["token1"],
            fee=pool_config["fee"],
            upper_range_pct=mint_setting.upper_range_pct,
            lower_range_pct=mint_setting.lower_range_pct,
            aggregator=mint_setting.aggregator,
        )
        if response.get("is_minted", None):
            await send_or_edit(
                update,
                context,
                "Manual minting completed successfully.",
                parse_mode="Markdown",
            )
        else:
            await send_or_edit(
                update,
                context,
                f"Manual minting failed.",
                parse_mode="Markdown",
            )
    except AccountTypeNotFoundException as e:
        await send_or_edit(
            update,
            context,
            f"Something went wrong. Try again later.",
            parse_mode="Markdown",
        )

    await asyncio.sleep(1)

    return await lpvault_command(update, context)


manual_mint_states = {
    LpvaultManualMintState.SELECT_DEX: [
        CallbackQueryHandler(
            lpvault_manual_mint_select_dex,
            pattern=f"^{LpvaultManualMintState.SELECT_DEX.value}_",
        ),
    ],
    LpvaultManualMintState.SELECT_POOL: [
        CallbackQueryHandler(
            lpvault_manual_mint_select_pool,
            pattern=f"^{LpvaultManualMintState.SELECT_POOL.value}_",
        ),
    ],
    LpvaultManualMintState.RANGE_PERCENTAGE: [
        MessageHandler(
            filters.TEXT & ~filters.COMMAND, lpvault_manual_mint_range_percentage
        ),
        CallbackQueryHandler(
            lpvault_manual_mint_range_percentage,
            pattern=f"^{LpvaultManualMintState.RANGE_PERCENTAGE.value}_",
        ),
    ],
    LpvaultManualMintState.USE_EXISTING_SETTINGS: [
        CallbackQueryHandler(
            lpvault_use_settings_from_existing,
            pattern=f"^{LpvaultManualMintState.USE_EXISTING_SETTINGS.value}_",
        ),
    ],
    LpvaultManualMintState.SELECT_AGGREGATOR: [
        CallbackQueryHandler(
            lpvault_manual_mint_aggregator,
            pattern=f"^{LpvaultManualMintState.SELECT_AGGREGATOR.value}_",
        ),
    ],
    LpvaultManualMintState.CONFIRM: [
        CallbackQueryHandler(
            lpvault_manual_mint_confirm,
            pattern=f"^{LpvaultManualMintState.CONFIRM.value}$",
        ),
    ],
}
