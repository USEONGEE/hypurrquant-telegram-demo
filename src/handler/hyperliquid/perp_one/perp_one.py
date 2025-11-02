from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
)

from handler.command import Command
from handler.utils.cancel import cancel_handler as common_cancel_handler
from .perp_one_start import (
    perp_one_start,
    perp_one_start_state,
)
from ..start.states import HLCoreStartState
from handler.hyperliquid.buy_one.utils import CONVERSATION_HANDLER_NAME


# ================================
# ConversationHandler 정의
# ================================
perp_one_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.PERP_ONE, perp_one_start),
        CallbackQueryHandler(
            perp_one_start,
            pattern=rf"^{HLCoreStartState.TRIGGER.value}\|{Command.PERP_ONE}$",
        ),
    ],
    states={
        **perp_one_start_state,
    },
    fallbacks=[common_cancel_handler],
    name=Command.PERP_ONE,
    allow_reentry=True,
)
