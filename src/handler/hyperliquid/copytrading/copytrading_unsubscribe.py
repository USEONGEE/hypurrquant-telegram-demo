from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from hypurrquant.models.account import Account
from .states import (
    CopytradingStates,
    UnsubscribeStates,
)
from .copytrading_start import copytrading_start
from .settings import CopytradingSetting
from api.hyperliquid import CopytradingService

logger = configure_logging(__name__)
copytrading_service = CopytradingService()
PREFIX = "CT_UN_SB"


@force_coroutine_logging
async def copytrading_unsubscribe_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await update.callback_query.answer()
    copytrading_setting = CopytradingSetting.get_setting(context)
    account: Account = copytrading_setting.account

    text = "Unsubscribe\n\n" "unsubscribe"
    # 구독하는 target 목록 조회
    target_accounts = await copytrading_service.get_targets_by_subscriber(
        account.public_key
    )
    buttons = [
        [
            InlineKeyboardButton(
                account,
                callback_data=(f"{PREFIX}|{account}"),
            )
        ]
        for account in target_accounts
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                "Cancel",
                callback_data="copytrading_cancel",
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return UnsubscribeStates.UNSUBSCRIBE


# ================================
# 지갑 변경
# ================================
@force_coroutine_logging
async def copytrading_unsubscribe_change(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    copytrading_setting = CopytradingSetting.get_setting(context)
    account: Account = copytrading_setting.account
    target_public_key = str(update.callback_query.data.split("|")[1])

    # 구독 취소
    await copytrading_service.unsubscribe(account.public_key, target_public_key)

    message = f"success"
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
    )
    await copytrading_start(update, context)
    return CopytradingStates.SELECT_ACTION


unsubscribe_states = {
    UnsubscribeStates.UNSUBSCRIBE: [
        CallbackQueryHandler(copytrading_unsubscribe_change, pattern=f"^{PREFIX}")
    ],
}
