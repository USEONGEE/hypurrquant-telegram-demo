from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
)
from handler.command import Command
from handler.utils.cancel import cancel_handler
from .states import *
from .sell_all import sell_all_start, all_states
from .sell_start import sell_start
from .sell_specific import (
    sell_sepecific_start,
    specific_states,
)
from .cancel import sell_cancel
from hypurrquant.logging_config import configure_logging
from ..start.states import HLCoreStartState

logger = configure_logging(__name__)
# ================================
# ConversationHandler 정의
# ================================
sell_conv = ConversationHandler(
    entry_points=[
        CommandHandler(Command.SELL, sell_start),
        CallbackQueryHandler(
            sell_start,
            pattern=rf"^{HLCoreStartState.TRIGGER.value}\|{Command.SELL}$",
        ),
    ],
    states={
        SellStates.SELL: [
            CallbackQueryHandler(sell_all_start, pattern=f"^{AllStates.START.value}$"),
            CallbackQueryHandler(
                sell_sepecific_start, pattern=f"^{SpecificStates.START.value}$"
            ),
        ],
        **all_states,
        **specific_states,
    },
    fallbacks=[cancel_handler, sell_cancel],
    name=Command.SELL,
    allow_reentry=True,
)
