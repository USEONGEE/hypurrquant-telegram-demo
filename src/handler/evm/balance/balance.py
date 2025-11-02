from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
)
from handler.command import Command

# swap
from handler.evm.lpvault.lpvault_swap import lpvault_swap_states, lpvault_swap_start
from handler.evm.lpvault.states import LpvaultSwapState
from .balance_start import balance_start, page_callback, CALLBACK_PREFIX
from .balance_send import send_start, send_state
from .states import *
from handler.utils.cancel import cancel_handler as common_cancel_handler

# ================================
# ConversationHandler 정의
# ================================
balance_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.EVM_BALANCE, balance_start),
        CallbackQueryHandler(
            balance_start,
            pattern=rf"^{EvmBalanceState.START.value}",
        ),
    ],
    states={
        EvmBalanceState.SELECT_ACTION: [
            CallbackQueryHandler(page_callback, pattern=f"^{CALLBACK_PREFIX}"),
            CallbackQueryHandler(send_start, pattern=f"^{SendState.START.value}"),
            # swap
            CallbackQueryHandler(
                lpvault_swap_start, pattern=f"^{LpvaultSwapState.START.value}"
            ),
        ],
        **send_state,
        # swap
        **lpvault_swap_states,
    },
    fallbacks=[common_cancel_handler],
    name=Command.BALANCE,
    allow_reentry=True,
)
