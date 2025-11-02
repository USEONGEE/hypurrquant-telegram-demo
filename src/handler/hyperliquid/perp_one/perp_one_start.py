from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from hypurrquant.models.perp_market_data import MarketData as PerpMarketData
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api.hyperliquid import PerpOrderService, PerpMarketDataCache
from handler.command import Command
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from handler.models.perp_balance import PerpBalanceMapping
from .pagination import PerpMarketDataPagination
from .states import PerpOneStates
from .settings import PerpOneSetting
from .utils import generate_info_text
from handler.utils.decorators import require_builder_fee_approved
from handler.utils.utils import answer, send_or_edit
from typing import List

logger = configure_logging(__name__)

perp_market_data_caache = PerpMarketDataCache()
perp_order_service = PerpOrderService()

CALLBACK_PREFIX = "PERP_ONE_START"

MINIMUM_AMOUNT = 20


# ================================
# 시작 - 전체 종목 조회
# ================================
@require_builder_fee_approved
@force_coroutine_logging
async def perp_one_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    # Initial Setting
    await answer(update)
    PerpOneSetting.clear_setting(context)
    perp_one_setting: PerpOneSetting = PerpOneSetting.get_setting(context)
    market_datas: List[PerpMarketData] = list(
        perp_market_data_caache.market_datas.values()
    )
    account_manager: AccountManager = await fetch_account_manager(context)
    perp_balance_mapping: PerpBalanceMapping = account_manager.perp_balance_mapping
    perp_market_data_pagination = PerpMarketDataPagination(
        market_datas, perp_balance_mapping.withdrawable
    )
    perp_one_setting.perp_market_data_pagination = perp_market_data_pagination

    await show_current_page(update, context)
    return PerpOneStates.PAGE


# =============== #
# 2) 페이지 보여주기 #
# =============== #
@force_coroutine_logging
async def show_current_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    perp_one_setting: PerpOneSetting = PerpOneSetting.get_setting(context)
    pagination = perp_one_setting.perp_market_data_pagination

    # 메시지 텍스트
    info_text = pagination.generate_info_text()  # 각 종목 정보를 문자열로 만듦
    # 버튼
    keyboard_markup = pagination.generate_buttons(callback_prefix=CALLBACK_PREFIX)

    # 이미 콜백 쿼리(CallbackQuery)에서 호출되었다면 edit_message로 갱신
    await send_or_edit(
        update,
        context,
        text=info_text,
        reply_markup=keyboard_markup,
        parse_mode="Markdown",
    )


# =============== #
# 3) 콜백 처리    #
# =============== #
@force_coroutine_logging
async def page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    query = update.callback_query
    await query.answer()
    data = query.data

    perp_one_setting: PerpOneSetting = PerpOneSetting.get_setting(context)
    pagination = perp_one_setting.perp_market_data_pagination

    if data.startswith(f"{CALLBACK_PREFIX}_TOGGLE_"):
        await information(update, context)
        return PerpOneStates.ORDER_SETTING

    elif data == f"{CALLBACK_PREFIX}_NEXT":
        pagination.go_to_next_page()
        await show_current_page(update, context)
        return PerpOneStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_PREV":
        pagination.go_to_prev_page()
        await show_current_page(update, context)
        return PerpOneStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_CANCEL":
        await query.edit_message_text("Canceled")
        return ConversationHandler.END

    else:
        await query.edit_message_text("Invalid callback data")
        return ConversationHandler.END


# =============== #
# 4) information     #
# =============== #
@force_coroutine_logging
async def information(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    perp_one_setting: PerpOneSetting = PerpOneSetting.get_setting(context)

    # callback data에서 ticker 추출하기
    data = update.callback_query.data
    ticker = data.split("_")[-1]
    ticker: PerpMarketData = perp_market_data_caache.market_datas[ticker]

    perp_one_setting.selected_ticker = ticker
    text = generate_info_text(perp_one_setting.selected_ticker)

    # 취소 버튼 추가
    buttons = [
        [
            InlineKeyboardButton(
                "GRAPH", url=f"https://app.hyperliquid.xyz/trade/{ticker.name}"
            )
        ],
        [
            InlineKeyboardButton("LONG", callback_data=f"{CALLBACK_PREFIX}_LONG"),
            InlineKeyboardButton("SHORT", callback_data=f"{CALLBACK_PREFIX}_SHORT"),
        ],
        [InlineKeyboardButton("GO BACK", callback_data=f"{CALLBACK_PREFIX}_GO BACK")],
    ]

    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )

    return PerpOneStates.ORDER_SETTING


