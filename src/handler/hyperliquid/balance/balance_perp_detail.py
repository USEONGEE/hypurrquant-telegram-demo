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
from .states import (
    PerpDetailStates,
    BalanceStates,
)
from .settings import PerpDetailSetting
from .pagination import PerpDetailPagination
from handler.models.perp_balance import (
    PerpBalanceMapping,
    PositionDetail,
)
from handler.utils.cancel import create_cancel_inline_button
from handler.utils.utils import send_or_edit, answer
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from handler.command import Command

from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)


logger = configure_logging(__name__)


CALLBACK_PREFIX = "BALANCE_PERP_DETAIL"


# =============== #
# 2) 시작 페이지 #
# =============== #
@force_coroutine_logging
async def balance_perp_detail_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)

    # 데이터 셋팅
    account_manager: AccountManager = await fetch_account_manager(context)
    perp_balance_mapping: PerpBalanceMapping = (
        await account_manager.refresh_perp_balance()
    )
    logger.debug(f"Perp balance mapping: {type(perp_balance_mapping)}")
    perp_detail_pagination = PerpDetailPagination(data=perp_balance_mapping)
    perp_detail_setting: PerpDetailSetting = PerpDetailSetting.get_setting(context)
    perp_detail_setting.perp_detail_pagination = perp_detail_pagination

    await show_current_page(update, context)
    return PerpDetailStates.PAGE


# =============== #
# 2) 페이지 보여주기 #
# =============== #
@force_coroutine_logging
async def show_current_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    현재 페이지의 종목 목록(문구) + 버튼(이전, 다음, 토글, 확인)을 전송
    """

    perp_detail_setting: PerpDetailSetting = PerpDetailSetting.get_setting(context)
    pagination = perp_detail_setting.perp_detail_pagination

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
    data = update.callback_query.data

    logger.debug(f"Callback data: {data}")

    perp_detail_setting: PerpDetailSetting = PerpDetailSetting.get_setting(context)
    pagination = perp_detail_setting.perp_detail_pagination

    if data.startswith(f"{CALLBACK_PREFIX}_TOGGLE_"):
        await show_more_detail(update, context)
        return PerpDetailStates.GO_BACK

    elif data == f"{CALLBACK_PREFIX}_NEXT":
        pagination.go_to_next_page()
        await show_current_page(update, context)
        return PerpDetailStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_PREV":
        pagination.go_to_prev_page()
        await show_current_page(update, context)
        return PerpDetailStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_CONFIRM":
        # 이전 페이지로 이동
        await balance_start(update, context)
        return BalanceStates.SELECT_ACTION

    else:
        await send_or_edit(
            update,
            context,
            text="Invalid callback data",
            parse_mode="Markdown",
        )
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
    perp_balance_mapping: PerpBalanceMapping = (
        await account_manager.get_perp_balance_mapping()
    )

    perp_detail: PositionDetail = perp_balance_mapping.position.oneWay[ticker]
    logger.debug(f"Selected ticker: {perp_detail.name}")

    message = "```"
    message += f" - Information\n"
    message += "+-------------+--------------+\n"
    message += "|   Ticker    |     Mode     |\n"
    message += "+-------------+--------------+\n"
    message += f"| {ticker:>10}  |   {perp_detail.pos_type:>8}   |\n"
    message += "+-------------+--------------+\n"
    message += f" - Market Direction\n"
    message += "+-------------+--------------+\n"
    message += "|  Direction  |   Leverage   |\n"
    message += "+-------------+--------------+\n"
    message += f"| {'LONG' if perp_detail.is_long else 'SHORT':>10}  |   {perp_detail.leverage:>8.2f} X |\n"
    message += "+-------------+--------------+\n"
    message += f" - Price Comparision\n"
    message += f" ⚠️ Liq Px: {perp_detail.liquidationPx:.2f}\n"
    message += "+-------------+--------------+\n"
    message += "|    Entry    |    Current   |\n"
    message += "+-------------+--------------+\n"
    message += f"| {perp_detail.entryPx:>10.2f}$ |  {perp_detail.midPx:>10.2f}$ |\n"
    message += "+-------------+--------------+\n"
    message += f" - Margin & Position\n"
    message += "+-------------+--------------+\n"
    message += "|   Margin    |   Position   |\n"
    message += "+-------------+--------------+\n"
    message += (
        f"| {perp_detail.marginUsed:>10.2f}$ |  {perp_detail.positionValue:>10.2f}$ |\n"
    )
    message += "+-------------+--------------+\n"
    message += f" - Profitability\n"
    message += "+-------------+--------------+\n"
    message += "|     PNL     |     PNL(%)   |\n"
    message += "+-------------+--------------+\n"
    message += f"| {perp_detail.unrealizedPnl:>10.2f}$ |  {perp_detail.returnOnEquity:>10.2f}% |\n"
    message += "+-------------+--------------+\n"
    message += "```"

    # 뒤로가기 InlineKeyboardButton 추가
    keyboard_markup = InlineKeyboardMarkup(
        [[create_cancel_inline_button(Command.BALANCE)]]
    )

    # 이전 페이지로 이동
    await send_or_edit(
        update,
        context,
        text=message,
        parse_mode="Markdown",
        reply_markup=keyboard_markup,
    )
    return PerpDetailStates.GO_BACK


perp_detail_states = {
    PerpDetailStates.PAGE: [
        CallbackQueryHandler(page_callback, pattern=f"^{CALLBACK_PREFIX}_")
    ]
}
