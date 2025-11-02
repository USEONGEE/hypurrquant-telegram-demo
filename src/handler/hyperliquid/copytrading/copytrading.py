from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from handler.command import Command
from .copytrading_leverage import (
    copytrading_leverage_start,
    leverage_states,
)
from .copytrading_order_value import (
    copytrading_order_value_start,
    order_value_states,
)
from .copytrading_pnl_alarm import (
    copytrading_pnl_start,
    pnl_states,
)
from .copytrading_select import (
    copytrading_select_start,
    select_states,
)
from .copytrading_start import (
    copytrading_start,
)
from .copytrading_refresh import (
    copytrading_refresh_start,
)
from .copytrading_subscribe import (
    copytrading_subscribe_start,
    subscribe_states,
)
from .copytrading_unsubscribe import (
    copytrading_unsubscribe_start,
    unsubscribe_states,
)
from .copytrading_sell_type import (
    copytrading_sell_type_start,
    sell_type_states,
)
from .copytrading_follow import (
    follow_start,
    follow_states,
)
from .copytrading_unregister import (
    copytrading_unregister_start,
    unregister_confirm,
)
from .states import *
from .cancel import (
    cancel_handler as copytrading_cancel_handler,
)
from handler.utils.cancel import cancel_handler as common_cancel_handler
from ..start.states import HLCoreStartState

# ================================
# ConversationHandler 등록
# ===============================
copytrading_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.COPY_TRADING, copytrading_start),
        CallbackQueryHandler(
            copytrading_start,
            pattern=rf"^{HLCoreStartState.TRIGGER.value}\|{Command.COPY_TRADING}$",
        ),
    ],
    states={
        CopytradingStates.SELECT_ACTION: [
            CallbackQueryHandler(
                copytrading_leverage_start,
                pattern=f"^{LeverageStates.START.value}$",
            ),
            CallbackQueryHandler(
                copytrading_order_value_start,
                pattern=f"^{OrderValueStates.START.value}$",
            ),
            CallbackQueryHandler(
                copytrading_pnl_start, pattern=f"^{PnlStates.START.value}$"
            ),
            CallbackQueryHandler(
                copytrading_refresh_start,
                pattern=f"^{RefreshStates.START.value}$",
            ),
            CallbackQueryHandler(
                copytrading_select_start, pattern=f"^{SelectStates.START.value}$"
            ),
            CallbackQueryHandler(
                copytrading_sell_type_start,
                pattern=f"^{SellTypeStates.START.value}$",
            ),
            CallbackQueryHandler(
                copytrading_subscribe_start,
                pattern=f"^{SubscribeStates.START.value}$",
            ),
            CallbackQueryHandler(
                copytrading_unsubscribe_start,
                pattern=f"^{UnsubscribeStates.START.value}$",
            ),
            CallbackQueryHandler(follow_start, pattern=f"^{FollowStates.START.value}$"),
            CallbackQueryHandler(
                copytrading_unregister_start,
                pattern=f"^{UnregisterStates.START.value}$",
            ),
        ],
        **select_states,
        **pnl_states,
        **order_value_states,
        **leverage_states,
        **sell_type_states,
        **subscribe_states,
        **unsubscribe_states,
        **follow_states,
        **unregister_confirm,
    },
    fallbacks=[copytrading_cancel_handler, common_cancel_handler],
    name=Command.COPY_TRADING,
    allow_reentry=True,
)