# =============== #
# 5) order_setting  #
# =============== #
@force_coroutine_logging
async def order_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    perp_one_setting: PerpOneSetting = PerpOneSetting.get_setting(context)
    data = update.callback_query.data
    instruction = data.split("_")[-1]

    if instruction == "GO BACK":
        await show_current_page(update, context)
        return PerpOneStates.PAGE
    elif instruction == "LONG" or instruction == "SHORT":
        perp_one_setting.position = instruction
        await before_order(update, context)
        return PerpOneStates.SELECT_LEVERAGE
    else:
        await update.callback_query.edit_message_text("Invalid instruction")
        return ConversationHandler.END


# =============== #
# 6) before_order  #
# =============== #
@force_coroutine_logging
async def before_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    perp_one_setting: PerpOneSetting = PerpOneSetting.get_setting(context)

    # 레버리지 선택
    perp_market_data: PerpMarketData = perp_one_setting.selected_ticker
    message = f"Select Leverage: min X1, max X{perp_market_data.maxLeverage}"

    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
    )

    return PerpOneStates.SELECT_LEVERAGE


# =============== #
# 7) select leverage  #
# =============== #
@force_coroutine_logging
async def select_leverage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    perp_one_setting: PerpOneSetting = PerpOneSetting.get_setting(context)
    message = update.message

    perp_market_data: PerpMarketData = perp_one_setting.selected_ticker
    # validaiton: 숫자만 허용
    try:
        value = int(message.text)
    except ValueError:
        await message.reply_text("Please enter a number. Try again.")
        return ConversationHandler.END

    # validaiotn: 주어진 범위 내에서만
    if value < 1 or value > perp_market_data.maxLeverage:
        await message.reply_text(
            f"Please enter a number between 1 and {perp_market_data.maxLeverage}. Try again."
        )
        return ConversationHandler.END

    perp_one_setting.leverage = value

    account_manager: AccountManager = await fetch_account_manager(context)
    perp_balance_mapping: PerpBalanceMapping = account_manager.perp_balance_mapping

    message = f"How much would you like to purchase?\n\n"
    message += f"💰 Max Position Value: {float(perp_balance_mapping.withdrawable) * float(perp_one_setting.leverage)}\n"
    message += f"💰 Min Position Value: {MINIMUM_AMOUNT}\n\n"
    message += f"Please choose carefully, as your input cannot be canceled."

    await update.effective_chat.send_message(
        message,
        parse_mode="Markdown",
    )
    return PerpOneStates.ORDER


# =============== #
# 8) order  #
# =============== #
@force_coroutine_logging
async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    message = update.message

    # validaiton: 숫자만 허용
    try:
        value = float(message.text)
    except ValueError:
        await message.reply_text("Please enter a number. Try again.")
        return ConversationHandler.END
    perp_one_setting: PerpOneSetting = PerpOneSetting.get_setting(context)

    # validation: 최소 금액 확인
    account_manager: AccountManager = await fetch_account_manager(context)
    perp_balance_mapping: PerpBalanceMapping = account_manager.perp_balance_mapping
    current_balance = perp_balance_mapping.withdrawable * float(
        perp_one_setting.leverage
    )
    if value < MINIMUM_AMOUNT or value > current_balance:
        await message.reply_text(
            f"Please enter a number between {MINIMUM_AMOUNT} and {current_balance}. Try again."
        )
        return ConversationHandler.END

    # 주문
    ticker = perp_one_setting.selected_ticker
    order = await perp_order_service.open_market(
        telegram_id=context._user_id,
        tickers=[
            {
                "name": ticker.name,
                "value": value,
                "is_long": True if perp_one_setting.position == "LONG" else False,
                "leverage": perp_one_setting.leverage,
                "is_cross": False,
            }
        ],
    )
    if order:
        await message.reply_text(
            f"Success! You can check your order history using /{Command.BALANCE}"
        )
        return ConversationHandler.END
    else:
        await message.reply_text("An error occurred with the order.")
        return ConversationHandler.END


perp_one_start_state = {
    PerpOneStates.PAGE: [
        CallbackQueryHandler(page_callback, pattern=f"^{CALLBACK_PREFIX}")
    ],
    PerpOneStates.ORDER_SETTING: [
        CallbackQueryHandler(order_setting, pattern=f"^{CALLBACK_PREFIX}")
    ],
    PerpOneStates.SELECT_LEVERAGE: [
        MessageHandler(filters.TEXT, select_leverage),
    ],
    PerpOneStates.ORDER: [
        MessageHandler(filters.TEXT, order),
    ],
}
