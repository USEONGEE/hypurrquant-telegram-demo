from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
)

from .balance_start import balance_start
from .settings import SpotDetailSetting
from .pagination import SpotDetailPagination
from .states import SpotDetailStates
from handler.utils.utils import answer, send_or_edit
from handler.utils.cancel import initialize_handler
from handler.models.spot_balance import SpotBalance, SpotBalanceMapping
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager

from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)


logger = configure_logging(__name__)


CALLBACK_PREFIX = "BALANCE_SPOT_DETAIL"


# =============== #
# 2) 시작 페이지 #
# =============== #
@force_coroutine_logging
@initialize_handler(setting_cls=SpotDetailSetting)
async def balance_spot_detail_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    # 데이터 셋팅
    account_manager: AccountManager = await fetch_account_manager(context)
    spot_balance_mapping: SpotBalanceMapping = (
        await account_manager.refresh_spot_balance()
    )
    spot_detail_pagination = SpotDetailPagination(data=spot_balance_mapping)
    spot_detail_setting: SpotDetailSetting = SpotDetailSetting.get_setting(context)
    spot_detail_setting.spot_detail_pagination = spot_detail_pagination

    await show_current_page(update, context)
    return SpotDetailStates.PAGE


# =============== #
# 2) 페이지 보여주기 #
# =============== #
@force_coroutine_logging
async def show_current_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    현재 페이지의 종목 목록(문구) + 버튼(이전, 다음, 토글, 확인)을 전송
    """

    spot_detail_setting: SpotDetailSetting = SpotDetailSetting.get_setting(context)
    pagination = spot_detail_setting.spot_detail_pagination

    # 메시지 텍스트
    info_text = pagination.generate_info_text()  # 각 종목 정보를 문자열로 만듦
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

    await answer(update)
    data = update.callback_query.data  # ex) "STOCKS_TOGGLE_AAPL" or "STOCKS_PREV" etc.

    spot_detail_setting: SpotDetailSetting = SpotDetailSetting.get_setting(context)
    pagination = spot_detail_setting.spot_detail_pagination

    if data.startswith(f"{CALLBACK_PREFIX}_TOGGLE_"):
        await show_more_detail(update, context)
        return SpotDetailStates.GO_BACK

    elif data == f"{CALLBACK_PREFIX}_NEXT":
        pagination.go_to_next_page()
        await show_current_page(update, context)
        return SpotDetailStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_PREV":
        pagination.go_to_prev_page()
        await show_current_page(update, context)
        return SpotDetailStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_CONFIRM":
        # 이전 페이지로 이동
        return await balance_start(update, context)

    else:
        await send_or_edit(update, context, "Invalid callback data")
        return ConversationHandler.END


# =============== #
# 4) 종목 디테일 보여주기 #
# =============== #
@force_coroutine_logging
async def show_more_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    종목 디테일 보여주기
    """
    await answer(update)
    data = update.callback_query.data
    ticker = data.split(f"{CALLBACK_PREFIX}_TOGGLE_")[1]

    account_manager: AccountManager = await fetch_account_manager(context)
    spot_balance_mapping: SpotBalanceMapping = (
        await account_manager.get_spot_balance_mapping()
    )

    spot_balance: SpotBalance = spot_balance_mapping.balances[ticker]
    logger.debug(f"Selected ticker: {spot_balance.Name}")

    message = f"- Ticker name: {ticker}\n"
    message += f"- Balance: {spot_balance.Balance} ({ticker})\n```"
    message += f" - Price Comparision\n"
    message += "+-------------+--------------+\n"
    message += "|    Entry    |    Current   |\n"
    message += "+-------------+--------------+\n"
    message += (
        f"| {spot_balance.EntryPrice:>10.2f}$ |  {spot_balance.Price:>10.2f}$ |\n"
    )
    message += "+-------------+--------------+\n"
    message += f" - Capital and Valuation\n"
    message += "+-------------+--------------+\n"
    message += "|  Principal  |    Current   |\n"
    message += "+-------------+--------------+\n"
    message += f"| {spot_balance.entryNtl:>10.2f}$ |  {spot_balance.Value:>10.2f}$ |\n"
    message += "+-------------+--------------+\n"
    message += f" - Profitability\n"
    message += "+-------------+--------------+\n"
    message += "|     PNL     |     PNL(%)   |\n"
    message += "+-------------+--------------+\n"
    message += f"| {spot_balance.PNL:>10.2f}$ |  {spot_balance.PNL_percent:>10.2f}% |\n"
    message += "+-------------+--------------+\n"
    message += "```"

    # 뒤로가기 InlineKeyboardButton 추가
    keyboard_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("BACK", callback_data=f"{CALLBACK_PREFIX}_GO_BACK")]]
    )

    # 이전 페이지로 이동
    await send_or_edit(
        update, context, message, parse_mode="Markdown", reply_markup=keyboard_markup
    )
    return SpotDetailStates.GO_BACK


# =============== #
# 5) 이전으로 가기
# =============== #
@force_coroutine_logging
async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    이전 페이지로 이동
    """
    await answer(update)
    await show_current_page(update, context)
    return SpotDetailStates.PAGE


spot_detail_states = {
    SpotDetailStates.PAGE: [
        CallbackQueryHandler(page_callback, pattern=f"^{CALLBACK_PREFIX}_")
    ],
    SpotDetailStates.GO_BACK: [
        CallbackQueryHandler(go_back, pattern=f"^{CALLBACK_PREFIX}_GO_BACK")
    ],
}
