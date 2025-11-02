from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
)
from handler.command import Command
from ..start.states import HLCoreStartState
from handler.utils.cancel import cancel_handler
from .buy_start import buy_start
from .buy_select_stock import select_stock_states
from .buy_order import order_states
from .buy_strategy import strategy_states

# ================================
# ConversationHandler 정의
# ================================
buy_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.BUY, buy_start),
        CallbackQueryHandler(
            buy_start,
            pattern=rf"^{HLCoreStartState.TRIGGER.value}\|{Command.BUY}$",
        ),
    ],
    states={
        **strategy_states,
        **select_stock_states,
        **order_states,
    },
    fallbacks=[cancel_handler],
    name=Command.BUY,
    allow_reentry=True,
)
