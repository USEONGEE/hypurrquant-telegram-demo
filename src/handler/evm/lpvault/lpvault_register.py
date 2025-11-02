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
from api import AccountService, LpVaultService, LpVaultSettingsService
from api.exception import AccountTypeNotFoundException
from handler.utils.utils import answer, send_or_edit, format_buttons_grid
from handler.utils.account_helpers import fetch_active_account
from .cancel import cancel_keyboard_button
from .settings import LpvaultRegisterSetting, LpvaultSetting
from .states import *
from .lpvault_start import lpvault_command
from .utils import create_register_confirm_message
from tabulate import tabulate
import asyncio

logger = configure_logging(__name__)

account_service = AccountService()
lpvault_service = LpVaultService()
lpvault_settings_service = LpVaultSettingsService()

CHAIN = Chain.HYPERLIQUID

AUTO_AGGREGATOR = "Best Route"


@force_coroutine_logging
async def lpvault_register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    LpvaultRegisterSetting.clear_setting(context)
    register_setting: LpvaultRegisterSetting = LpvaultRegisterSetting.get_setting(
        context
    )
    account = await fetch_active_account(context)
    dex_list, settings = await asyncio.gather(
        lpvault_service.dex_list(CHAIN),
        lpvault_settings_service.get_settings(
            public_key=account.public_key, chain=CHAIN
        ),
    )
    register_setting.lpvault_settings = settings
    register_setting._all_dex_infos = dex_list
    logger.debug(f"dex_list: {dex_list}")

    kb = []
    for i, dex in enumerate(dex_list):
        kb.append(
            InlineKeyboardButton(
                dex["name"],
                callback_data=f"{LpvaultRegisterState.SELECT_DEX.value}_{i}",
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
    return LpvaultRegisterState.SELECT_DEX


@force_coroutine_logging
async def lpvault_register_select_dex(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(
        "lpvault_register_select_dex triggered by user: %s", update.effective_user.id
    )
    await answer(update)

    # 1. 사용자가 선택한 dex info 추출
    register_setting = LpvaultRegisterSetting.get_setting(context)
    dex_index = int(
        update.callback_query.data[len(LpvaultRegisterState.SELECT_DEX.value) + 1 :]
    )
    register_setting.dex_info = register_setting._all_dex_infos[dex_index]

    logger.debug(f"Selected dex_type: {register_setting.dex_info}")

    pool_config_list = await lpvault_service.pool_list(
        CHAIN, register_setting.dex_info["name"]
    )
    register_setting.all_pool_configs = pool_config_list
    logger.debug(
        f"pool_list for {register_setting.dex_info['name']}: {pool_config_list}"
    )

    tmp = []
    for i, config in enumerate(pool_config_list):
        tmp.append(
            InlineKeyboardButton(
                config["pool_name"],
                callback_data=LpvaultRegisterState.SELECT_POOL.value + f"_{i}",
            )
        )
    columns = 2
    kb = format_buttons_grid(tmp, columns=columns)

    kb.append([InlineKeyboardButton("Cancel", callback_data="lpvault_cancel")])

    text = f"Please select a pool in the DEX: {register_setting.dex_info['name']}\n\n"

    for i, pool_config in enumerate(pool_config_list):
        text += f"{i + 1}. *{pool_config['pool_name']}* (fee: {(pool_config['fee'] or 0 )/ 10000} %)\n"

    await send_or_edit(
        update,
        context,
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return LpvaultRegisterState.SELECT_POOL


@force_coroutine_logging
async def lpvault_register_select_pool(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(
        "lpvault_register_select_pool triggered by user: %s", update.effective_user.id
    )
    await answer(update)

    pool_index = int(update.callback_query.data.split("_")[-1])
    pool_config_list = await lpvault_service.pool_list(
        CHAIN, LpvaultRegisterSetting.get_setting(context).dex_info["name"]
    )

    if pool_index < 0 or pool_index >= len(pool_config_list):
        await send_or_edit(
            update,
            context,
            "Invalid pool selection. Please try again.",
            parse_mode="Markdown",
        )
        return LpvaultRegisterState.SELECT_POOL

    LpvaultRegisterSetting.get_setting(context).config_index = pool_index

    text = f"You have selected the pool: {pool_config_list[pool_index]['pool_name']}({pool_config_list[pool_index]['dex_type']})\n\n"
    text += (
        "Please set the range percentage for the LP Vault. \n\nThere are three options.\n"
        "- Tap a preset button (e.g., ±1%, ±5%).\n"
        "- Enter a single number (e.g., `5`) → ±5% range.\n"
        "- Enter two numbers with a space (e.g., `-5 3`) → -5% ~ 3% \n"
        "Note: If the range is too narrow, minting may be restricted."
    )

    pcts = pool_config_list[pool_index]["pcts"]

    kb = []
    for pct in pcts:
        kb.append(
            InlineKeyboardButton(
                f"±{pct}%",
                callback_data=f"{LpvaultRegisterState.RANGE_PERCENTAGE.value}_{pct}",
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
    return LpvaultRegisterState.RANGE_PERCENTAGE


@force_coroutine_logging
async def lpvault_register_range_percentage(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(
        "lpvault_register_confirm triggered by user: %s", update.effective_user.id
    )
    await answer(update)
    setting: LpvaultRegisterSetting = LpvaultRegisterSetting.get_setting(context)

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
                    f"Invalid input",
                    parse_mode="Markdown",
                )
                return ConversationHandler.END
            setting: LpvaultRegisterSetting = LpvaultRegisterSetting.get_setting(
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
    register_setting: LpvaultRegisterSetting = LpvaultRegisterSetting.get_setting(
        context
    )
    lpvault_setting = register_setting.lpvault_settings
    table = [
        [
            "Aggregator",
            (
                lpvault_setting["aggregator"]
                if lpvault_setting["aggregator"] != "__auto__"
                else AUTO_AGGREGATOR
            ),
        ],
        [
            "Auto Claim",
            "Enabled" if lpvault_setting["auto_claim"] else "Disabled",
        ],
    ]
    msg = (
        "You have the following settings: \n"
        f"```{tabulate(
            table,
            tablefmt="grid",
        )}```\n"
        "Do you want to proceed with these settings?\n\n"
    )

    kb = [
        [
            InlineKeyboardButton(
                "Yes",
                callback_data=f"{LpvaultRegisterState.USE_EXISTING_SETTINGS.value}_Yes",
            )
        ],
        [
            InlineKeyboardButton(
                "No",
                callback_data=f"{LpvaultRegisterState.USE_EXISTING_SETTINGS.value}_No",
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

    return LpvaultRegisterState.USE_EXISTING_SETTINGS


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
        register_setting: LpvaultRegisterSetting = LpvaultRegisterSetting.get_setting(
            context
        )
        register_setting.aggregator = register_setting.lpvault_settings["aggregator"]
        register_setting.auto_claim = register_setting.lpvault_settings["auto_claim"]

        if register_setting.dex_info["is_ve33"] and register_setting.auto_claim:
            message, kb = await create_data_for_swap_target_token(register_setting)
            await send_or_edit(
                update,
                context,
                message,
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="Markdown",
            )
            return LpvaultRegisterState.SELECT_SWAP_TARGET_TOKEN
        else:
            message = create_register_confirm_message(register_setting)

            kb = [
                [
                    InlineKeyboardButton(
                        "Confirm", callback_data=LpvaultRegisterState.CONFIRM.value
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
            return LpvaultRegisterState.CONFIRM

    # 2. 새로운 설정을 선택하는 경우 -> aggregator 선택으로 이동
    else:
        agg_list: list = await lpvault_service.aggregator_list(CHAIN)

        if len(agg_list) > 1:
            agg_list = [AUTO_AGGREGATOR] + agg_list

        kb = [
            [
                InlineKeyboardButton(
                    agg,
                    callback_data=f"{LpvaultRegisterState.SELECT_AGGREGATOR.value}_{agg}",
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
        return LpvaultRegisterState.SELECT_AGGREGATOR


@force_coroutine_logging
async def lpvault_register_aggregator(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)

    # 1. 사용자가 선택한 agg 저장
    agg = update.callback_query.data.split("_")[-1]
    if agg == AUTO_AGGREGATOR:
        agg = "__auto__"
    register_setting = LpvaultRegisterSetting.get_setting(context)
    register_setting.aggregator = agg

    # 2. auto claim 선택
    # TODO auto claim을 선택한 ve33에서도 파밍된 gov token이 increaseLIquidity에 사용된다고 언급
    message = (
        "Do you want to enable Auto Claim?\n\n"
        "∙ With Auto Claim, If you have unclaimed rewards from farming, they will be automatically claimed periodically and added to your LP position.\n"
    )
    kb = [
        [
            InlineKeyboardButton(
                "Yes", callback_data=f"{LpvaultRegisterState.AUTO_CLAIM.value}_true"
            )
        ],
        [
            InlineKeyboardButton(
                "No", callback_data=f"{LpvaultRegisterState.AUTO_CLAIM.value}_false"
            )
        ],
    ]
    await send_or_edit(
        update,
        context,
        message,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return LpvaultRegisterState.AUTO_CLAIM


@force_coroutine_logging
async def lpvault_register_auto_claim(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    register_setting: LpvaultRegisterSetting = LpvaultRegisterSetting.get_setting(
        context
    )
    response = update.callback_query.data.split("_")[-1]
    register_setting.auto_claim = True if response.lower() == "true" else False

    if register_setting.dex_info["is_ve33"] and register_setting.auto_claim:
        message, kb = await create_data_for_swap_target_token(register_setting)
        await send_or_edit(
            update,
            context,
            message,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown",
        )
        return LpvaultRegisterState.SELECT_SWAP_TARGET_TOKEN
    else:
        kb = [
            [
                InlineKeyboardButton(
                    "Confirm", callback_data=LpvaultRegisterState.CONFIRM.value
                )
            ],
            [InlineKeyboardButton("Cancel", callback_data="lpvault_cancel")],
        ]
        message = create_register_confirm_message(register_setting)

        await send_or_edit(
            update,
            context,
            message,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown",
        )
        return LpvaultRegisterState.CONFIRM


@force_coroutine_logging
async def lpvault_register_select_swap_target_token(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    ticker = update.callback_query.data.split("_")[-1]
    setting = LpvaultRegisterSetting.get_setting(context)
    setting.swap_target_token_ticker = ticker if ticker != "NOSWAP" else None
    setting.swap_target_token_address = (
        await lpvault_service.get_address_by_ticker(CHAIN, ticker)
        if setting.swap_target_token_ticker
        else None
    )

    message = create_register_confirm_message(setting=setting)

    kb = [
        [
            InlineKeyboardButton(
                "Confirm", callback_data=LpvaultRegisterState.CONFIRM.value
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
    return LpvaultRegisterState.CONFIRM


@force_coroutine_logging
async def lpvault_register_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    setting: LpvaultSetting = LpvaultSetting.get_setting(context)
    register_setting: LpvaultRegisterSetting = LpvaultRegisterSetting.get_setting(
        context
    )

    logger.debug(f"{register_setting.dex_info['name']=}")
    dex_type = register_setting.dex_info["name"]
    config_index = register_setting.config_index
    pool_config = register_setting.all_pool_configs[config_index]
    aggregator_mode = (
        "auto"
        if register_setting.aggregator == AUTO_AGGREGATOR
        or register_setting.aggregator == "__auto__"
        else "manual"
    )
    try:
        await lpvault_service.register(
            public_key=setting.account.public_key,
            chain=CHAIN,
            aggregator=register_setting.aggregator,
            aggregator_mode=aggregator_mode,
            dex_type=dex_type,
            token0=pool_config["token0"],
            token1=pool_config["token1"],
            fee=pool_config["fee"],
            upper_range_pct=register_setting.upper_range_pct,
            lower_range_pct=register_setting.lower_range_pct,
            auto_claim=register_setting.auto_claim,
            swap_target_token_address=register_setting.swap_target_token_address,
        )
        await send_or_edit(
            update,
            context,
            "LP vault registered successfully.",
            parse_mode="Markdown",
        )
    except AccountTypeNotFoundException as e:
        await send_or_edit(
            update,
            context,
            f"Something went wrong. Try again later.",
            parse_mode="Markdown",
        )

    return await lpvault_command(update, context)


lpvault_register_states = {
    LpvaultRegisterState.SELECT_DEX: [
        CallbackQueryHandler(
            lpvault_register_select_dex,
            pattern=f"^{LpvaultRegisterState.SELECT_DEX.value}_",
        ),
    ],
    LpvaultRegisterState.SELECT_POOL: [
        CallbackQueryHandler(
            lpvault_register_select_pool,
            pattern=f"^{LpvaultRegisterState.SELECT_POOL.value}_",
        ),
    ],
    LpvaultRegisterState.RANGE_PERCENTAGE: [
        MessageHandler(
            filters.TEXT & ~filters.COMMAND, lpvault_register_range_percentage
        ),
        CallbackQueryHandler(
            lpvault_register_range_percentage,
            pattern=f"^{LpvaultRegisterState.RANGE_PERCENTAGE.value}_",
        ),
    ],
    LpvaultRegisterState.SELECT_AGGREGATOR: [
        CallbackQueryHandler(
            lpvault_register_aggregator,
            pattern=f"^{LpvaultRegisterState.SELECT_AGGREGATOR.value}_",
        ),
    ],
    LpvaultRegisterState.USE_EXISTING_SETTINGS: [
        CallbackQueryHandler(
            lpvault_use_settings_from_existing,
            pattern=f"^{LpvaultRegisterState.USE_EXISTING_SETTINGS.value}_",
        ),
    ],
    LpvaultRegisterState.AUTO_CLAIM: [
        CallbackQueryHandler(
            lpvault_register_auto_claim,
            pattern=f"^{LpvaultRegisterState.AUTO_CLAIM.value}_",
        ),
    ],
    LpvaultRegisterState.SELECT_SWAP_TARGET_TOKEN: [
        CallbackQueryHandler(
            lpvault_register_select_swap_target_token,
            pattern=f"^{LpvaultRegisterState.SELECT_SWAP_TARGET_TOKEN.value}_",
        ),
    ],
    LpvaultRegisterState.CONFIRM: [
        CallbackQueryHandler(
            lpvault_register_confirm,
            pattern=f"^{LpvaultRegisterState.CONFIRM.value}$",
        ),
    ],
}


async def create_data_for_swap_target_token(register_setting: LpvaultRegisterSetting):
    message = (
        "For ve33-based exchanges, auto-claimed governance tokens must be swapped \n"
        "to enable compounding. If you agree, please select the token to swap for harvesting. \n"
        "Otherwise, choose 'Only Claim'."
    )

    core_tokens = await lpvault_service.get_core_tokens(CHAIN)
    wrapped, stable = (
        core_tokens["wrapped"]["ticker"],
        core_tokens["stable"]["ticker"],
    )
    pool_config = register_setting.all_pool_configs[register_setting.config_index]
    ticker0, ticker1 = pool_config["pool_name"].split("/")

    ticker_set = list({ticker0, ticker1, wrapped, stable})

    kb = [
        [
            InlineKeyboardButton(
                f"⭐ {ticker}" if ticker in [ticker0, ticker1] else ticker,
                callback_data=f"{LpvaultRegisterState.SELECT_SWAP_TARGET_TOKEN.value}_{ticker}",
            )
        ]
        for ticker in ticker_set
    ]
    kb.append(
        [
            InlineKeyboardButton(
                f"Only Claim (no swap)",
                callback_data=f"{LpvaultRegisterState.SELECT_SWAP_TARGET_TOKEN.value}_NOSWAP",
            )
        ]
    )

    return message, kb
