from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from api import AccountService
from api.hyperliquid import BuyOrderService, MarketDataCache
from hypurrquant.models.market_data import MarketData
from hypurrquant.logging_config import (
    force_coroutine_logging,
)
from handler.command import Command
from handler.utils.account_helpers import (
    fetch_active_wallet_usdc_balance,
)
from .pagination import MarketDataPagination
from .settings import BuyOneSetting
from .states import BuyOneStates
from .utils import generate_info_text
from hypurrquant.logging_config import configure_logging
from handler.utils.decorators import (
    require_builder_fee_approved,
)
from handler.utils.utils import answer, send_or_edit

from typing import List

logger = configure_logging(__name__)

MINIMUM_AMOUNT = 20  # 최소 매수 금액

fetcher = MarketDataCache()
accountService = AccountService()
buyOrderService = BuyOrderService()

CALLBACK_PREFIX = "BUY_ONE_START"


# ================================
# 시작 - 전체 종목 조회
# ================================
@require_builder_fee_approved
@force_coroutine_logging
async def buy_one_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    BuyOneSetting.clear_setting(context)
    buy_one_setting: BuyOneSetting = BuyOneSetting.get_setting(context)
    market_datas: List[MarketData] = fetcher._market_datas
    current_balance = await fetch_active_wallet_usdc_balance(context)
    market_data_pagination = MarketDataPagination(
        market_data=market_datas, current_balance=current_balance
    )
    buy_one_setting.market_data_pagination = market_data_pagination

    await show_current_page(update, context)
    return BuyOneStates.PAGE


# =============== #
# 2) 페이지 보여주기 #
# =============== #
@force_coroutine_logging
async def show_current_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    현재 페이지의 종목 목록(문구) + 버튼(이전, 다음, 토글, 확인)을 전송
    """
    logger.debug("show_current_page")
    buy_one_setting: BuyOneSetting = BuyOneSetting.get_setting(context)
    pagination = buy_one_setting.market_data_pagination

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
    data = query.data  # ex) "STOCKS_TOGGLE_AAPL" or "STOCKS_PREV" etc.

    buy_one_setting: BuyOneSetting = BuyOneSetting.get_setting(context)
    pagination = buy_one_setting.market_data_pagination

    if data.startswith(f"{CALLBACK_PREFIX}_TOGGLE_"):
        await information(update, context)
        return BuyOneStates.ORDER_SETTING

    elif data == f"{CALLBACK_PREFIX}_NEXT":
        pagination.go_to_next_page()
        await show_current_page(update, context)
        return BuyOneStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_PREV":
        pagination.go_to_prev_page()
        await show_current_page(update, context)
        return BuyOneStates.PAGE

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
    buy_one_setting: BuyOneSetting = BuyOneSetting.get_setting(context)

    logger.debug("information")

    # callback data에서 ticker 추출하기
    data = update.callback_query.data
    ticker = data.split("_")[-1]
    ticker: MarketData = fetcher.filter_by_Tname(ticker)

    buy_one_setting.selected_ticker = ticker
    text = generate_info_text(buy_one_setting.selected_ticker)

    # 취소 버튼 추가
    buttons = [
        [
            InlineKeyboardButton(
                "GRAPH", url=f"https://app.hyperliquid.xyz/trade/{ticker.tokenId}"
            )
        ],
        [InlineKeyboardButton("BUY", callback_data=f"{CALLBACK_PREFIX}_BUY")],
        [InlineKeyboardButton("GO BACK", callback_data=f"{CALLBACK_PREFIX}_GO BACK")],
    ]

    # 티커 정보 가져오기

    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )

    return BuyOneStates.ORDER_SETTING


# =============== #
# 5) order_setting  #
# =============== #
@force_coroutine_logging
async def order_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")

    logger.debug("order_setting")

    data = update.callback_query.data
    instruction = data.split("_")[-1]

    if instruction == "GO BACK":
        await show_current_page(update, context)
        return BuyOneStates.PAGE
    elif instruction == "BUY":
        await before_order(update, context)
        return BuyOneStates.ORDER
    else:
        await update.callback_query.edit_message_text("Invalid instruction")
        return ConversationHandler.END


# =============== #
# 6) before_order  #
# =============== #
@force_coroutine_logging
async def before_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    buy_one_setting: BuyOneSetting = BuyOneSetting.get_setting(context)
    ticker = buy_one_setting.selected_ticker

    # validaiton: 최소 금액 확인
    if MINIMUM_AMOUNT > buy_one_setting.market_data_pagination.current_balance:
        await update.callback_query.edit_message_text(
            "You don't have enough balance to buy this token."
        )
        return ConversationHandler.END

    current_balance = await fetch_active_wallet_usdc_balance(context)
    message = f"How much would you like to purchase?\n\n"
    message += f"💰 Max USDC: {current_balance}\n"
    message += f"💰 Min USDC: {MINIMUM_AMOUNT}\n\n"
    message += f"Please choose carefully, as your input cannot be canceled."

    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
    )


# =============== #
# 7) order  #
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

    # validation: 최소 금액 확인
    current_balance = await fetch_active_wallet_usdc_balance(context)
    if value < MINIMUM_AMOUNT or value > current_balance:
        await message.reply_text(
            f"Please enter a number between {MINIMUM_AMOUNT} and {current_balance}. Try again."
        )
        return ConversationHandler.END

    # 주문
    buy_one_setting: BuyOneSetting = BuyOneSetting.get_setting(context)
    ticker = buy_one_setting.selected_ticker
    order = await buyOrderService.buy_order_market_usdc(
        telegram_id=context._user_id,
        tickers=[{"name": ticker.Tname, "value": value}],
    )

    if order:
        await message.reply_text(
            f"Success! You can check your order history using /{Command.BALANCE}"
        )
        return ConversationHandler.END
    else:
        await message.reply_text("An error occurred with the order.")
        return ConversationHandler.END


buy_one_start_state = {
    BuyOneStates.PAGE: [
        CallbackQueryHandler(page_callback, pattern=f"^{CALLBACK_PREFIX}")
    ],
    BuyOneStates.ORDER_SETTING: [
        CallbackQueryHandler(order_setting, pattern=f"^{CALLBACK_PREFIX}")
    ],
    BuyOneStates.ORDER: [MessageHandler(filters=filters.TEXT, callback=order)],
}
