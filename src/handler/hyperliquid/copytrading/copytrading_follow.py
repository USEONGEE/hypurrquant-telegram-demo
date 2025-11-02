from telegram import Update
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
)

from api.hyperliquid import CopytradingService
from .pagination import SubscriptionPagination
from .settings import *
from .states import (
    FollowStates,
    CopytradingStates,
)
from .copytrading_start import copytrading_start

from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)


logger = configure_logging(__name__)
copytrading_service = CopytradingService()

CALLBACK_PREFIX = "CT_F"


# =============== #
# 2) 시작 페이지 #
# =============== #
@force_coroutine_logging
async def follow_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    query = update.callback_query
    await query.answer()

    # 데이터 셋팅
    page_size = 15
    data = await copytrading_service.page_subscription(page_size=page_size)
    logger.info(f"page_subscription {data}")
    pagination = SubscriptionPagination(data=data)
    follow_setting: FollowSetting = FollowSetting.get_setting(context)
    follow_setting.pagination = pagination

    await show_current_page(update, context)
    return FollowStates.PAGE


# =============== #
# 2) 페이지 보여주기 #
# =============== #
@force_coroutine_logging
async def show_current_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    현재 페이지의 종목 목록(문구) + 버튼(이전, 다음, 토글, 확인)을 전송
    """

    follow_setting: FollowSetting = FollowSetting.get_setting(context)
    pagination = follow_setting.pagination

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
    query = update.callback_query
    await query.answer()
    data = query.data  # ex) "STOCKS_TOGGLE_AAPL" or "STOCKS_PREV" etc.

    follow_setting: FollowSetting = FollowSetting.get_setting(context)
    pagination = follow_setting.pagination

    if data.startswith(f"{CALLBACK_PREFIX}_TOGGLE_"):
        await show_more_detail(update, context)
        await copytrading_start(update, context)
        return CopytradingStates.SELECT_ACTION

    elif data == f"{CALLBACK_PREFIX}_NEXT":
        pagination.go_to_next_page()
        await show_current_page(update, context)
        return FollowStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_PREV":
        pagination.go_to_prev_page()
        await show_current_page(update, context)
        return FollowStates.PAGE

    elif data == f"{CALLBACK_PREFIX}_CONFIRM":
        # 이전 페이지로 이동
        await copytrading_start(update, context)
        return CopytradingStates.SELECT_ACTION

    else:
        await query.edit_message_text("Invalid callback data")
        return ConversationHandler.END


# =============== #
# 4) 구독하기
# =============== #
@force_coroutine_logging
async def show_more_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    종목 디테일 보여주기
    """
    query = update.callback_query
    await query.answer()
    # 필요한 정보 가져오기
    data = query.data
    target_public_key = data.split(f"{CALLBACK_PREFIX}_TOGGLE_")[1]
    account = CopytradingSetting.get_setting(context).account

    # 구독 요청 보내기
    await copytrading_service.subscribe(account.public_key, target_public_key)

    # 응답 메시지 보내기
    info_text = "success"
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=info_text, parse_mode="Markdown"
        )
    else:
        await update.effective_chat.send_message(text=info_text, parse_mode="Markdown")


# =============== #
# 5) 이전으로 가기
# =============== #
@force_coroutine_logging
async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    이전 페이지로 이동
    """
    logger.debug("Go back")
    query = update.callback_query
    await query.answer()

    await show_current_page(update, context)
    return FollowStates.PAGE


follow_states = {
    FollowStates.PAGE: [
        CallbackQueryHandler(page_callback, pattern=f"^{CALLBACK_PREFIX}_")
    ],
    FollowStates.GO_BACK: [
        CallbackQueryHandler(go_back, pattern=f"^{CALLBACK_PREFIX}_GO_BACK")
    ],
}
