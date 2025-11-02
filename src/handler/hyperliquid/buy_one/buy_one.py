from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
)

from handler.command import Command
from .buy_one_start import (
    buy_one_start,
    buy_one_start_state,
)
from ..start.states import HLCoreStartState
from handler.utils.cancel import cancel_handler

# ================================
# ConversationHandler 정의
# ================================
buy_one_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.BUY_ONE, buy_one_start),
        CallbackQueryHandler(
            buy_one_start,
            pattern=rf"^{HLCoreStartState.TRIGGER.value}\|{Command.BUY_ONE}$",
        ),
    ],
    states={
        **buy_one_start_state,
    },
    fallbacks=[cancel_handler],
    name=Command.BUY_ONE,
    allow_reentry=True,
)
