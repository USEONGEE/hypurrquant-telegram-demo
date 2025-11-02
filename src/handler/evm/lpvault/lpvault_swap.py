from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api import AccountService, LpVaultService
from handler.utils.account_helpers import fetch_active_account
from handler.utils.utils import answer, send_or_edit, format_buttons_grid
from handler.utils.cancel import (
    create_cancel_inline_button,
    initialize_handler,
    main_menu,
)
from hypurrquant.models.account import Account
from .states import LpvaultSwapState
from .settings import LpvaultSwapSetting

from tabulate import tabulate
import asyncio

logger = configure_logging(__name__)

account_service = AccountService()
lpvault_service = LpVaultService()

CHAIN = "HYPERLIQUID"  # TODO 추후엔 LpVaultSetting으로 넘어가야함.


@force_coroutine_logging
@initialize_handler(setting_cls=LpvaultSwapSetting)
async def lpvault_swap_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    setting: LpvaultSwapSetting = LpvaultSwapSetting.get_setting(context)
    await answer(update)
    account: Account = await fetch_active_account(context)
    setting.tokens = await lpvault_service.get_tokens_for_swap(
        account.public_key, CHAIN
    )

    msg = "which token do you want to swap?"

    kb = [
        InlineKeyboardButton(
            f"{token} ({value['amount']:.3f})",
            callback_data=f"{LpvaultSwapState.SELECT_IN_TICKER.value}|{token}",
        )
        for token, value in setting.tokens.items()
    ]

    grid_kb = format_buttons_grid(kb, 2)

    grid_kb.append([create_cancel_inline_button(setting.return_to)])

    await send_or_edit(
        update,
        context,
        msg,
        reply_markup=InlineKeyboardMarkup(grid_kb),
        parse_mode="Markdown",
    )
    return LpvaultSwapState.SELECT_IN_TICKER


