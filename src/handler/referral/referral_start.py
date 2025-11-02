from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from api import AccountService
from handler.referral.states import ReferralState, DetailState
from handler.referral.settings import ReferralSetting
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from handler.utils.utils import answer, send_or_edit
from handler.utils.cancel import create_cancel_inline_button
from handler.command import Command
import os

logger = configure_logging(__name__)

account_service = AccountService()

BOT_NAME = os.getenv("BOT_NAME")

if BOT_NAME is None:
    logger.error("BOT_NAME environment variable is not set.")
    raise ValueError("BOT_NAME environment variable is not set.")


@force_coroutine_logging
async def referral_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    logger.info("referral_start called")

    # 1. 데이터 가져오기 및 설정
    code = await account_service.get_referral_code(context._user_id)
    summary = await account_service.get_referral_summary(context._user_id)
    referral_setting = ReferralSetting.get_setting(context)
    referral_setting.summary = summary

    # 2. 메시지 텍스트 생성
    message = (
        "<b>🪪 Referral Program</b>\n\n"
        f"Your referral link is: <code>https://t.me/{BOT_NAME}?start={code}</code>\n\n"
        "🔄 Referral rewards are settled every 24 hours. "
        "Payouts are made only when your available balance exceeds 1 USDC, "
        "and any unpaid balance will roll over to the next cycle.\n"
        "💰 You can earn up to 50% commission on hyperliquid referral profits.\n\n"
        "<b>📊 Your Referral Summary</b>\n"
        f"- Total referees: {summary['num_referees']}\n"
        f"- Total earned: {summary['total_earned']:.6f} USDC\n"
        f"- Total paid out: {summary['total_paid']:.6f} USDC\n"
        f"- Still unpaid: {summary['total_unpaid']:.6f} USDC\n"
    )

    # 3. 버튼 생성
    button = [
        [
            InlineKeyboardButton(
                text="View Details",
                callback_data=DetailState.START.value,
            )
        ],
        [create_cancel_inline_button(Command.START)],
    ]

    await send_or_edit(
        update,
        context,
        text=message,
        reply_markup=InlineKeyboardMarkup(button),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    return ReferralState.SELECT_ACTION
