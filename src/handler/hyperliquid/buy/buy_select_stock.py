# .stock_select.py

from enum import Enum, auto
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from .pagenations import (
    MarketDataPagination,
)
from .model.orderable_market_data import (
    OrderableMarketData,
)
from .states import StockSelectStates, OrderStates
from .settings import (
    StockSelectSetting,
    BuySetting,
)
from .utils import (
    get_needed_balance,
    is_sufficient_balance,
)
from handler.utils.account_helpers import (
    fetch_active_wallet_usdc_balance,
)

CALLBACK_PREFIX = "BUY_SELECT_STOCK"

logger = configure_logging(__name__)


# =============== #
# 1) 엔트리 함수  #
# =============== #
@force_coroutine_logging
async def start_stock_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    BuyConversation에서 넘어올 때 호출되는 엔트리 함수.
    1) buy_setting.filterd_stocks를 OrderableMarketData로 변환
    2) MarketDataPagination 생성 -> StockSelectSetting.pagination 에 저장
    3) 첫 화면(페이지) 전송
    """
    query = update.callback_query
    await query.answer()
    buy_setting: BuySetting = BuySetting.get_setting(context)

    # 만약 이미 필터링된 종목이 없다면, 대화 종료 또는 다른 처리
    if not buy_setting.filterd_stocks:
        await update.callback_query.message.reply_text(
            "No stocks were found based on the parameters you selected. Please try again with /buy."
        )
        return ConversationHandler.END

    # OrderableMarketData로 변환
    orderable_list = [
        OrderableMarketData.from_market_data(md) for md in buy_setting.filterd_stocks
    ]

    buy_setting.orderable_market_data = orderable_list

    crruent_balance: float = await fetch_active_wallet_usdc_balance(context)
    # Pagination 생성
    pagination = MarketDataPagination(
        market_data=orderable_list, current_balance=crruent_balance, page_size=15
    )

    # StockSelectSetting에 저장
    select_setting: StockSelectSetting = StockSelectSetting.get_setting(context)
    select_setting.pagination = pagination

    # 첫 페이지 보여주기
    await show_current_page(update, context)
    return StockSelectStates.PAGE


# =============== #
# 2) 페이지 보여주기 #
# =============== #
@force_coroutine_logging
async def show_current_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    현재 페이지의 종목 목록(문구) + 버튼(이전, 다음, 토글, 확인)을 전송
    """
    select_setting: StockSelectSetting = StockSelectSetting.get_setting(context)
    pagination = select_setting.pagination

    # 메시지 텍스트
    info_text = await pagination.generate_info_text()
    # 버튼
    keyboard_markup = pagination.generate_buttons(callback_prefix=CALLBACK_PREFIX)

    # 이미 콜백 쿼리(CallbackQuery)에서 호출되었다면 edit_message로 갱신
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=info_text, reply_markup=keyboard_markup, parse_mode="Markdown"
        )
    else:
        await update.effective_chat.send_message(
            text=info_text, reply_markup=keyboard_markup, parse_mode="Markdown"
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

    select_setting: StockSelectSetting = StockSelectSetting.get_setting(context)
    pagination = select_setting.pagination

    if data.startswith(f"{CALLBACK_PREFIX}_TOGGLE_"):
        # 종목 선택/해제 토글
        ticker = data.split(f"{CALLBACK_PREFIX}_TOGGLE_")[1]
        # 현재 페이지 내 데이터 탐색
        current_page_data = pagination.get_current_page_data()
        for item in current_page_data:
            if item.Tname == ticker:
                item.is_buy = not item.is_buy
                break  # 찾으면 즉시 종료

        await show_current_page(update, context)
        return StockSelectStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_NEXT":
        pagination.go_to_next_page()
        await show_current_page(update, context)
        return StockSelectStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_PREV":
        pagination.go_to_prev_page()
        await show_current_page(update, context)
        return StockSelectStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_CONFIRM":

        buy_setting = BuySetting.get_setting(context)
        buy_setting.orderable_market_data = [d for d in pagination.data if d.is_buy]
        balance = await fetch_active_wallet_usdc_balance(context)

        # 검증
        if not is_sufficient_balance(buy_setting.orderable_market_data, balance):
            await query.edit_message_text("You do not have sufficient balance.")
            return ConversationHandler.END

        if len(buy_setting.orderable_market_data) <= 0:
            await query.edit_message_text(
                "No stocks selected. Please select at least one stock to proceed."
            )
            return ConversationHandler.END

        keyboard = [[InlineKeyboardButton("Next", callback_data="GO_ORDER")]]
        markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            "Stock selection is complete. Click 'Next' to proceed to the order stage.",
            reply_markup=markup,
            parse_mode="Markdown",
        )
        return OrderStates.START

    else:
        await query.edit_message_text(
            "Oops, that's not valid. Please give it another try!"
        )
        return ConversationHandler.END


# # ================================
# # ConversationHandler 정의
# # ================================
# stock_select_conv = ConversationHandler(
#     entry_points=[
#         CallbackQueryHandler(start_stock_selection, pattern="^go_select_stock$")
#     ],
#     states={
#         StockSelectStates.PAGE: [
#             CallbackQueryHandler(page_callback, pattern=r"^STOCKS_")
#         ],
#     },
#     fallbacks=[],
#     allow_reentry=True,
#     map_to_parent={StockSelectStates.END: BuyStates.ORDER},
# )


select_stock_states = {
    StockSelectStates.START: [
        CallbackQueryHandler(start_stock_selection, pattern="^GO_SELECT_STOCK")
    ],
    StockSelectStates.PAGE: [
        CallbackQueryHandler(page_callback, pattern=f"^{CALLBACK_PREFIX}_")
    ],
}
