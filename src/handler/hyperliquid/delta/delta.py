from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from handler.command import Command
from handler.utils.cancel import cancel_handler as common_cancel_handler
from ..start.states import HLCoreStartState

from .delta_start import delta_start
from .states import *
from .delta_open import (
    delta_open_start,
    delta_open_states,
)
from .delta_close import (
    delta_close_start,
    delta_close_states,
)
from .cancel import cancel_handler

# ================================
# ConversationHandler 등록
# ===============================
delta_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.DELTA, delta_start),
        CallbackQueryHandler(
            delta_start,
            pattern=rf"^{HLCoreStartState.TRIGGER.value}\|{Command.DELTA}$",
        ),
    ],
    states={
        DeltaState.SELECT_ACTION: [
            CallbackQueryHandler(
                delta_open_start, pattern=f"^{DeltaOpenState.START.value}$"
            ),
            CallbackQueryHandler(
                delta_close_start, pattern=f"^{DeltaCloseState.START.value}$"
            ),
        ],
        **delta_open_states,
        **delta_close_states,
    },
    fallbacks=[
        cancel_handler,
        common_cancel_handler,
    ],
    name=Command.DELTA,
    allow_reentry=True,
)
