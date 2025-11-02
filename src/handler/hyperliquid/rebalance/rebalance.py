from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from handler.command import Command
from .rebalance_pnl_alarm import (
    rebalance_pnl_start,
    pnl_states,
)
from .rebalance_select import (
    rebalance_select_start,
    select_states,
)
from .rebalance_start import (
    rebalance_start,
    rebalance_alarm_toggle,
    rebalance_auto_trading_toggle,
)
from .rebalance_unregister import (
    rebalance_unregister_start,
    unregister_confirm,
)
from .rebalance_refresh import (
    rebalance_refresh_start,
)
from .states import *
from .cancel import cancel_handler as rebalance_cancel_handler
from handler.utils.cancel import cancel_handler as common_cancel_handler
from ..start.states import HLCoreStartState

# ================================
# ConversationHandler 등록
# ===============================
rebalance_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.REBALANCE, rebalance_start),
        CallbackQueryHandler(
            rebalance_start,
            pattern=rf"^{HLCoreStartState.TRIGGER.value}\|{Command.REBALANCE}$",
        ),
    ],
    states={
        RebalanceStates.SELECT_ACTION: [
            CallbackQueryHandler(
                rebalance_pnl_start, pattern=f"^{PnlStates.START.value}$"
            ),
            CallbackQueryHandler(
                rebalance_select_start, pattern=f"^{SelectStates.START.value}$"
            ),
            CallbackQueryHandler(
                rebalance_alarm_toggle,
                pattern=(f"^{RebalanceStates.TOGGLE_ALARM.value}$"),
            ),
            CallbackQueryHandler(
                rebalance_auto_trading_toggle,
                pattern=f"^{RebalanceStates.TOGGLE_AUTO_TRADING.value}$",
            ),
            CallbackQueryHandler(
                rebalance_refresh_start,
                pattern=f"^{RefreshStates.START.value}$",
            ),
            CallbackQueryHandler(
                rebalance_unregister_start,
                pattern=f"^{UnregisterStates.START.value}$",
            ),
        ],
        **select_states,
        **pnl_states,
        **unregister_confirm,
    },
    fallbacks=[
        rebalance_cancel_handler,
        common_cancel_handler,
    ],
    name=Command.REBALANCE,
    allow_reentry=True,
)