@force_coroutine_logging
async def lpvault_swap_select_in_ticker(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(f"triggerred by user: {context._user_id}")
    setting: LpvaultSwapSetting = LpvaultSwapSetting.get_setting(context)

    selected_token = update.callback_query.data.split("|")[1]
    logger.info(f"{selected_token=}")
    if selected_token in setting.tokens:
        setting.selected_in_token = selected_token
        logger.debug(f"{setting.selected_in_token=}")
    else:
        raise ValueError("Invalid token selected.")

    msg = "How much do you want to swap? Click button or enter percentage."

    percentages = [50, 100]
    kb = [
        [
            InlineKeyboardButton(
                f"{amount}%",
                callback_data=f"{LpvaultSwapState.SELECT_AMOUNT.value}|{amount}",
            )
        ]
        for amount in percentages
    ]
    kb.append([create_cancel_inline_button(setting.return_to)])

    await send_or_edit(
        update,
        context,
        msg,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )

    return LpvaultSwapState.SELECT_AMOUNT


async def lpvault_swap_select_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(f"triggerred by user: {context._user_id}")
    setting: LpvaultSwapSetting = LpvaultSwapSetting.get_setting(context)

    # 1. 사용자 입력 percentage parsing & validation
    if update.message:
        try:
            percentage = int(update.message.text)
        except ValueError:
            raise ValueError("Please enter a valid percentage.")
    elif update.callback_query:
        await answer(update)
        percentage = int(update.callback_query.data.split("|")[1])
    else:
        await update.effective_message.reply_text(
            "Please enter a valid account public key."
        )
        return ConversationHandler.END

    if percentage < 0 or percentage > 100:
        raise ValueError("Percentage must be between 0 and 100.")
    setting.amount_percentage = percentage
    # 2. 메시지 생성
    msg = "which token do you want to swap out ?"

    kb = [
        InlineKeyboardButton(
            f"{token}",
            callback_data=f"{LpvaultSwapState.SELECT_OUT_TICKER.value}|{token}",
        )
        for token, _ in setting.tokens.items()
        if token != setting.selected_in_token
    ]
    grid_kb = format_buttons_grid(kb, 2)
    grid_kb.append([create_cancel_inline_button(setting.return_to)])
    await send_or_edit(
        update,
        context,
        msg,
        reply_markup=InlineKeyboardMarkup(grid_kb),
        parse_mode="Markdown",
    )

    return LpvaultSwapState.SELECT_OUT_TICKER


async def lpvault_swap_select_out_ticker(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await answer(update)
    await send_or_edit(update, context, "Fetching routes...")
    logger.info(f"triggerred by user: {context._user_id}")
    setting = LpvaultSwapSetting.get_setting(context)
    account: Account = await fetch_active_account(context)

    selected_token = update.callback_query.data.split("|")[1]
    if selected_token in setting.tokens:
        setting.selected_out_token = selected_token
    else:
        raise ValueError("Invalid token selected.")

    # 1. swap route 조회
    setting.swap_routes = await lpvault_service.create_routes(
        account.public_key,
        CHAIN,
        setting.tokens[setting.selected_in_token]["address"],
        setting.tokens[setting.selected_out_token]["address"],
        setting.tokens[setting.selected_in_token]["amount"]
        * setting.amount_percentage
        / 100,
    )
    routes: list = setting.swap_routes["routes"]
    routes.sort(
        key=lambda r: r["min_out_human"], reverse=True
    )  # `amount_out_human`으로 정렬

    if len(routes) < 1:
        raise ValueError("No valid swap routes found.")

    # 2. 응답
    msg = (
        "which aggregator do you want to use?\n"
        "*NOTE*\n"
        "- `PI` means `price impact`\n"
        "- It is sorted in descending order of min out.\n"
        "```\n"
    )

    for route in routes:
        msg += f"{route['aggregator']}\n"
        data = [
            [
                "In",
                f"{route['amount_in_human']:.2f} {setting.swap_routes['token_in_ticker']}",
            ],
            [
                "Out",
                f"{route['amount_out_human']:.2f} {setting.swap_routes['token_out_ticker']}",
            ],
            [
                "Min out",
                f"{route['min_out_human']:.2f} {setting.swap_routes['token_out_ticker']}",
            ],
            ["PI", f"{route['price_impact']:.2f} %"],
        ]
        msg += f"{tabulate(data, tablefmt='grid')}\n"
    msg += "```"

    kb = [
        [
            InlineKeyboardButton(
                f"{route['aggregator']}",
                callback_data=f"{LpvaultSwapState.SELECT_AGGREGATION.value}|{route['aggregator']}",
            )
            for route in routes
        ]
    ]
    kb.append([create_cancel_inline_button(setting.return_to)])

    await send_or_edit(
        update,
        context,
        msg,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )

    return LpvaultSwapState.SELECT_AGGREGATION


async def lpvault_swap_select_aggregator(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info(f"triggerred by user: {context._user_id}")
    setting = LpvaultSwapSetting.get_setting(context)

    # 1. 사용자가 선택한 aggregator validation & save
    setting.selected_aggregator = update.callback_query.data.split("|")[1]
    route = next(
        (
            r
            for r in setting.swap_routes["routes"]
            if r["aggregator"] == setting.selected_aggregator
        ),
        None,
    )

    if not route:
        raise ValueError("Something went wrong. Please try again.")

    # 2. Confirm Message 생성
    data = [
        ["In", f"{route['amount_in_human']:.2f}"],
        ["Out", f"{route['amount_out_human']:.2f}"],
        ["Min out", f"{route['min_out_human']:.2f}"],
        ["PI", f"{route['price_impact']:.2f} %"],
    ]
    msg = f"Please confirm your swap \n```\n"
    msg += f"{route["aggregator"]}({setting.swap_routes['token_in_ticker']} -> {setting.swap_routes['token_out_ticker']})\n"
    msg += f"{tabulate(data, tablefmt='grid')}\n```"

    kb = [
        [
            InlineKeyboardButton(
                "Confirm",
                callback_data=f"{LpvaultSwapState.CONFIRM.value}|Ok",
            )
        ],
        [create_cancel_inline_button(setting.return_to)],
    ]

    await send_or_edit(
        update,
        context,
        msg,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )

    return LpvaultSwapState.CONFIRM


async def lpvault_swap_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    setting = LpvaultSwapSetting.get_setting(context)
    await send_or_edit(update, context, "Swapping 🔄")

    txid = await lpvault_service.execute_swap(
        setting.swap_routes["context_id"], setting.selected_aggregator
    )
    logger.debug(f"swap response: {txid}")

    await send_or_edit(
        update,
        context,
        f"Swap successful! Transaction ID: `{txid}`",
        parse_mode="Markdown",
    )
    await asyncio.sleep(3)
    return await main_menu(update, context, setting.return_to)


lpvault_swap_states = {
    LpvaultSwapState.SELECT_IN_TICKER: [
        CallbackQueryHandler(
            lpvault_swap_select_in_ticker,
            pattern=f"^{LpvaultSwapState.SELECT_IN_TICKER.value}",
        )
    ],
    LpvaultSwapState.SELECT_OUT_TICKER: [
        CallbackQueryHandler(
            lpvault_swap_select_out_ticker,
            pattern=f"^{LpvaultSwapState.SELECT_OUT_TICKER.value}",
        )
    ],
    LpvaultSwapState.SELECT_AMOUNT: [
        CallbackQueryHandler(
            lpvault_swap_select_amount,
            pattern=f"^{LpvaultSwapState.SELECT_AMOUNT.value}",
        ),
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            lpvault_swap_select_amount,
        ),
    ],
    LpvaultSwapState.SELECT_AGGREGATION: [
        CallbackQueryHandler(
            lpvault_swap_select_aggregator,
            pattern=f"^{LpvaultSwapState.SELECT_AGGREGATION.value}",
        )
    ],
    LpvaultSwapState.CONFIRM: [
        CallbackQueryHandler(
            lpvault_swap_confirm,
            pattern=f"^{LpvaultSwapState.CONFIRM.value}",
        )
    ],
}
