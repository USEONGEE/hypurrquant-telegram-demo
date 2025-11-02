from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler
from handler.command import Command
from handler.referral.states import *
from handler.referral.referral_detail import (
    referral_detail_start,
    detail_states,
)
from handler.referral.referral_start import referral_start
from handler.utils.cancel import cancel_handler
from handler.start.states import StartStates

# ================================
# ConversationHandler 등록
# ===============================
referral_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.REFERRAL, referral_start),
        CallbackQueryHandler(
            referral_start,
            pattern=rf"^{StartStates.TRIGGER.value}\|{Command.REFERRAL}$",
        ),
    ],
    states={
        ReferralState.SELECT_ACTION: [
            CallbackQueryHandler(
                referral_detail_start, pattern=f"^{DetailState.START.value}$"
            ),
        ],
        **detail_states,
    },
    fallbacks=[cancel_handler],
    name=Command.REFERRAL,
    allow_reentry=True,
)
