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

from handler.referral.pagination import ReferralDetailPagination
from handler.referral.settings import ReferralDetailSetting, ReferralSetting
from handler.referral.states import *
from handler.referral.referral_start import referral_start
from handler.utils.utils import send_or_edit, answer

from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)


logger = configure_logging(__name__)


CALLBACK_PREFIX = "REFERRAL_DETAIL"


# =============== #
# 2) 시작 페이지 #
# =============== #
@force_coroutine_logging
async def referral_detail_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)

    summary = ReferralSetting.get_setting(context).summary
    ReferralDetailSetting.get_setting(context).pagination = ReferralDetailPagination(
        summary["details"]
    )

    await show_current_page(update, context)
    return DetailState.PAGE


# =============== #
# 2) 페이지 보여주기 #
# =============== #
@force_coroutine_logging
async def show_current_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    현재 페이지의 종목 목록(문구) + 버튼(이전, 다음, 토글, 확인)을 전송
    """

    referral_detail_setting: ReferralDetailSetting = ReferralDetailSetting.get_setting(
        context
    )
    pagination: ReferralDetailPagination = referral_detail_setting.pagination

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

    logger.debug(f"Callback data: {data}")

    referral_detail_setting: ReferralDetailSetting = ReferralDetailSetting.get_setting(
        context
    )
    pagination = referral_detail_setting.pagination

    if data == f"{CALLBACK_PREFIX}_NEXT":
        pagination.go_to_next_page()
        await show_current_page(update, context)
        return DetailState.PAGE

    elif data == f"{CALLBACK_PREFIX}_PREV":
        pagination.go_to_prev_page()
        await show_current_page(update, context)
        return DetailState.PAGE

    elif data == f"{CALLBACK_PREFIX}_GO_BACK":
        return await referral_start(update, context)

    else:
        await send_or_edit(update, context, "Invalid callback data")
        return ConversationHandler.END


detail_states = {
    DetailState.PAGE: [
        CallbackQueryHandler(page_callback, pattern=f"^{CALLBACK_PREFIX}_")
    ],
}
