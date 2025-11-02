from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
)
from handler.command import Command
from .states import *
from .close_all import close_all_start, all_states
from .close_start import close_start
from .close_one import (
    close_one_start,
    one_states,
)
from ..start.states import HLCoreStartState
from .cancel import close_cancel
from hypurrquant.logging_config import configure_logging
from handler.utils.cancel import cancel_handler as common_cancel_handler

logger = configure_logging(__name__)
# ================================
# ConversationHandler 정의
# ================================
close_conv = ConversationHandler(
    entry_points=[
        CommandHandler(Command.CLOSE, close_start),
        CallbackQueryHandler(
            close_start,
            pattern=rf"^{HLCoreStartState.TRIGGER.value}\|{Command.CLOSE}$",
        ),
    ],
    states={
        CloseStates.CLOSE: [
            CallbackQueryHandler(
                close_all_start, pattern=f"^{CloseAllStates.START.value}$"
            ),
            CallbackQueryHandler(
                close_one_start, pattern=f"^{CloseOneStates.START.value}$"
            ),
        ],
        **all_states,
        **one_states,
    },
    fallbacks=[close_cancel, common_cancel_handler],
    name=Command.CLOSE,
    allow_reentry=True,
)
