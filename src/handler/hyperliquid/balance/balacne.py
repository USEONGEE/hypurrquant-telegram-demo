from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
)
from handler.command import Command
from ..start.states import HLCoreStartState
from .balance_start import balance_start
from .balance_refresh import (
    balance_refresh_start,
)
from .balance_perp_to_spot import (
    balance_perp_to_spot_start,
    perp_to_spot_states,
)
from .balance_spot_to_perp import (
    balance_spot_to_perp_start,
    spot_to_perp_states,
)
from .balance_spot_detail import (
    balance_spot_detail_start,
    spot_detail_states,
)
from .balance_send_usdc import (
    balance_send_usdc_start,
    send_usdc_state,
)
from .balance_perp_detail import (
    balance_perp_detail_start,
    perp_detail_states,
)
from .states import BalanceStates
from .states import *
from handler.utils.cancel import cancel_handler as common_cancel_handler

# ================================
# ConversationHandler 정의
# ================================
balance_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.BALANCE, balance_start),
        CallbackQueryHandler(
            balance_start,
            pattern=rf"^{HLCoreStartState.TRIGGER.value}\|{Command.BALANCE}$",
        ),
    ],
    states={
        BalanceStates.SELECT_ACTION: [
            CallbackQueryHandler(
                balance_perp_to_spot_start, pattern=f"^{PerpToSpotStates.START.value}"
            ),
            CallbackQueryHandler(
                balance_spot_to_perp_start, pattern=f"^{SpotToPerpStates.START.value}"
            ),
            CallbackQueryHandler(
                balance_spot_detail_start, pattern=f"^{SpotDetailStates.START.value}"
            ),
            CallbackQueryHandler(
                balance_refresh_start, pattern=f"^{RefreshStates.START.value}"
            ),
            CallbackQueryHandler(
                balance_send_usdc_start, pattern=f"^{SendUsdcStates.START.value}"
            ),
            CallbackQueryHandler(
                balance_perp_detail_start, pattern=f"^{PerpDetailStates.START.value}"
            ),
        ],
        **perp_to_spot_states,
        **spot_to_perp_states,
        **spot_detail_states,
        **send_usdc_state,
        **perp_detail_states,
    },
    fallbacks=[common_cancel_handler],
    name=Command.BALANCE,
    allow_reentry=True,
)
